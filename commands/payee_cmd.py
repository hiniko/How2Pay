import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from models.recurrence import Recurrence
from models.payee import Payee, PaySchedule
from helpers.state_ops import load_state, save_state
from models.state_file import StateFile
from scheduler.payment_scheduler import PaymentScheduler
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
