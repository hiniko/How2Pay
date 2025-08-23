from datetime import date, timedelta
from typing import Literal, Optional
from calendar import monthrange

class ScheduleOptions:
    def __init__(
        self,
        cutoff_day: int = 28,  # Default to 28th of month (usually safe for all months)
        weekend_adjustment: Literal['last_working_day', 'next_working_day'] = 'last_working_day',
        default_projection_months: int = 12  # Default number of months to project
    ):
        self.cutoff_day = cutoff_day
        self.weekend_adjustment = weekend_adjustment
        self.default_projection_months = default_projection_months

    @staticmethod
    def from_dict(data: dict) -> 'ScheduleOptions':
        return ScheduleOptions(
            cutoff_day=data.get('cutoff_day', 28),
            weekend_adjustment=data.get('weekend_adjustment', 'last_working_day'),
            default_projection_months=data.get('default_projection_months', 12)
        )

    def to_dict(self) -> dict:
        return {
            'cutoff_day': self.cutoff_day,
            'weekend_adjustment': self.weekend_adjustment,
            'default_projection_months': self.default_projection_months
        }

    def get_cutoff_date(self, month: int, year: int) -> date:
        """Get the actual cutoff date for a given month/year, adjusted for weekends."""
        # Handle case where cutoff_day is beyond the month's days
        last_day = monthrange(year, month)[1]
        actual_day = min(self.cutoff_day, last_day)
        
        cutoff_date = date(year, month, actual_day)
        
        # Adjust for weekends (Saturday = 5, Sunday = 6)
        if cutoff_date.weekday() >= 5:  # Weekend
            if self.weekend_adjustment == 'last_working_day':
                # Move backwards to Friday
                days_back = cutoff_date.weekday() - 4  # 5-4=1 for Sat, 6-4=2 for Sun
                cutoff_date = cutoff_date - timedelta(days=days_back)
            else:  # next_working_day
                # Move forward to Monday
                days_forward = 7 - cutoff_date.weekday()  # 7-5=2 for Sat, 7-6=1 for Sun
                cutoff_date = cutoff_date + timedelta(days=days_forward)
        
        return cutoff_date

    def get_current_month_cutoff(self, reference_date: Optional[date] = None) -> date:
        """Get the cutoff date for the current month."""
        ref = reference_date or date.today()
        return self.get_cutoff_date(ref.month, ref.year)

    def get_next_month_cutoff(self, reference_date: Optional[date] = None) -> date:
        """Get the cutoff date for the next month."""
        ref = reference_date or date.today()
        next_month = ref.month + 1
        next_year = ref.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return self.get_cutoff_date(next_month, next_year)
