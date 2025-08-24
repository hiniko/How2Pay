from typing import Optional, List, Literal
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
    ):
        self.name = name
        self.pay_schedules = pay_schedules or []
        self.description = description

    @staticmethod
    def from_dict(data: dict) -> 'Payee':
        pay_schedules = []
        schedules_data = data.get('pay_schedules', [])
        for schedule_data in schedules_data:
            pay_schedules.append(PaySchedule.from_dict(schedule_data))
        return Payee(
            name=data.get('name'),
            pay_schedules=pay_schedules,
            description=data.get('description')
        )

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'pay_schedules': [schedule.to_dict() for schedule in self.pay_schedules],
            'description': self.description
        }
