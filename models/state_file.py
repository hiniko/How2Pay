from typing import List, Dict, Any, Optional
from models.bill import Bill
from models.payee import Payee
from models.schedule_options import ScheduleOptions

class StateFile:
    def __init__(
        self, 
        bills: Optional[List[Bill]] = None, 
        payees: Optional[List[Payee]] = None,
        schedule_options: Optional[ScheduleOptions] = None
    ):
        self.bills = bills or []
        self.payees = payees or []
        self.schedule_options = schedule_options or ScheduleOptions()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'StateFile':
        bills = [Bill.from_dict(b) for b in data.get('bills', [])]
        payees = [Payee.from_dict(p) for p in data.get('payees', [])]
        schedule_options_data = data.get('schedule_options')
        schedule_options = ScheduleOptions.from_dict(schedule_options_data) if schedule_options_data else ScheduleOptions()
        return StateFile(bills=bills, payees=payees, schedule_options=schedule_options)

    def to_dict(self) -> dict:
        return {
            'bills': [b.to_dict() for b in self.bills],
            'payees': [p.to_dict() for p in self.payees],
            'schedule_options': self.schedule_options.to_dict()
        }
