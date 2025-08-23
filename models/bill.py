
from typing import List, Optional
from datetime import date
from models.recurrence import Recurrence

class BillShare:
    def __init__(self, payee: str, percentage: float):
        self.payee = payee
        self.percentage = percentage

class Bill:
    def __init__(
        self,
        name: str,
        amount: float,
        recurrence: Optional[Recurrence],
        share: Optional[List[BillShare]] = None,
        ends: Optional[date] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.amount = amount
        self.recurrence = recurrence
        self.share = share or []
        self.ends = ends
        self.description = description

    @staticmethod
    def from_dict(data: dict) -> 'Bill':
        recurrence = data.get('recurrence')
        if isinstance(recurrence, dict):
            recurrence = Recurrence.from_dict(recurrence)
        return Bill(
            name=data.get('name'),
            amount=data.get('amount'),
            recurrence=recurrence,
            share=[],  # Add share deserialization if needed
            ends=data.get('ends'),
            description=data.get('description')
        )

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'amount': self.amount,
            'recurrence': self.recurrence.to_dict() if self.recurrence else None,
            'share': [],  # Add share serialization if needed
            'ends': self.ends,
            'description': self.description
        }
