
import typer
from rich.console import Console
from rich.prompt import Prompt
from models.recurrence import Recurrence
from helpers.state_ops import load_state, save_state
from helpers.validation import validate_amount, validate_date_string
from models.state_file import StateFile
from rich.table import Table
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
        
        # Show bill assignment information
        if bill.has_custom_shares():
            console.print("  Assignment: [bold]Custom percentages[/bold]")
            total_assigned = 0.0
            for share in bill.share:
                console.print(f"    {share.payee}: {share.percentage:.1f}%")
                total_assigned += share.percentage
            
            if abs(total_assigned - 100.0) > 0.01:
                console.print(f"    [red]WARNING: Total is {total_assigned:.1f}% (should be 100%)[/red]")
        else:
            console.print("  Assignment: [dim]Equal split among all payees[/dim]")
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

@app.command()
def assign() -> None:
    """Assign percentage splits for bills among payees."""
    state: StateFile = load_state()
    
    if not state.bills:
        console.print("[yellow]No bills found. Add bills first with 'how2pay bills add'.[/yellow]")
        return
    
    if not state.payees:
        console.print("[yellow]No payees found. Add payees first with 'how2pay payee add'.[/yellow]")
        return
    
    # Show current bill assignments
    console.print("[bold]Current Bill Assignments:[/bold]\n")
    
    for i, bill in enumerate(state.bills, 1):
        console.print(f"{i}. [bold cyan]{bill.name}[/bold cyan] (${bill.amount:.2f})")
        
        if bill.has_custom_shares():
            console.print("   Custom percentages:")
            total_assigned = 0.0
            for share in bill.share:
                console.print(f"     {share.payee}: {share.percentage:.1f}%")
                total_assigned += share.percentage
            
            if abs(total_assigned - 100.0) > 0.01:
                console.print(f"   [red]WARNING: Total is {total_assigned:.1f}% (should be 100%)[/red]")
        else:
            console.print("   Equal split among all payees")
        console.print("")
    
    # Select bill to modify
    bill_choice = Prompt.ask("Enter bill number to modify assignments", default="1")
    
    try:
        bill_index = int(bill_choice) - 1
        if bill_index < 0 or bill_index >= len(state.bills):
            console.print("[red]Invalid bill number.[/red]")
            return
    except ValueError:
        console.print("[red]Please enter a valid number.[/red]")
        return
    
    bill = state.bills[bill_index]
    console.print(f"\n[bold]Modifying assignments for: {bill.name}[/bold]")
    
    # Show payees and get percentages
    payee_names = [payee.name for payee in state.payees]
    console.print(f"Available payees: {', '.join(payee_names)}")
    console.print("\nEnter percentage for each payee (0-100). Total must equal 100%.")
    
    new_percentages = {}
    total_percentage = 0.0
    
    for payee_name in payee_names:
        current_percentage = bill.get_payee_percentage(payee_name)
        percentage_str = Prompt.ask(f"{payee_name} percentage", default=str(current_percentage))
        
        try:
            percentage = float(percentage_str)
            if percentage < 0 or percentage > 100:
                console.print("[red]Percentage must be between 0 and 100.[/red]")
                return
            
            new_percentages[payee_name] = percentage
            total_percentage += percentage
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")
            return
    
    # Validate total
    if abs(total_percentage - 100.0) > 0.01:
        console.print(f"[red]Total percentages must equal 100%, got {total_percentage:.1f}%[/red]")
        return
    
    # Apply changes
    bill.share.clear()  # Clear existing assignments
    for payee_name, percentage in new_percentages.items():
        if percentage > 0:
            bill.set_payee_percentage(payee_name, percentage)
    
    # Validate and save
    is_valid, message = bill.validate_percentages()
    if not is_valid:
        console.print(f"[red]Validation error: {message}[/red]")
        return
    
    save_state(state)
    console.print(f"[bold green]Successfully updated assignments for '{bill.name}'[/bold green]")
    
    # Show summary
    console.print("\nNew assignments:")
    if bill.has_custom_shares():
        for share in bill.share:
            console.print(f"  {share.payee}: {share.percentage:.1f}%")
    else:
        console.print("  Equal split among all payees")
