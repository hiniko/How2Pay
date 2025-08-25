import typer
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from datetime import date, datetime
from typing import Optional
from models.schedule_options import ScheduleOptions
from helpers.state_ops import load_state, save_state
from helpers.validation import validate_month, validate_year, validate_projection_months, validate_cutoff_day
from models.state_file import StateFile
from scheduler.cash_flow import CashFlowScheduler
from tui.payment_schedule_display import PaymentScheduleDisplay
from exporters.csv_exporter import CsvExporter

console = Console()
app = typer.Typer(no_args_is_help=True)

# Create subcommands
config_app = typer.Typer(no_args_is_help=True)
app.add_typer(config_app, name="config", help="Manage schedule configuration")

@app.command()
def show(
    months: Optional[int] = typer.Option(None, "--months", "-m", help="Number of months to project"),
    start_month: Optional[int] = typer.Option(None, "--start-month", help="Starting month (1-12)"),
    start_year: Optional[int] = typer.Option(None, "--start-year", help="Starting year"),
    export_csv: Optional[str] = typer.Option(None, "--export", help="Export to CSV file"),
    export_pdf: bool = typer.Option(False, "--pdf", help="Export to PDF file (auto-generates filename)"),
    show_zero_contribution: bool = typer.Option(False, "--show-zero", help="Show income streams with 0% contribution")
) -> None:
    """Show cash flow projection schedule."""
    state: StateFile = load_state()
    
    # Use defaults if not specified
    projection_months = months or state.schedule_options.default_projection_months
    current_date = date.today()
    target_month = start_month or current_date.month
    target_year = start_year or current_date.year
    
    # Validate inputs
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
    
    console.print(f"[bold]Generating {projection_months}-month cash flow projection starting {target_month}/{target_year}[/bold]")
    console.print(f"Bills: {len(state.bills)}, Payees: {len(state.payees)}")
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
    
    # Display the table
    display = PaymentScheduleDisplay(console)
    display.display_pivot_table(result, show_zero_contribution)
    
    # Export if requested
    if export_csv:
        CsvExporter.export_payment_schedule(result, export_csv)
        console.print(f"\n[green]Exported to {export_csv}[/green]")
    
    if export_pdf:
        try:
            from exporters.pdf_exporter import PdfExporter
            from helpers.config_ops import get_active_state_file
            import os
            
            # Generate filename from state file name
            state_filename = get_active_state_file()
            base_name = os.path.splitext(os.path.basename(state_filename))[0]
            pdf_filename = f"{base_name}.pdf"
            
            # Use the unified PDF export (household schedule)
            PdfExporter.export_schedule_to_pdf(
                result=result,
                output_path=pdf_filename,
                payee_name=None,  # None means household schedule
                show_zero_contribution=show_zero_contribution
            )
            console.print(f"\n[green]Exported professional PDF to {pdf_filename}[/green]")
            
        except ImportError as e:
            console.print(f"\n[red]PDF export failed: {e}[/red]")
            console.print("[yellow]Install PDF dependencies with: pip install -e '.[pdf]'[/yellow]")

