import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from models.recurrence import Recurrence
from models.payee import Payee, PaySchedule
from helpers.state_ops import load_state, save_state
from models.state_file import StateFile
from scheduler.cash_flow import CashFlowScheduler
from tui.payment_schedule_display import PaymentScheduleDisplay
from datetime import date
from typing import Any, Optional

console = Console()
app = typer.Typer(no_args_is_help=True)

@app.command()
def list() -> None:
    """List all payees with pay schedule details."""
    state: StateFile = load_state()
    payees = state.payees
    if not payees:
        console.print("[yellow]No payees found.[/yellow]")
        return
    for i, payee in enumerate(payees, 1):
        console.print(f"[bold][cyan]{payee.name}[/cyan][/bold]")
        if payee.description:
            console.print(f"  Description: [white]{payee.description}[/white]")
        
        if payee.pay_schedules:
            console.print(f"  Pay schedules ({len(payee.pay_schedules)}):")
            for j, schedule in enumerate(payee.pay_schedules, 1):
                console.print(f"    [yellow]{j}.[/yellow] Amount: [cyan]${schedule.amount}[/cyan]")
                if schedule.description:
                    console.print(f"       Description: [white]{schedule.description}[/white]")
                recurrence = schedule.recurrence
                if recurrence:
                    # Determine correct unit (singular/plural)
                    unit = recurrence.interval or "interval"
                    every = recurrence.every or 1
                    # Handle 'ly' ending intervals: remove 'ly' for singular, add 's' for plural
                    if unit.endswith('ly'):
                        base_unit = unit[:-2]  # Remove 'ly'
                        unit_str = base_unit if every == 1 else base_unit + 's'
                    else:
                        unit_str = unit if every == 1 else unit + 's'
                    console.print(f"       Paid every: [bold]{every}[/bold] [magenta]{unit_str}[/magenta]")
                    console.print(f"       Start: [magenta]{recurrence.start}[/magenta]")
                    console.print(f"       End: [magenta]{recurrence.end}[/magenta]")
        else:
            console.print("  [yellow]No pay schedules defined[/yellow]")
        console.print("")

@app.command()
def add() -> None:
    """Interactively add a payee with multiple pay schedules."""
    state: StateFile = load_state()
    while True:
        name: str = Prompt.ask("Enter payee name")
        description: str = Prompt.ask("Enter payee description (optional)", default="")
        description = description if description else None

        payee = Payee(name=name, description=description)
        
        # Add pay schedules
        console.print("[bold]Adding pay schedules...[/bold]")
        while True:
            # Amount
            amount_str: str = Prompt.ask("Enter pay amount", default="0.0")
            try:
                amount = float(amount_str)
            except ValueError:
                console.print("[red]Amount must be a number. Please try again.[/red]")
                continue

            schedule_description: str = Prompt.ask("Enter schedule description (optional)", default="")
            schedule_description = schedule_description if schedule_description else None

            # Pay recurrence input
            kind: str = Prompt.ask("Pay recurrence kind", choices=["interval", "calendar"], default="interval")
            interval: str = None
            every: int = None
            start: Any = None
            end: Any = None
            if kind == "interval":
                interval = Prompt.ask("Interval type", choices=["daily", "weekly", "quarterly", "yearly"], default="weekly")
                every = Prompt.ask("Every how many intervals?", default="1")
                try:
                    every = int(every)
                except ValueError:
                    console.print("[red]Must be an integer. Please try again.[/red]")
                    continue
            elif kind == "calendar":
                interval = Prompt.ask("Calendar interval", choices=["monthly", "quarterly", "yearly"], default="monthly")
            # Start date
            start_str: str = Prompt.ask("Start date (YYYY-MM-DD)", default="2025-01-01")
            try:
                from datetime import datetime
                start = datetime.strptime(start_str, "%Y-%m-%d").date()
            except Exception:
                console.print("[red]Invalid date format. Please try again.[/red]")
                continue
            # End date
            end_str: str = Prompt.ask("End date (YYYY-MM-DD, optional)", default="")
            if end_str:
                try:
                    from datetime import datetime
                    end = datetime.strptime(end_str, "%Y-%m-%d").date()
                except Exception:
                    console.print("[red]Invalid end date format. Please try again.[/red]")
                    end = None
            
            recurrence = Recurrence(kind=kind, interval=interval, every=every, start=start, end=end)
            schedule = PaySchedule(amount=amount, recurrence=recurrence, description=schedule_description)
            payee.pay_schedules.append(schedule)
            
            console.print(f"[green]Added pay schedule: ${amount}[/green]")
            
            # Ask if they want to add another schedule
            if not Confirm.ask("Add another pay schedule?", default=False):
                break

        state.payees.append(payee)
        save_state(state)
        console.print(f"[bold blue]Added payee:[/bold blue] {payee.name} with {len(payee.pay_schedules)} pay schedule(s)")
        break

