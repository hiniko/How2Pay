
from typing import List, Optional
from datetime import date
from models.recurrence import Recurrence

class BillShare:
    def __init__(self, exclude: Optional[List[str]] = None, custom: Optional[dict] = None):
        """
        New flexible bill sharing system.
        
        Args:
            exclude: List of payee names to exclude from this bill
            custom: Dictionary of payee_name -> percentage for custom splits
        """
        self.exclude = exclude or []
        self.custom = custom or {}  # payee_name -> percentage
    
    @staticmethod
    def from_dict(data) -> 'BillShare':
        """Parse bill share from dictionary or list format."""
        if isinstance(data, list):
            # Old format: list of {payee: str, percentage: float}
            # Convert to new format for backward compatibility
            custom = {}
            for item in data:
                if isinstance(item, dict) and 'payee' in item and 'percentage' in item:
                    custom[item['payee']] = item['percentage']
            return BillShare(custom=custom)
        elif isinstance(data, dict):
            # New format: {exclude: [...], custom: {payee: percentage}}
            return BillShare(
                exclude=data.get('exclude', []),
                custom=data.get('custom', {})
            )
        else:
            return BillShare()
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        result = {}
        if self.exclude:
            result['exclude'] = self.exclude
        if self.custom:
            result['custom'] = self.custom
        return result if result else None

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
        elif start_date is None and recurrence and recurrence.start:
            # Fall back to recurrence start if no explicit start_date
            start_date = recurrence.start
        
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
        share: Optional[BillShare] = None,
        ends: Optional[date] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.share = share or BillShare()
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
        # Deserialize share information using new format
        share = None
        share_data = data.get('share')
        if share_data is not None:
            share = BillShare.from_dict(share_data)
        
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
    
    def calculate_payee_shares(self, all_payees: List) -> dict:
        """
        Calculate the actual percentage share for each payee based on:
        1. Bill-specific exclusions
        2. Bill-specific custom percentages
        3. Payee default percentages
        4. Equal split for remaining
        
        Args:
            all_payees: List of Payee objects
            
        Returns:
            dict: {payee_name: percentage}
        """
        result = {}
        
        # Start with all active payees
        eligible_payees = [p for p in all_payees if p.name not in self.share.exclude]
        
        if not eligible_payees:
            return result  # No one pays for this bill
        
        # Apply custom percentages from the bill
        remaining_percentage = 100.0
        unassigned_payees = []
        
        for payee in eligible_payees:
            if payee.name in self.share.custom:
                # Use bill-specific custom percentage
                percentage = self.share.custom[payee.name]
                result[payee.name] = percentage
                remaining_percentage -= percentage
            else:
                unassigned_payees.append(payee)
        
        # Handle unassigned payees using defaults or equal split
        if unassigned_payees and remaining_percentage > 0:
            # Check if any unassigned payees have default percentages
            payees_with_defaults = [p for p in unassigned_payees if p.default_share_percentage is not None]
            payees_without_defaults = [p for p in unassigned_payees if p.default_share_percentage is None]
            
            # Calculate total default percentages
            total_defaults = sum(p.default_share_percentage for p in payees_with_defaults)
            
            if total_defaults <= remaining_percentage:
                # Apply default percentages
                for payee in payees_with_defaults:
                    result[payee.name] = payee.default_share_percentage
                    remaining_percentage -= payee.default_share_percentage
                
                # Split any remaining percentage equally among payees without defaults
                if payees_without_defaults and remaining_percentage > 0:
                    equal_share = remaining_percentage / len(payees_without_defaults)
                    for payee in payees_without_defaults:
                        result[payee.name] = equal_share
                elif remaining_percentage > 0.01:  # Leftover percentage with no one to assign to
                    # Redistribute proportionally among payees with defaults
                    if payees_with_defaults:
                        for payee in payees_with_defaults:
                            additional = (payee.default_share_percentage / total_defaults) * remaining_percentage
                            result[payee.name] += additional
            else:
                # Default percentages exceed remaining - normalize them
                for payee in payees_with_defaults:
                    normalized = (payee.default_share_percentage / total_defaults) * remaining_percentage
                    result[payee.name] = normalized
                # Payees without defaults get nothing in this case
                for payee in payees_without_defaults:
                    result[payee.name] = 0.0
        
        return result
    
    def get_payee_percentage(self, payee_name: str, all_payees: List = None) -> float:
        """Get the percentage for a specific payee."""
        if all_payees is None:
            # Fallback to old behavior for backward compatibility
            return self.share.custom.get(payee_name, 0.0)
        
        shares = self.calculate_payee_shares(all_payees)
        return shares.get(payee_name, 0.0)
    
    def has_custom_shares(self) -> bool:
        """Check if this bill has custom share configuration."""
        return bool(self.share.exclude or self.share.custom)
    
    def validate_shares(self, all_payees: List) -> tuple[bool, str]:
        """Validate that the share configuration is valid."""
        try:
            shares = self.calculate_payee_shares(all_payees)
            total = sum(shares.values())
            
            # Check total adds up to 100%
            if abs(total - 100.0) > 0.01:
                return False, f"Total percentages equal {total:.2f}%, should be 100%"
            
            # Check for negative percentages
            for payee, percentage in shares.items():
                if percentage < 0:
                    return False, f"Payee '{payee}' has negative percentage: {percentage:.2f}%"
            
            return True, "Valid"
        except Exception as e:
            return False, f"Error calculating shares: {str(e)}"
    
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
