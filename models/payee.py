from typing import Optional, List, Literal
from datetime import date
from models.recurrence import Recurrence

class PaySchedule:
    def __init__(
        self,
        amount: Optional[float] = None,
        recurrence: Recurrence = None,
        description: Optional[str] = None,
        weekend_adjustment: Optional[Literal['last_working_day', 'next_working_day']] = None,
        contribution_percentage: Optional[float] = None,
    ):
        # Use default amount if not provided (for calculation purposes only)
        self.amount = amount or 1000.0  # Default placeholder amount
        self.recurrence = recurrence
        self.description = description
        self.weekend_adjustment = weekend_adjustment or 'last_working_day'
        self.contribution_percentage = contribution_percentage  # If set, use this instead of proportional split

    @staticmethod
    def from_dict(data: dict) -> 'PaySchedule':
        recurrence = data.get('recurrence')
        if isinstance(recurrence, dict):
            recurrence = Recurrence.from_dict(recurrence)
        return PaySchedule(
            amount=data.get('amount'),  # Will use default if None
            recurrence=recurrence,
            description=data.get('description'),
            weekend_adjustment=data.get('weekend_adjustment'),
            contribution_percentage=data.get('contribution_percentage')
        )

    def to_dict(self) -> dict:
        return {
            'amount': self.amount,
            'recurrence': self.recurrence.to_dict() if self.recurrence else None,
            'description': self.description,
            'weekend_adjustment': self.weekend_adjustment,
            'contribution_percentage': self.contribution_percentage
        }

    def get_adjusted_payment_date(self, payment_date):
        """Apply weekend adjustment to a payment date."""
        from datetime import timedelta
        
        # If it's already a weekday (Monday=0, Sunday=6), no adjustment needed
        if payment_date.weekday() < 5:  # Monday to Friday
            return payment_date
        
        if self.weekend_adjustment == 'last_working_day':
            # Move backward to Friday
            days_to_subtract = payment_date.weekday() - 4  # Friday is weekday 4
            return payment_date - timedelta(days=days_to_subtract)
        elif self.weekend_adjustment == 'next_working_day':
            # Move forward to Monday
            days_to_add = 7 - payment_date.weekday()  # Monday is weekday 0
            return payment_date + timedelta(days=days_to_add)
        else:
            return payment_date

class Payee:
    def __init__(
        self,
        name: str,
        pay_schedules: Optional[List[PaySchedule]] = None,
        description: Optional[str] = None,
        start_date: Optional[date] = None,
    ):
        self.name = name
        self.pay_schedules = pay_schedules or []
        self.description = description
        self.start_date = start_date  # Date when payee starts contributing to bills

    @staticmethod
    def from_dict(data: dict) -> 'Payee':
        pay_schedules = []
        schedules_data = data.get('pay_schedules', [])
        for schedule_data in schedules_data:
            pay_schedules.append(PaySchedule.from_dict(schedule_data))
            
        # Parse start_date if provided
        start_date = None
        start_date_str = data.get('start_date')
        if start_date_str:
            if isinstance(start_date_str, str):
                start_date = date.fromisoformat(start_date_str)
            elif isinstance(start_date_str, date):
                start_date = start_date_str
                
        return Payee(
            name=data.get('name'),
            pay_schedules=pay_schedules,
            description=data.get('description'),
            start_date=start_date
        )

    def to_dict(self) -> dict:
        result = {
            'name': self.name,
            'pay_schedules': [schedule.to_dict() for schedule in self.pay_schedules],
            'description': self.description
        }
        if self.start_date:
            result['start_date'] = self.start_date.isoformat()
        return result
    
    def is_active_for_month(self, target_year: int, target_month: int) -> bool:
        """
        Check if payee is active (contributing to bills) for the given month.
        
        Args:
            target_year: Year to check
            target_month: Month to check (1-12)
            
        Returns:
            bool: True if payee should contribute to bills in this month
        """
        # If no start date is set, payee is always active
        if not self.start_date:
            return True
            
        # Create date for the first day of the target month
        target_month_start = date(target_year, target_month, 1)
        
        # Payee is active if their start date is on or before the target month
        return self.start_date <= target_month_start
