from datetime import date
from typing import Dict, List
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from scheduler.cash_flow import PaymentScheduleResult, WeekendAdjustment


class PaymentScheduleDisplay:
    """Handles TUI display of payment schedules using Rich tables."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
    
    def display_pivot_table(self, result: PaymentScheduleResult) -> None:
        """Display payment schedule as a rich pivot table."""
        # Group data by month and payee/schedule
        monthly_data = defaultdict(lambda: defaultdict(list))
        
        for item in result.schedule_items:
            month_key = item.payment_date.strftime('%Y-%m')
            payee_schedule_key = f"{item.payee_name} - {item.schedule_description}"
            monthly_data[month_key][payee_schedule_key].append(item)
        
        # Create lookup for weekend adjustments
        weekend_adj_lookup = self._create_weekend_adjustment_lookup(result.weekend_adjustments)
        
        # Create lookup for monthly bill totals
        bill_totals_lookup = {f"{bt.year}-{bt.month:02d}": bt.total_bills 
                             for bt in result.monthly_bill_totals}
        
        # Get all unique payee-schedule combinations for columns, grouped by payee
        payee_schedules = defaultdict(list)
        for month_data in monthly_data.values():
            for payee_schedule in month_data.keys():
                payee_name = payee_schedule.split(" - ", 1)[0]
                if payee_schedule not in payee_schedules[payee_name]:
                    payee_schedules[payee_name].append(payee_schedule)
        
        # Sort payees and their schedules
        sorted_payees = sorted(payee_schedules.keys())
        all_payee_schedules = []
        for payee in sorted_payees:
            all_payee_schedules.extend(sorted(payee_schedules[payee]))
        
        # Create table
        table = Table(title=f"12-Month Payment Schedule Starting {result.start_month}/{result.start_year}")
        
        # Add columns - first the fixed columns, then dynamic payee columns
        table.add_column("Month", style="bold yellow", no_wrap=True)
        table.add_column("Detail", style="dim", no_wrap=True)
        table.add_column("Monthly Bills", style="bold red", justify="right")
        
        # Create column headers with payee grouping
        for payee in sorted_payees:
            payee_schedule_list = sorted(payee_schedules[payee])
            for i, payee_schedule in enumerate(payee_schedule_list):
                parts = payee_schedule.split(" - ", 1)
                schedule_desc = parts[1] if len(parts) > 1 else ""
                
                if len(payee_schedule_list) == 1:
                    # Single column for this payee - show payee name
                    header = f"[bold cyan]{payee}[/bold cyan]\\n[dim]{schedule_desc}[/dim]"
                else:
                    # Multiple columns for this payee
                    if i == 0:
                        # First column shows payee name centered over all their columns
                        header = f"[bold cyan]{payee}[/bold cyan]\\n[dim]{schedule_desc}[/dim]"
                    else:
                        # Subsequent columns just show schedule description
                        header = f"[dim]{schedule_desc}[/dim]"
                
                table.add_column(header, justify="right", style="green")
        
        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())
        
        # Skip the first month in display (it's only used for income calculation)
        display_months = sorted_months[1:] if len(sorted_months) > 1 else sorted_months
        
        for month_key in display_months:
            month_data = monthly_data[month_key]
            month_display = date.fromisoformat(f"{month_key}-01").strftime('%B %Y')
            
            # Get monthly bill total for this month
            month_bill_total = bill_totals_lookup.get(month_key, 0.0)
            
            # Payment dates row
            row_dates = [month_display, "Payment Dates", ""]
            for payee_schedule in all_payee_schedules:
                if payee_schedule in month_data:
                    items = month_data[payee_schedule]
                    dates = [item.payment_date.strftime('%m/%d') for item in items]
                    row_dates.append(", ".join(dates))
                else:
                    # Check for weekend adjustments
                    adjustment = self._find_weekend_adjustment(
                        weekend_adj_lookup, payee_schedule, month_key)
                    if adjustment:
                        row_dates.append(f"→{adjustment.adjusted_date.strftime('%m/%d')}")
                    else:
                        row_dates.append("-")
            table.add_row(*row_dates)
            
            # Income amounts row
            row_income = ["", "Income Amount", ""]
            for payee_schedule in all_payee_schedules:
                if payee_schedule in month_data:
                    items = month_data[payee_schedule]
                    amounts = [f"${item.income_amount:.0f}" for item in items]
                    row_income.append(", ".join(amounts))
                else:
                    # Check for weekend adjustments
                    adjustment = self._find_weekend_adjustment(
                        weekend_adj_lookup, payee_schedule, month_key)
                    if adjustment:
                        row_income.append(f"→${adjustment.income_amount:.0f}")
                    else:
                        row_income.append("-")
            table.add_row(*row_income)
            
            # Required contribution row
            row_required = ["", "Required", ""]
            for payee_schedule in all_payee_schedules:
                if payee_schedule in month_data:
                    items = month_data[payee_schedule]
                    amounts = [f"${item.required_contribution:.2f}" for item in items]
                    row_required.append(", ".join(amounts))
                else:
                    # Check for weekend adjustments
                    adjustment = self._find_weekend_adjustment(
                        weekend_adj_lookup, payee_schedule, month_key)
                    if adjustment:
                        row_required.append("→Moved")
                    else:
                        row_required.append("-")
            table.add_row(*row_required, style="bold")
            
            # Percentage row
            row_percentage = ["", "Percentage", ""]
            for payee_schedule in all_payee_schedules:
                if payee_schedule in month_data:
                    items = month_data[payee_schedule]
                    percentages = [f"{item.contribution_percentage:.1f}%" for item in items]
                    row_percentage.append(", ".join(percentages))
                else:
                    # Check for weekend adjustments
                    adjustment = self._find_weekend_adjustment(
                        weekend_adj_lookup, payee_schedule, month_key)
                    if adjustment:
                        row_percentage.append("→Next")
                    else:
                        row_percentage.append("-")
            table.add_row(*row_percentage, style="dim")
            
            # Monthly payee totals row
            monthly_payee_totals = ["", "Payee Totals", f"${month_bill_total:.2f}"]
            for payee in sorted_payees:
                payee_monthly_total = 0.0
                payee_schedule_list = sorted(payee_schedules[payee])
                
                # Calculate total for this payee for this month only
                for payee_schedule in payee_schedule_list:
                    if payee_schedule in month_data:
                        payee_monthly_total += sum(item.required_contribution for item in month_data[payee_schedule])
                
                # Add the total for first column of this payee, empty for subsequent columns
                monthly_payee_totals.append(f"${payee_monthly_total:.2f}")
                for _ in range(len(payee_schedule_list) - 1):
                    monthly_payee_totals.append("")
            
            table.add_row(*monthly_payee_totals, style="bold blue")
            
            # Add separator between months
            if month_key != display_months[-1]:
                table.add_section()
        
        self.console.print(table)
    
    def _create_weekend_adjustment_lookup(self, weekend_adjustments: List[WeekendAdjustment]) -> Dict[str, List[WeekendAdjustment]]:
        """Create a lookup dictionary for weekend adjustments by month."""
        lookup = defaultdict(list)
        for adj in weekend_adjustments:
            month_key = adj.adjusted_date.strftime('%Y-%m')
            lookup[month_key].append(adj)
        return lookup
    
    def _find_weekend_adjustment(self, weekend_adj_lookup: Dict[str, List[WeekendAdjustment]], 
                                payee_schedule: str, month_key: str) -> WeekendAdjustment:
        """Find a weekend adjustment for a specific payee/schedule in a month."""
        payee_name = payee_schedule.split(" - ", 1)[0]
        schedule_desc = payee_schedule.split(" - ", 1)[1] if " - " in payee_schedule else ""
        
        for adjustment in weekend_adj_lookup.get(month_key, []):
            if (adjustment.payee_name == payee_name and 
                adjustment.schedule_description == schedule_desc):
                return adjustment
        return None