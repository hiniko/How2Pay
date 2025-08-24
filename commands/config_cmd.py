import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from helpers.config_ops import get_active_state_file, set_active_state_file
from models.config_model import load_config, save_config, LocaleConfig
from helpers.formatting import refresh_formatter

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

locale_app = typer.Typer(help="Locale configuration commands.", no_args_is_help=True)

@locale_app.command("show")
def show_locale():
    """Show current locale settings."""
    config = load_config()
    locale = config.locale
    
    console.print("[bold]Current Locale Settings:[/bold]")
    console.print(f"  Currency Symbol: [cyan]{locale.currency_symbol}[/cyan]")
    console.print(f"  Currency Position: [cyan]{locale.currency_position}[/cyan] (before/after amount)")
    console.print(f"  Date Format: [cyan]{locale.date_format}[/cyan]")
    console.print(f"  Decimal Separator: [cyan]{locale.decimal_separator}[/cyan]")
    console.print(f"  Thousands Separator: [cyan]{locale.thousands_separator}[/cyan]")
    
    # Show examples
    from helpers.formatting import LocaleFormatter
    formatter = LocaleFormatter(locale)
    from datetime import date
    today = date.today()
    
    console.print("\n[bold]Examples:[/bold]")
    console.print(f"  Currency: [yellow]{formatter.format_currency(1234.56)}[/yellow]")
    console.print(f"  Short date: [yellow]{formatter.format_date_short(today)}[/yellow]")
    console.print(f"  Full date: [yellow]{formatter.format_date_full(today)}[/yellow]")
    console.print(f"  Percentage: [yellow]{formatter.format_percentage(15.5)}[/yellow]")

@locale_app.command("set")
def set_locale():
    """Configure locale settings interactively."""
    config = load_config()
    current = config.locale
    
    console.print("[bold]Current settings:[/bold]")
    console.print(f"  Currency Symbol: [cyan]{current.currency_symbol}[/cyan]")
    console.print(f"  Currency Position: [cyan]{current.currency_position}[/cyan]")
    console.print(f"  Date Format: [cyan]{current.date_format}[/cyan]")
    console.print("")
    
    # Currency symbol
    currency_symbol = Prompt.ask(
        "Currency symbol",
        default=current.currency_symbol
    )
    
    # Currency position
    currency_position = Prompt.ask(
        "Currency position",
        choices=["before", "after"],
        default=current.currency_position
    )
    
    # Date format
    date_format = Prompt.ask(
        "Date format",
        choices=["dd/mm/yyyy", "mm/dd/yyyy"],
        default=current.date_format
    )
    
    # Decimal separator
    decimal_separator = Prompt.ask(
        "Decimal separator",
        choices=[".", ","],
        default=current.decimal_separator
    )
    
    # Thousands separator
    thousands_separator = Prompt.ask(
        "Thousands separator",
        choices=[",", ".", " ", ""],
        default=current.thousands_separator
    )
    
    # Create new locale config
    new_locale = LocaleConfig(
        currency_symbol=currency_symbol,
        currency_position=currency_position,
        date_format=date_format,
        decimal_separator=decimal_separator,
        thousands_separator=thousands_separator
    )
    
    # Show preview
    from helpers.formatting import LocaleFormatter
    formatter = LocaleFormatter(new_locale)
    from datetime import date
    today = date.today()
    
    console.print("\n[bold]Preview with new settings:[/bold]")
    console.print(f"  Currency: [yellow]{formatter.format_currency(1234.56)}[/yellow]")
    console.print(f"  Short date: [yellow]{formatter.format_date_short(today)}[/yellow]")
    console.print(f"  Full date: [yellow]{formatter.format_date_full(today)}[/yellow]")
    
    # Confirm and save
    if Confirm.ask("\nSave these settings?", default=True):
        config.locale = new_locale
        save_config(config)
        refresh_formatter()  # Refresh the global formatter
        console.print("[bold green]Locale settings updated successfully![/bold green]")
    else:
        console.print("[yellow]Settings not saved.[/yellow]")

@locale_app.command("preset")
def set_preset(
    preset: str = typer.Argument(..., help="Preset name: uk, us, eu")
):
    """Set locale to a predefined preset."""
    presets = {
        "uk": LocaleConfig(
            currency_symbol="£",
            currency_position="before",
            date_format="dd/mm/yyyy",
            decimal_separator=".",
            thousands_separator=","
        ),
        "us": LocaleConfig(
            currency_symbol="$",
            currency_position="before",
            date_format="mm/dd/yyyy",
            decimal_separator=".",
            thousands_separator=","
        ),
        "eu": LocaleConfig(
            currency_symbol="€",
            currency_position="after",
            date_format="dd/mm/yyyy",
            decimal_separator=",",
            thousands_separator="."
        )
    }
    
    preset_lower = preset.lower()
    if preset_lower not in presets:
        console.print(f"[red]Unknown preset '{preset}'. Available presets: uk, us, eu[/red]")
        return
    
    config = load_config()
    config.locale = presets[preset_lower]
    save_config(config)
    refresh_formatter()
    
    console.print(f"[bold green]Locale set to {preset.upper()} preset![/bold green]")
    
    # Show the new settings
    show_locale()

config_app.add_typer(locale_app, name="locale")
