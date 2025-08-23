import typer
from rich.console import Console
from helpers.config_ops import get_active_state_file, set_active_state_file

console = Console()

config_app = typer.Typer(help="Configuration commands.", no_args_is_help=True)

context_app = typer.Typer(help="Context management commands.", no_args_is_help=True)

@context_app.command("set")
def set_context(filename: str):
    """Set the active state file context."""
    set_active_state_file(filename)
    console.print(f'[bold yellow]Active state file set to: {filename}[/bold yellow]')

@context_app.command("show")
def show_context():
    """Show the current active state file context."""
    active = get_active_state_file()
    console.print(f'[bold cyan]Current active state file: {active}[/bold cyan]')

config_app.add_typer(context_app, name="context")
