
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
        
        # Deserialize share information
        share = []
        share_data = data.get('share', [])
        if isinstance(share_data, list):
            for share_item in share_data:
                if isinstance(share_item, dict):
                    share.append(BillShare(
                        payee=share_item.get('payee', ''),
                        percentage=share_item.get('percentage', 0.0)
                    ))
        
        return Bill(
            name=data.get('name'),
            amount=data.get('amount'),
            recurrence=recurrence,
            share=share,
            ends=data.get('ends'),
            description=data.get('description')
        )

    def to_dict(self) -> dict:
        # Serialize share information
        share_data = []
        for share_item in self.share:
            share_data.append({
                'payee': share_item.payee,
                'percentage': share_item.percentage
            })
        
        return {
            'name': self.name,
            'amount': self.amount,
            'recurrence': self.recurrence.to_dict() if self.recurrence else None,
            'share': share_data,
            'ends': self.ends,
            'description': self.description
        }
    
    def get_payee_percentage(self, payee_name: str) -> float:
        """Get the percentage for a specific payee, or 0 if not assigned."""
        for share in self.share:
            if share.payee == payee_name:
                return share.percentage
        return 0.0
    
    def set_payee_percentage(self, payee_name: str, percentage: float) -> None:
        """Set the percentage for a specific payee."""
        # Remove existing entry for this payee
        self.share = [s for s in self.share if s.payee != payee_name]
        # Add new entry if percentage > 0
        if percentage > 0:
            self.share.append(BillShare(payee_name, percentage))
    
    def get_total_percentage(self) -> float:
        """Get the sum of all assigned percentages."""
        return sum(share.percentage for share in self.share)
    
    def has_custom_shares(self) -> bool:
        """Check if this bill has custom percentage assignments."""
        return len(self.share) > 0
    
    def validate_percentages(self) -> tuple[bool, str]:
        """Validate that percentages sum to 100% and are all non-negative."""
        total = self.get_total_percentage()
        
        # Check for negative percentages
        for share in self.share:
            if share.percentage < 0:
                return False, f"Payee '{share.payee}' has negative percentage: {share.percentage}%"
            if share.percentage > 100:
                return False, f"Payee '{share.payee}' has percentage over 100%: {share.percentage}%"
        
        # Check total
        if abs(total - 100.0) > 0.01:  # Allow small floating point errors
            return False, f"Total percentages must equal 100%, got {total}%"
        
        return True, "Valid"