@app.command()
def schedule(
    payee_name: str = typer.Argument(..., help="Name of the payee to show schedule for"),
    months: Optional[int] = typer.Option(None, "--months", "-m", help="Number of months to project"),
    start_month: Optional[int] = typer.Option(None, "--start-month", help="Starting month (1-12)"),
    start_year: Optional[int] = typer.Option(None, "--start-year", help="Starting year"),
    export_pdf: Optional[str] = typer.Option(None, "--pdf", help="Export to PDF file")
) -> None:
    """Show payment schedule for a specific payee."""
    state: StateFile = load_state()
    
    # Check if payee exists
    payee = None
    for p in state.payees:
        if p.name.lower() == payee_name.lower():
            payee = p
            payee_name = p.name  # Use exact case from state
            break
    
    if not payee:
        console.print(f"[red]Payee '{payee_name}' not found.[/red]")
        console.print("Available payees:")
        for p in state.payees:
            console.print(f"  • {p.name}")
        return
    
    # Use defaults if not specified
    projection_months = months or state.schedule_options.default_projection_months
    current_date = date.today()
    target_month = start_month or current_date.month
    target_year = start_year or current_date.year
    
    # Validate inputs
    from helpers.validation import validate_month, validate_year, validate_projection_months
    try:
        target_month = validate_month(target_month)
        target_year = validate_year(target_year)
        projection_months = validate_projection_months(projection_months)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return
    
    # Check if we have any data
    if not state.bills and not state.payees:
        console.print("[yellow]No bills or payees configured. Use 'how2pay bills add' and 'how2pay payees add' to get started.[/yellow]")
        return
    
    console.print(f"[bold]Generating {projection_months}-month schedule for {payee_name} starting {target_month}/{target_year}[/bold]")
    console.print(f"Bills: {len(state.bills)}, Income streams: {len(payee.pay_schedules)}")
    console.print("")
    
    # Create scheduler and generate projection
    scheduler = CashFlowScheduler(state)
    result = scheduler.calculate_proportional_contributions(
        start_month=target_month,
        start_year=target_year,
        months_ahead=projection_months
    )
    
    if not result.schedule_items:
        console.print("[yellow]No schedule items generated. Check your bill and payee configurations.[/yellow]")
        return
    
    # Display the payee-specific table
    display = PaymentScheduleDisplay(console)
    display.display_payee_schedule(result, payee_name)
    
    # Export to PDF if requested
    if export_pdf:
        try:
            from exporters.pdf_exporter import PdfExporter
            
            # Use the unified PDF export (payee-specific schedule)
            PdfExporter.export_schedule_to_pdf(
                result=result,
                output_path=export_pdf,
                payee_name=payee_name  # Providing payee_name means payee-specific schedule
            )
            console.print(f"\n[green]Exported professional PDF to {export_pdf}[/green]")
            
        except ImportError as e:
            console.print(f"\n[red]PDF export failed: {e}[/red]")
            console.print("[yellow]Install PDF dependencies with: pip install -e '.[pdf]'[/yellow]")
