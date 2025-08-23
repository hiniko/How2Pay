
import typer
from rich.console import Console
from rich.prompt import Prompt
from models.recurrence import Recurrence
from helpers.state_ops import load_state, save_state
from helpers.validation import validate_amount, validate_date_string
from models.state_file import StateFile
from typing import Any

console = Console()

app = typer.Typer(no_args_is_help=True)
@app.command()
def list() -> None:
    """List all bills with recurrence details."""
    state: StateFile = load_state()
    bills = state.bills
    if not bills:
        console.print("[yellow]No bills found.[/yellow]")
        return
    for i, bill in enumerate(bills, 1):
        console.print(f"[bold][yellow]{bill.name}[/yellow][/bold]")
        console.print(f"  Amount: [cyan]{bill.amount}[/cyan]")
        recurrence = bill.recurrence
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
            console.print(f"  Recurring every: [bold]{every}[/bold] [magenta]{unit_str}[/magenta]")
            console.print(f"  Start: [magenta]{recurrence.start}[/magenta]")
            console.print(f"  End: [magenta]{recurrence.end}[/magenta]")
        console.print("")


@app.command()
def add() -> None:
    """Interactively add a bill."""
    state: StateFile = load_state()
    while True:
        name: str = Prompt.ask("Enter bill name")
        amount: str = Prompt.ask("Enter bill amount", default="0.0")
        try:
            amount = validate_amount(amount)
        except ValueError as e:
            console.print(f"[red]Error: {e}. Please try again.[/red]")
            continue

        # Recurrence input
        kind: str = Prompt.ask("Recurrence kind", choices=["interval", "calendar"], default="interval")
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

        from models.bill import Bill
        bill = Bill(name=name, amount=amount, recurrence=recurrence)
        state.bills.append(bill)
        save_state(state)
        console.print(f"[bold blue]Added bill:[/bold blue] {bill.name}")
        break
