from datetime import date, timedelta
from typing import List, Tuple
from dataclasses import dataclass
from models.state_file import StateFile
from models.bill import Bill
from models.payee import Payee, PaySchedule

@dataclass
class PaymentScheduleItem:
    payee_name: str
    schedule_description: str
    income_amount: float
    required_contribution: float
    contribution_percentage: float
    payment_date: date
    is_before_cutoff: bool

@dataclass
class MonthlyBillTotal:
    month: int
    year: int
    total_bills: float

@dataclass 
class WeekendAdjustment:
    payee_name: str
    schedule_description: str
    original_date: date
    adjusted_date: date
    income_amount: float

@dataclass
class PaymentScheduleResult:
    """Complete payment schedule result containing all data needed for display/export."""
    schedule_items: List[PaymentScheduleItem]
    monthly_bill_totals: List[MonthlyBillTotal]
    weekend_adjustments: List[WeekendAdjustment]
    start_month: int
    start_year: int
    months_ahead: int

class CashFlowScheduler:
    def __init__(self, state: StateFile, projection_start_month: int = None, projection_start_year: int = None):
        self.state = state
        self.schedule_options = state.schedule_options
        self.projection_start_month = projection_start_month
        self.projection_start_year = projection_start_year
    
    def _get_month_boundaries(self, month: int, year: int) -> Tuple[date, date]:
        """Get the first and last day of a month."""
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        return month_start, month_end
    
    def _adjust_month_year(self, month: int, year: int) -> Tuple[int, int]:
        """Handle month/year rollover (e.g., month 13 -> month 1, year+1)."""
        adjusted_year = year
        adjusted_month = month
        while adjusted_month > 12:
            adjusted_month -= 12
            adjusted_year += 1
        while adjusted_month < 1:
            adjusted_month += 12
            adjusted_year -= 1
        return adjusted_month, adjusted_year
    
    def _is_before_projection_start(self, month: int, year: int) -> bool:
        """Check if a month/year is before the projection start date."""
        if not (self.projection_start_month and self.projection_start_year):
            return False
        return (year < self.projection_start_year or 
                (year == self.projection_start_year and month < self.projection_start_month))
    
    def _create_no_income_item(self, payee_name: str, per_payee_responsibility: float, cutoff_date: date) -> PaymentScheduleItem:
        """Create a placeholder entry for a payee with no income in the funding month."""
        return PaymentScheduleItem(
            payee_name=payee_name,
            schedule_description="No income in previous month",
            income_amount=0.0,
            required_contribution=per_payee_responsibility,
            contribution_percentage=0.0,
            payment_date=cutoff_date,
            is_before_cutoff=False
        )
    
    def _calculate_weekend_adjustment_shortfall(self, payee: Payee, income_month: int, income_year: int, 
                                               per_payee_responsibility: float, total_income: float) -> float:
        """Calculate shortfall caused by weekend adjustments moving payments out of funding month."""
        weekend_adjustments = self.check_for_weekend_adjusted_payments(payee, income_month, income_year)
        weekend_adjusted_shortfall = 0.0
        
        for schedule, orig_date, adj_date in weekend_adjustments:
            # If the payment was moved out of the income month, it creates a shortfall
            if orig_date.month == income_month and orig_date.year == income_year:
                if schedule.contribution_percentage is not None:
                    # Custom percentage - add the expected contribution to shortfall
                    weekend_adjusted_shortfall += per_payee_responsibility * (schedule.contribution_percentage / 100)
                else:
                    # Would have been proportional - estimate the shortfall
                    if total_income > 0:
                        proportion = schedule.amount / total_income
                        weekend_adjusted_shortfall += per_payee_responsibility * proportion
        
        return weekend_adjusted_shortfall
    
    def _create_schedule_item(self, payee_name: str, schedule: PaySchedule, payment_date: date, 
                             required_contribution: float) -> PaymentScheduleItem:
        """Create a PaymentScheduleItem for a schedule."""
        contribution_percentage = (required_contribution / schedule.amount) * 100 if schedule.amount > 0 else 0
        return PaymentScheduleItem(
            payee_name=payee_name,
            schedule_description=schedule.description or f"{schedule.recurrence.interval} payment",
            income_amount=schedule.amount,
            required_contribution=required_contribution,
            contribution_percentage=contribution_percentage,
            payment_date=payment_date,
            is_before_cutoff=True
        )
    
    def _process_custom_percentage_schedules(self, payee: Payee, income_schedules: List[Tuple[PaySchedule, date]], 
                                           per_payee_responsibility: float, total_income: float, 
                                           weekend_adjusted_shortfall: float) -> Tuple[List[PaymentScheduleItem], float, List[Tuple[PaySchedule, date]]]:
        """Process schedules with custom contribution percentages."""
        schedule_items = []
        total_custom_bill_percentage = 0.0
        remaining_schedules = []
        
        for schedule, payment_date in income_schedules:
            if schedule.contribution_percentage is not None:
                # Use custom percentage OF THE BILLS (not of income)
                base_contribution = per_payee_responsibility * (schedule.contribution_percentage / 100)
                
                # Add proportional share of weekend adjustment shortfall
                weekend_adjustment_share = 0.0
                if weekend_adjusted_shortfall > 0 and total_income > 0:
                    income_proportion = schedule.amount / total_income
                    weekend_adjustment_share = weekend_adjusted_shortfall * income_proportion
                
                required_contribution = base_contribution + weekend_adjustment_share
                total_custom_bill_percentage += schedule.contribution_percentage
                
                schedule_items.append(self._create_schedule_item(payee.name, schedule, payment_date, required_contribution))
            else:
                remaining_schedules.append((schedule, payment_date))
        
        return schedule_items, total_custom_bill_percentage, remaining_schedules
    
    def _process_remaining_schedules(self, payee: Payee, remaining_schedules: List[Tuple[PaySchedule, date]], 
                                   per_payee_responsibility: float, remaining_bill_percentage: float, 
                                   total_income: float, weekend_adjusted_shortfall: float) -> List[PaymentScheduleItem]:
        """Process remaining schedules (those without custom percentages) proportionally."""
        schedule_items = []
        
        if remaining_bill_percentage <= 0 or not remaining_schedules:
            # Handle case where no remaining percentage or schedules need weekend adjustment compensation
            for schedule, payment_date in remaining_schedules:
                weekend_adjustment_share = 0.0
                if weekend_adjusted_shortfall > 0 and total_income > 0:
                    income_proportion = schedule.amount / total_income
                    weekend_adjustment_share = weekend_adjusted_shortfall * income_proportion
                
                schedule_items.append(self._create_schedule_item(payee.name, schedule, payment_date, weekend_adjustment_share))
            return schedule_items
        
        # Normal case: distribute remaining bill percentage proportionally
        total_remaining_income = sum(schedule.amount for schedule, _ in remaining_schedules)
        
        for schedule, payment_date in remaining_schedules:
            if total_remaining_income > 0:
                # Proportionally allocate remaining bill percentage based on income amounts
                proportion = schedule.amount / total_remaining_income
                bill_percentage_for_this_stream = remaining_bill_percentage * proportion
                base_contribution = per_payee_responsibility * (bill_percentage_for_this_stream / 100)
                
                # Add proportional share of weekend adjustment shortfall
                weekend_adjustment_share = 0.0
                if weekend_adjusted_shortfall > 0 and total_income > 0:
                    income_proportion = schedule.amount / total_income
                    weekend_adjustment_share = weekend_adjusted_shortfall * income_proportion
                
                required_contribution = base_contribution + weekend_adjustment_share
            else:
                required_contribution = 0.0
            
            schedule_items.append(self._create_schedule_item(payee.name, schedule, payment_date, required_contribution))
        
        return schedule_items
    
    def _process_proportional_schedules(self, payee: Payee, income_schedules: List[Tuple[PaySchedule, date]], 
                                       per_payee_responsibility: float, total_income: float, 
                                       weekend_adjusted_shortfall: float) -> List[PaymentScheduleItem]:
        """Process schedules using pure proportional allocation (no custom percentages)."""
        schedule_items = []
        
        for schedule, payment_date in income_schedules:
            if total_income > 0:
                proportion = schedule.amount / total_income
                base_contribution = per_payee_responsibility * proportion
                
                # Add proportional share of weekend adjustment shortfall
                weekend_adjustment_share = 0.0
                if weekend_adjusted_shortfall > 0:
                    weekend_adjustment_share = weekend_adjusted_shortfall * proportion
                
                required_contribution = base_contribution + weekend_adjustment_share
            else:
                required_contribution = 0.0
            
            schedule_items.append(self._create_schedule_item(payee.name, schedule, payment_date, required_contribution))
        
        return schedule_items
    
    def calculate_monthly_bill_total(self, target_month: int, target_year: int) -> float:
        """Calculate total bills due in the target month."""
        if self._is_before_projection_start(target_month, target_year):
            return 0.0
            
        month_start, month_end = self._get_month_boundaries(target_month, target_year)
        total = 0.0
        
        for bill in self.state.bills:
            if not bill.recurrence:
                continue
                
            # Check if this bill is due within the target month
            # Start checking from just before the month start
            check_date = month_start - timedelta(days=1)
            max_checks = 10  # Reasonable limit for checking multiple occurrences
            
            for _ in range(max_checks):
                next_payment = bill.recurrence.next_due(check_date)
                
                if not next_payment:
                    break
                
                # If the payment is beyond our target month, stop looking
                if next_payment > month_end:
                    break
                
                # If the payment is within our target month, count it
                if next_payment >= month_start and next_payment <= month_end:
                    total += bill.amount
                
                # Move to the next potential date (past current payment to find next occurrence)
                check_date = next_payment + timedelta(days=1)
        
        return total
    
    def get_payee_income_before_cutoff(self, payee: Payee, cutoff_date: date, month_start: date) -> List[Tuple[PaySchedule, date]]:
        """Get all income payments for a payee that occur between month start and cutoff date."""
        income_before_cutoff = []
        
        for schedule in payee.pay_schedules:
            if not schedule.recurrence:
                continue
                
            # Use a set to track found payment dates for this schedule to avoid duplicates
            found_dates = set()
            
            # Start checking from just before the month start
            check_date = month_start - timedelta(days=1)
            max_checks = 50  # Reasonable limit for monthly checks
            
            for _ in range(max_checks):
                next_payment = schedule.recurrence.next_due(check_date)
                
                if not next_payment:
                    break
                
                # Apply weekend adjustment to the payment date
                adjusted_payment = schedule.get_adjusted_payment_date(next_payment)
                
                # If the adjusted payment is beyond our cutoff date, stop looking
                if adjusted_payment > cutoff_date:
                    break
                
                # If the adjusted payment is in our target month and before/on cutoff, count it
                if (adjusted_payment >= month_start and 
                    adjusted_payment <= cutoff_date and 
                    adjusted_payment.month == cutoff_date.month and 
                    adjusted_payment.year == cutoff_date.year):
                    
                    if adjusted_payment not in found_dates:
                        found_dates.add(adjusted_payment)
                        income_before_cutoff.append((schedule, adjusted_payment))
                
                # Move to the next potential date
                check_date = next_payment
        
        return income_before_cutoff
    
    def get_payee_income_in_month(self, payee: Payee, month_start: date, month_end: date) -> List[Tuple[PaySchedule, date]]:
        """Get all income payments for a payee that occur during a specific month."""
        income_in_month = []
        
        for schedule in payee.pay_schedules:
            if not schedule.recurrence:
                continue
                
            # Use a set to track found payment dates for this schedule to avoid duplicates
            found_dates = set()
            
            # Start checking from just before the month start
            check_date = month_start - timedelta(days=1)
            max_checks = 50  # Reasonable limit for monthly checks
            
            for _ in range(max_checks):
                next_payment = schedule.recurrence.next_due(check_date)
                
                if not next_payment:
                    break
                
                # Apply weekend adjustment to the payment date
                adjusted_payment = schedule.get_adjusted_payment_date(next_payment)
                
                # If the adjusted payment is beyond our month, stop looking
                if adjusted_payment > month_end:
                    break
                
                # If the adjusted_payment is in our target month, count it
                if (adjusted_payment >= month_start and 
                    adjusted_payment <= month_end):
                    
                    if adjusted_payment not in found_dates:
                        found_dates.add(adjusted_payment)
                        income_in_month.append((schedule, adjusted_payment))
                
                # Move to the next potential date
                check_date = next_payment + timedelta(days=1)
        
        return income_in_month
    
    def calculate_proportional_contributions(self, start_month: int, start_year: int, months_ahead: int = 12) -> PaymentScheduleResult:
        """Calculate how much each payee should contribute based on their income timing over multiple months."""
        schedule_items = []
        monthly_bill_totals = []
        weekend_adjustments = []
        
        # Calculate for each month in the projection period
        for month_offset in range(months_ahead):
            current_month, current_year = self._adjust_month_year(start_month + month_offset, start_year)
            
            cutoff_date = self.schedule_options.get_cutoff_date(current_month, current_year)
            total_bills = self.calculate_monthly_bill_total(current_month, current_year)
            
            # Store monthly bill total
            monthly_bill_totals.append(MonthlyBillTotal(current_month, current_year, total_bills))
            
            # Skip months with no bills (like setup months before the projection starts)
            if total_bills <= 0:
                continue
            
            # For income, look at the PREVIOUS month
            # Income received during the previous month is used to pay this month's bills
            income_month, income_year = self._adjust_month_year(current_month - 1, current_year)
            income_month_start, income_month_end = self._get_month_boundaries(income_month, income_year)
            
            # Equal responsibility among payees
            num_payees = len(self.state.payees)
            if num_payees == 0:
                continue
            
            per_payee_responsibility = total_bills / num_payees
            
            for payee in self.state.payees:
                # Get all income during the previous month (which will be used to pay this month's bills)
                income_during_previous_month = self.get_payee_income_in_month(payee, income_month_start, income_month_end)
                
                if not income_during_previous_month:
                    schedule_items.append(self._create_no_income_item(payee.name, per_payee_responsibility, cutoff_date))
                    continue
                
                # Calculate total income available from previous month
                total_income_from_previous_month = sum(schedule.amount for schedule, _ in income_during_previous_month)
                
                # Check for weekend-adjusted payments that were moved out of the funding month
                weekend_adjusted_shortfall = self._calculate_weekend_adjustment_shortfall(
                    payee, income_month, income_year, per_payee_responsibility, total_income_from_previous_month)
                
                # Collect weekend adjustments for this payee/month for display purposes
                payee_weekend_adjustments = self.check_for_weekend_adjusted_payments(payee, current_month, current_year)
                for schedule, orig_date, adj_date in payee_weekend_adjustments:
                    weekend_adjustments.append(WeekendAdjustment(
                        payee_name=payee.name,
                        schedule_description=schedule.description or f"{schedule.recurrence.interval} payment",
                        original_date=orig_date,
                        adjusted_date=adj_date,
                        income_amount=schedule.amount
                    ))
                
                # Check if any schedules have custom contribution percentages
                has_custom_percentages = any(schedule.contribution_percentage is not None for schedule, _ in income_during_previous_month)
                
                if has_custom_percentages:
                    # Process custom percentages first, then handle remaining schedules
                    custom_items, total_custom_bill_percentage, remaining_schedules = self._process_custom_percentage_schedules(
                        payee, income_during_previous_month, per_payee_responsibility, 
                        total_income_from_previous_month, weekend_adjusted_shortfall)
                    schedule_items.extend(custom_items)
                    
                    # Process remaining schedules without custom percentages
                    remaining_bill_percentage = 100.0 - total_custom_bill_percentage
                    remaining_items = self._process_remaining_schedules(
                        payee, remaining_schedules, per_payee_responsibility, remaining_bill_percentage,
                        total_income_from_previous_month, weekend_adjusted_shortfall)
                    schedule_items.extend(remaining_items)
                else:
                    # Use pure proportional allocation
                    proportional_items = self._process_proportional_schedules(
                        payee, income_during_previous_month, per_payee_responsibility,
                        total_income_from_previous_month, weekend_adjusted_shortfall)
                    schedule_items.extend(proportional_items)
        
        return PaymentScheduleResult(
            schedule_items=schedule_items,
            monthly_bill_totals=monthly_bill_totals,
            weekend_adjustments=weekend_adjustments,
            start_month=start_month,
            start_year=start_year,
            months_ahead=months_ahead
        )
    
    def check_for_weekend_adjusted_payments(self, payee: Payee, target_month: int, target_year: int) -> List[Tuple[PaySchedule, date, date]]:
        """Check if any payments were moved out of the target month due to weekend adjustment.
        
        Returns list of tuples: (schedule, original_date, adjusted_date)
        """
        adjusted_payments = []
        
        for schedule in payee.pay_schedules:
            if not schedule.recurrence:
                continue
                
            # Check for payments that would naturally occur in this month
            month_start = date(target_year, target_month, 1)
            if target_month == 12:
                month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(target_year, target_month + 1, 1) - timedelta(days=1)
            
            # Look for payments that should occur in this month
            check_date = month_start - timedelta(days=1)
            max_checks = 10
            
            for _ in range(max_checks):
                next_payment = schedule.recurrence.next_due(check_date)
                
                if not next_payment or next_payment > month_end:
                    break
                
                # If the original payment is in our target month
                if next_payment >= month_start and next_payment <= month_end:
                    adjusted_payment = schedule.get_adjusted_payment_date(next_payment)
                    
                    # If adjustment moved it outside the month, record it
                    if adjusted_payment > month_end or adjusted_payment < month_start:
                        adjusted_payments.append((schedule, next_payment, adjusted_payment))
                
                check_date = next_payment
        
        return adjusted_payments

def generate_payment_schedule(state_file_path: str, target_month: int, target_year: int, output_csv: str = None, display_table: bool = True) -> PaymentScheduleResult:
    """
    Main function to generate payment schedule from state file.
    
    Args:
        state_file_path: Path to the YAML state file
        target_month: Target month (1-12)
        target_year: Target year
        output_csv: Output CSV file path (optional)
        display_table: Whether to display rich table (default True)
    
    Returns:
        PaymentScheduleResult object containing all schedule data
    """
    from helpers.state_ops import load_state
    
    # Load state (assuming we'll modify load_state to accept file path)
    import yaml
    with open(state_file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    state = StateFile.from_dict(data)
    
    scheduler = CashFlowScheduler(state)
    result = scheduler.calculate_proportional_contributions(
        start_month=target_month, 
        start_year=target_year, 
        months_ahead=12
    )
    
    if display_table:
        from tui.payment_schedule_display import PaymentScheduleDisplay
        from rich.console import Console
        console = Console()
        display = PaymentScheduleDisplay(console)
        display.display_pivot_table(result)
    
    if output_csv:
        from exporters.csv_exporter import CsvExporter
        CsvExporter.export_payment_schedule(result, output_csv)
    
    return result
