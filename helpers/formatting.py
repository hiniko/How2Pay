"""Locale-aware formatting utilities."""

from datetime import date
from typing import Union
from models.config_model import LocaleConfig, load_config


class LocaleFormatter:
    """Handles locale-specific formatting for currency and dates."""
    
    def __init__(self, locale_config: LocaleConfig = None):
        self.config = locale_config or load_config().locale
    
    def format_currency(self, amount: Union[int, float]) -> str:
        """Format amount as currency with proper symbol placement."""
        # Format the number with thousands separator
        if isinstance(amount, float):
            formatted_amount = f"{amount:.2f}"
        else:
            formatted_amount = f"{float(amount):.2f}"
        
        # Add thousands separator if needed
        if self.config.thousands_separator and abs(amount) >= 1000:
            parts = formatted_amount.split('.')
            integer_part = parts[0]
            decimal_part = parts[1] if len(parts) > 1 else "00"
            
            # Add thousands separators
            reversed_int = integer_part[::-1]
            grouped = [reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)]
            integer_part = self.config.thousands_separator.join(grouped)[::-1]
            
            formatted_amount = f"{integer_part}.{decimal_part}"
        
        # Handle decimal separator
        if self.config.decimal_separator != '.':
            formatted_amount = formatted_amount.replace('.', self.config.decimal_separator)
        
        # Add currency symbol
        if self.config.currency_position == 'before':
            return f"{self.config.currency_symbol}{formatted_amount}"
        else:
            return f"{formatted_amount}{self.config.currency_symbol}"
    
    def format_date_short(self, date_obj: date) -> str:
        """Format date in short format (dd/mm or mm/dd)."""
        if self.config.date_format == 'dd/mm/yyyy':
            return date_obj.strftime('%d/%m')
        else:  # mm/dd/yyyy
            return date_obj.strftime('%m/%d')
    
    def format_date_full(self, date_obj: date) -> str:
        """Format date in full format."""
        if self.config.date_format == 'dd/mm/yyyy':
            return date_obj.strftime('%d/%m/%Y')
        else:  # mm/dd/yyyy
            return date_obj.strftime('%m/%d/%Y')
    
    def format_percentage(self, percentage: float) -> str:
        """Format percentage consistently."""
        return f"{percentage:.1f}%"


# Global formatter instance
_formatter = None

def get_formatter() -> LocaleFormatter:
    """Get the global formatter instance."""
    global _formatter
    if _formatter is None:
        _formatter = LocaleFormatter()
    return _formatter

def refresh_formatter():
    """Refresh the global formatter to pick up config changes."""
    global _formatter
    _formatter = LocaleFormatter()