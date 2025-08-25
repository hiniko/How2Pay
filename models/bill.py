
from typing import List, Optional
from datetime import date
from models.recurrence import Recurrence

class BillShare:
    def __init__(self, payee: str, percentage: float):
        self.payee = payee
        self.percentage = percentage

class BillPriceHistory:
    def __init__(self, amount: float, recurrence: Recurrence, start_date: date):
        self.amount = amount
        self.recurrence = recurrence
        self.start_date = start_date
    
    @staticmethod
    def from_dict(data: dict) -> 'BillPriceHistory':
        from datetime import datetime
        recurrence = data.get('recurrence')
        if isinstance(recurrence, dict):
            recurrence = Recurrence.from_dict(recurrence)
        
        start_date = data.get('start_date')
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        return BillPriceHistory(
            amount=data.get('amount'),
            recurrence=recurrence,
            start_date=start_date
        )
    
    def to_dict(self) -> dict:
        return {
            'amount': self.amount,
            'recurrence': self.recurrence.to_dict() if self.recurrence else None,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None
        }

class Bill:
    def __init__(
        self,
        name: str,
        amount: Optional[float] = None,
        recurrence: Optional[Recurrence] = None,
        price_history: Optional[List[BillPriceHistory]] = None,
        share: Optional[List[BillShare]] = None,
        ends: Optional[date] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.share = share or []
        self.ends = ends
        self.description = description
        
        # Support both old format (amount/recurrence) and new format (price_history)
        if price_history is not None:
            self.price_history = sorted(price_history, key=lambda x: x.start_date)
        elif amount is not None and recurrence is not None:
            # Convert old format to new format with a default start date
            default_start = recurrence.start if recurrence.start else date(2024, 1, 1)
            self.price_history = [BillPriceHistory(amount, recurrence, default_start)]
        else:
            self.price_history = []

    @staticmethod
    def from_dict(data: dict) -> 'Bill':
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
        
        # Handle price_history (new format) or amount/recurrence (old format)
        price_history = None
        if 'price_history' in data:
            price_history = []
            for history_item in data['price_history']:
                if isinstance(history_item, dict):
                    price_history.append(BillPriceHistory.from_dict(history_item))
        
        # Support old format for backwards compatibility
        amount = data.get('amount')
        recurrence = data.get('recurrence')
        if isinstance(recurrence, dict):
            recurrence = Recurrence.from_dict(recurrence)
        
        return Bill(
            name=data.get('name'),
            amount=amount,
            recurrence=recurrence,
            price_history=price_history,
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
        
        # Serialize price history
        price_history_data = []
        for history_item in self.price_history:
            price_history_data.append(history_item.to_dict())
        
        return {
            'name': self.name,
            'price_history': price_history_data,
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
    
    def get_price_info_for_date(self, target_date: date) -> Optional[BillPriceHistory]:
        """Get the appropriate price information for a given date."""
        if not self.price_history:
            return None
        
        # Find the most recent price history entry that starts before or on the target date
        applicable_history = None
        for history in self.price_history:
            if history.start_date <= target_date:
                applicable_history = history
            else:
                break  # price_history is sorted by start_date, so we can stop here
        
        return applicable_history
    
    def get_amount_for_date(self, target_date: date) -> Optional[float]:
        """Get the bill amount for a given date."""
        price_info = self.get_price_info_for_date(target_date)
        return price_info.amount if price_info else None
    
    def get_recurrence_for_date(self, target_date: date) -> Optional[Recurrence]:
        """Get the recurrence pattern for a given date."""
        price_info = self.get_price_info_for_date(target_date)
        return price_info.recurrence if price_info else None
    
    # Backward compatibility properties
    @property
    def amount(self) -> Optional[float]:
        """Get current amount (for backward compatibility)."""
        if self.price_history:
            return self.price_history[-1].amount
        return None
    
    @property
    def recurrence(self) -> Optional[Recurrence]:
        """Get current recurrence (for backward compatibility)."""
        if self.price_history:
            return self.price_history[-1].recurrence
        return None