@app.command()
def payee(
    payee_name: str = typer.Argument(..., help="Name of the payee to show schedule for"),
    months: Optional[int] = typer.Option(None, "--months", "-m", help="Number of months to project"),
    start_month: Optional[int] = typer.Option(None, "--start-month", help="Starting month (1-12)"),
    start_year: Optional[int] = typer.Option(None, "--start-year", help="Starting year"),
    export_pdf: bool = typer.Option(False, "--pdf", help="Export to PDF file (auto-generates filename)"),
    show_zero_contribution: bool = typer.Option(False, "--show-zero", help="Show income streams with 0% contribution")
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
    from scheduler.cash_flow import CashFlowScheduler
    from tui.payment_schedule_display import PaymentScheduleDisplay
    
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
    display.display_payee_schedule(result, payee_name, show_zero_contribution)
    
    # Export to PDF if requested
    if export_pdf:
        try:
            from exporters.pdf_exporter import PdfExporter
            from helpers.config_ops import get_active_state_file
            import os
            
            # Generate filename from state file name and payee name
            state_filename = get_active_state_file()
            base_name = os.path.splitext(os.path.basename(state_filename))[0]
            # Clean payee name for filename (replace spaces and special characters)
            clean_payee_name = payee_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            pdf_filename = f"{base_name}-{clean_payee_name}.pdf"
            
            # Use the unified PDF export (payee-specific schedule)
            PdfExporter.export_schedule_to_pdf(
                result=result,
                output_path=pdf_filename,
                payee_name=payee_name,  # Providing payee_name means payee-specific schedule
                show_zero_contribution=show_zero_contribution
            )
            console.print(f"\n[green]Exported professional PDF to {pdf_filename}[/green]")
            
        except ImportError as e:
            console.print(f"\n[red]PDF export failed: {e}[/red]")
            console.print("[yellow]Install PDF dependencies with: pip install -e '.[pdf]'[/yellow]")

@config_app.command("show")
def config_show() -> None:
    """Show current schedule configuration."""
    state: StateFile = load_state()
    options = state.schedule_options
    
    console.print("[bold]Current Schedule Configuration:[/bold]")
    console.print(f"  Cutoff Day: [cyan]{options.cutoff_day}[/cyan] of each month")
    console.print(f"  Weekend Adjustment: [magenta]{options.weekend_adjustment}[/magenta]")
    console.print(f"  Default Projection Months: [blue]{options.default_projection_months}[/blue]")
    console.print("")
    
    # Show examples for current and next month
    current_cutoff = options.get_current_month_cutoff()
    next_cutoff = options.get_next_month_cutoff()
    
    console.print("[bold]Examples:[/bold]")
    console.print(f"  This month's cutoff: [yellow]{current_cutoff.strftime('%A, %B %d, %Y')}[/yellow]")
    console.print(f"  Next month's cutoff: [yellow]{next_cutoff.strftime('%A, %B %d, %Y')}[/yellow]")

@config_app.command("set")
def config_set() -> None:
    """Interactively configure schedule options."""
    state: StateFile = load_state()
    current_options = state.schedule_options
    
    console.print("[bold]Current settings:[/bold]")
    console.print(f"  Cutoff Day: [cyan]{current_options.cutoff_day}[/cyan]")
    console.print(f"  Weekend Adjustment: [magenta]{current_options.weekend_adjustment}[/magenta]")
    console.print(f"  Default Projection Months: [blue]{current_options.default_projection_months}[/blue]")
    console.print("")
    
    # Get cutoff day
    cutoff_day = IntPrompt.ask(
        "Enter cutoff day of month (1-31)", 
        default=current_options.cutoff_day,
        show_default=True
    )
    
    try:
        cutoff_day = validate_cutoff_day(cutoff_day)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return
    
    # Get weekend adjustment
    weekend_adjustment = Prompt.ask(
        "Weekend adjustment strategy",
        choices=["last_working_day", "next_working_day"],
        default=current_options.weekend_adjustment,
        show_default=True
    )
    
    # Get default projection months
    default_projection_months = IntPrompt.ask(
        "Default projection months (1-60)",
        default=current_options.default_projection_months,
        show_default=True
    )
    
    try:
        default_projection_months = validate_projection_months(default_projection_months)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return
    
    # Create new options
    new_options = ScheduleOptions(
        cutoff_day=cutoff_day,
        weekend_adjustment=weekend_adjustment,
        default_projection_months=default_projection_months
    )
    
    # Show preview
    console.print("\n[bold]Preview with new settings:[/bold]")
    current_cutoff = new_options.get_current_month_cutoff()
    next_cutoff = new_options.get_next_month_cutoff()
    
    console.print(f"  Cutoff Day: [cyan]{new_options.cutoff_day}[/cyan]")
    console.print(f"  Weekend Adjustment: [magenta]{new_options.weekend_adjustment}[/magenta]")
    console.print(f"  Default Projection Months: [blue]{new_options.default_projection_months}[/blue]")
    console.print(f"  This month's cutoff: [yellow]{current_cutoff.strftime('%A, %B %d, %Y')}[/yellow]")
    console.print(f"  Next month's cutoff: [yellow]{next_cutoff.strftime('%A, %B %d, %Y')}[/yellow]")
    
    # Confirm and save
    if Confirm.ask("\nSave these settings?", default=True):
        state.schedule_options = new_options
        save_state(state)
        console.print("[bold green]Schedule configuration updated successfully![/bold green]")
    else:
        console.print("[yellow]Settings not saved.[/yellow]")

@config_app.command("test")
def config_test() -> None:
    """Test cutoff dates for the next 6 months."""
    state: StateFile = load_state()
    options = state.schedule_options
    
    console.print("[bold]Cutoff dates for next 6 months:[/bold]")
    console.print(f"Using cutoff day [cyan]{options.cutoff_day}[/cyan] with [magenta]{options.weekend_adjustment}[/magenta] adjustment\n")
    
    current_date = date.today()
    
    for i in range(6):
        month = current_date.month + i
        year = current_date.year
        while month > 12:
            month -= 12
            year += 1
        
        cutoff_date = options.get_cutoff_date(month, year)
        month_name = cutoff_date.strftime('%B %Y')
        day_name = cutoff_date.strftime('%A')
        
        console.print(f"  {month_name}: [yellow]{cutoff_date.strftime('%d')}[/yellow] ({day_name})")

# Legacy commands for backward compatibility (will be removed eventually)
@app.command(hidden=True)
def show_old() -> None:
    """Legacy command - use 'config show' instead."""
    console.print("[yellow]This command is deprecated. Use 'how2pay schedule config show' instead.[/yellow]")
    config_show()

@app.command(hidden=True) 
def set_old() -> None:
    """Legacy command - use 'config set' instead."""
    console.print("[yellow]This command is deprecated. Use 'how2pay schedule config set' instead.[/yellow]")
    config_set()

@app.command(hidden=True)
def test_old() -> None:
    """Legacy command - use 'config test' instead."""
    console.print("[yellow]This command is deprecated. Use 'how2pay schedule config test' instead.[/yellow]")
    config_test()
