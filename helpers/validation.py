"""Input validation helpers for the finance application."""

from typing import Optional, Union
from datetime import date


def validate_amount(amount_str: str) -> float:
    """
    Validate and parse amount string to float.
    
    Args:
        amount_str: String representation of amount
        
    Returns:
        float: Parsed amount
        
    Raises:
        ValueError: If amount cannot be parsed or is negative
    """
    try:
        amount = float(amount_str)
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        return amount
    except ValueError as e:
        if "negative" in str(e):
            raise
        raise ValueError(f"Invalid amount format: {amount_str}")


def validate_month(month: Union[int, str]) -> int:
    """
    Validate month is between 1 and 12.
    
    Args:
        month: Month as int or string
        
    Returns:
        int: Valid month
        
    Raises:
        ValueError: If month is not between 1-12
    """
    try:
        month_int = int(month)
        if month_int < 1 or month_int > 12:
            raise ValueError("Month must be between 1 and 12")
        return month_int
    except ValueError as e:
        if "between" in str(e):
            raise
        raise ValueError(f"Invalid month format: {month}")


def validate_year(year: Union[int, str]) -> int:
    """
    Validate year is reasonable (between 2020 and 2100).
    
    Args:
        year: Year as int or string
        
    Returns:
        int: Valid year
        
    Raises:
        ValueError: If year is not reasonable
    """
    try:
        year_int = int(year)
        if year_int < 2020 or year_int > 2100:
            raise ValueError("Year must be between 2020 and 2100")
        return year_int
    except ValueError as e:
        if "between" in str(e):
            raise
        raise ValueError(f"Invalid year format: {year}")


def validate_projection_months(months: Union[int, str]) -> int:
    """
    Validate projection months is between 1 and 60.
    
    Args:
        months: Number of months as int or string
        
    Returns:
        int: Valid number of months
        
    Raises:
        ValueError: If months is not between 1-60
    """
    try:
        months_int = int(months)
        if months_int < 1 or months_int > 60:
            raise ValueError("Projection months must be between 1 and 60")
        return months_int
    except ValueError as e:
        if "between" in str(e):
            raise
        raise ValueError(f"Invalid months format: {months}")


def validate_cutoff_day(day: Union[int, str]) -> int:
    """
    Validate cutoff day is between 1 and 31.
    
    Args:
        day: Day as int or string
        
    Returns:
        int: Valid day
        
    Raises:
        ValueError: If day is not between 1-31
    """
    try:
        day_int = int(day)
        if day_int < 1 or day_int > 31:
            raise ValueError("Cutoff day must be between 1 and 31")
        return day_int
    except ValueError as e:
        if "between" in str(e):
            raise
        raise ValueError(f"Invalid day format: {day}")


def validate_date_string(date_str: Optional[str]) -> Optional[date]:
    """
    Validate date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string or None
        
    Returns:
        date: Parsed date or None if input was None
        
    Raises:
        ValueError: If date string is invalid format
    """
    if date_str is None or date_str.strip() == "":
        return None
    
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {date_str}")