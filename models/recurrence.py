from datetime import date, timedelta
from typing import Optional, Literal

class Recurrence:
    def __init__(
        self,
        kind: Literal['interval', 'calendar'],
        interval: Optional[str] = None,
        every: Optional[int] = None,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ):
        self.kind = kind
        self.interval = interval
        self.every = every
        self.start = start
        self.end = end

    @staticmethod
    def from_dict(data: dict) -> 'Recurrence':
        from datetime import datetime, date
        start = data.get('start')
        if isinstance(start, str):
            try:
                start = datetime.strptime(start, "%Y-%m-%d").date()
            except Exception:
                start = None

        end = data.get('end')
        if isinstance(end, str):
            try:
                end = datetime.strptime(end, "%Y-%m-%d").date()
            except Exception:
                end = None

        return Recurrence(
            kind=data.get('kind'),
            interval=data.get('interval'),
            every=data.get('every'),
            start=start,
            end=end
        )

    def to_dict(self) -> dict:
        return {
            'kind': self.kind,
            'interval': self.interval,
            'every': self.every,
            'start': self.start.strftime('%Y-%m-%d') if self.start else None,
            'end': self.end.strftime('%Y-%m-%d') if self.end else None
        }

    def next_due(self, after: Optional[date] = None) -> Optional[date]:
        """Calculate the next due date after a given date, respecting end date if set."""
        if self.kind == 'interval' and self.interval and self.every and self.start:
            if self.interval == 'daily':
                delta = timedelta(days=self.every)
            elif self.interval == 'weekly':
                delta = timedelta(weeks=self.every)
            elif self.interval == 'monthly':
                # For monthly intervals, use precise month calculation instead of approximation
                return self._calculate_monthly_interval(after)
            elif self.interval == 'quarterly':
                # Approximate 3 months as 91 days
                delta = timedelta(days=91 * self.every)
            elif self.interval == 'yearly':
                # Approximate 1 year as 365 days
                delta = timedelta(days=365 * self.every)
            else:
                return None
            
            base_date = after or date.today()
            
            # If the base date is before or on the start date, return start date
            if base_date <= self.start:
                return self.start
            
            # Calculate how many intervals have passed since start
            days_since_start = (base_date - self.start).days
            interval_days = delta.days
            intervals_passed = days_since_start // interval_days
            
            # Calculate the next occurrence
            next_date = self.start + timedelta(days=(intervals_passed + 1) * interval_days)
            
            if self.end and next_date > self.end:
                return None
            return next_date
        elif self.kind == 'calendar' and self.start:
            base_date = after or date.today()
            interval = self.interval or 'monthly'
            
            # If the base date is before or on the start date, return start date
            if base_date <= self.start:
                return self.start
            
            # For multi-month intervals, we need to calculate from the start date
            if interval == 'monthly' and self.every and self.every > 1:
                # Calculate the next occurrence based on start date
                current_date = self.start
                while current_date <= base_date:
                    # Add the interval in months
                    month = current_date.month + self.every
                    year = current_date.year
                    day = current_date.day
                    
                    while month > 12:
                        month -= 12
                        year += 1
                    
                    try:
                        current_date = date(year, month, day)
                    except ValueError:
                        from calendar import monthrange
                        last_day = monthrange(year, month)[1]
                        current_date = date(year, month, last_day)
                
                if self.end and current_date > self.end:
                    return None
                return current_date
            
            # For single month intervals, use the simpler logic
            year = base_date.year
            month = base_date.month
            day = self.start.day
            
            # Try to create the payment date for current month
            try:
                current_month_payment = date(year, month, day)
            except ValueError:
                # Day doesn't exist in current month (e.g., Feb 30th)
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                current_month_payment = date(year, month, last_day)
            
            # If current month's payment is after our base date, return it
            if current_month_payment > base_date:
                if self.end and current_month_payment > self.end:
                    return None
                return current_month_payment
            
            # Otherwise, advance to next period
            if interval == 'monthly':
                month += 1
            elif interval == 'quarterly':
                month += 3
            elif interval == 'yearly':
                year += 1
            else:
                month += 1
            
            while month > 12:
                month -= 12
                year += 1
            
            try:
                next_date = date(year, month, day)
            except ValueError:
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                next_date = date(year, month, last_day)
            
            if self.end and next_date > self.end:
                return None
            return next_date
        return None
    
    def _calculate_monthly_interval(self, after: Optional[date] = None) -> Optional[date]:
        """Calculate next due date for monthly interval recurrence."""
        base_date = after or date.today()
        
        # If the base date is before or on the start date, return start date
        if base_date <= self.start:
            return self.start
        
        # Calculate the next occurrence based on start date
        current_date = self.start
        while current_date <= base_date:
            # Add the interval in months
            month = current_date.month + self.every
            year = current_date.year
            day = current_date.day
            
            while month > 12:
                month -= 12
                year += 1
            
            try:
                current_date = date(year, month, day)
            except ValueError:
                # Handle cases like Feb 31st by using last day of month
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                current_date = date(year, month, last_day)
        
        if self.end and current_date > self.end:
            return None
        return current_date
