#!/Users/sherman/Finances/.venv/bin/python


from commands.bills_cmd import app as bills_app
from commands.payee_cmd import app as payee_app
from commands.config_cmd import config_app 
from commands.schedule_cmd import app as schedule_app 


from rich.console import Console
import typer
from typing import Optional

from helpers.state_ops import save_state
from helpers.config_ops import set_active_state_file


DEFAULT_STATE_FILE = 'how2pay_state.yaml'

console = Console()


def version_callback(value: bool):
    if value:
        console.print("How2Pay CLI version 0.1.0")
        raise typer.Exit()

app = typer.Typer(
    short_help="How2Pay CLI",
    help="How2Pay CLI - Manage your bills and payees.",
    no_args_is_help=True)

app.add_typer(bills_app, name="bills")
app.add_typer(payee_app, name="payee")
app.add_typer(config_app, name="config")
app.add_typer(schedule_app, name="schedule")

@app.command()
def init(filename: str = DEFAULT_STATE_FILE):
    """Initialize a state file and set it as active context."""
    # Set the filename as active first, then save an empty state
    set_active_state_file(filename)
    from models.state_file import StateFile
    empty_state = StateFile()
    save_state(empty_state)
    console.print(f'[bold green]Initialized and set active state file: {filename}[/bold green]')

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(None, "--version", "-v", callback=version_callback, help="Show version and exit")
):
    """Entry point for the how2pay command."""
    # version parameter is handled by typer callback mechanism
    _ = version  # Suppress unused variable warning

def main():
    """Entry point for setuptools and command line."""
    app()

if __name__ == "__main__":
    main()
