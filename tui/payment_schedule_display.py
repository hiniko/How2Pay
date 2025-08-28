from datetime import date
from typing import Dict, List
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from scheduler.payment_scheduler import PaymentScheduleResult, WeekendAdjustment, BillDue, PayeeAnalytics, PeriodAnalytics
from helpers.formatting import get_formatter
from helpers.payee_colors import PayeeColorGenerator


class PaymentScheduleDisplay:
    """Handles TUI display of payment schedules using Rich tables."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.formatter = get_formatter()
        self.color_generator = PayeeColorGenerator()
    
    def _get_payee_colors(self, result: PaymentScheduleResult) -> Dict[str, str]:
        """Get Rich-compatible colors for all payees in the result."""
        # Extract unique payees from schedule items
        payees = list(set(item.payee_name for item in result.schedule_items))
        payees.sort()  # Ensure consistent ordering
        
        colors = {}
        for i, payee_name in enumerate(payees):
            colors[payee_name] = self.color_generator.get_payee_color(i, 'rich')
        
        return colors
    
    def _get_payee_colors_for_all_payees(self, all_payees: List) -> Dict[str, str]:
        """Get Rich-compatible colors for all payees (including inactive ones)."""
        colors = {}
        for i, payee in enumerate(all_payees):
            colors[payee.name] = self.color_generator.get_payee_color(i, 'rich')
        return colors
    
    def display_pivot_table(self, result: PaymentScheduleResult, show_zero_contribution: bool = False, all_payees: List = None) -> None:
        """Display payment schedule as a rich pivot table."""
        # Get payee colors - include all payees from state if provided
        if all_payees:
            payee_colors = self._get_payee_colors_for_all_payees(all_payees)
        else:
            payee_colors = self._get_payee_colors(result)
        
        # Display min/max payment summary before the table
        self._display_payment_summary(result, show_zero_contribution, payee_colors)
        
        # Filter schedule items based on contribution preference
        filtered_items = result.schedule_items
        if not show_zero_contribution:
            filtered_items = [item for item in result.schedule_items if item.required_contribution > 0]
        
        # Group data by month and payee/schedule
        monthly_data = defaultdict(lambda: defaultdict(list))
        
        for item in filtered_items:
            month_key = item.payment_date.strftime('%Y-%m')
            payee_schedule_key = f"{item.payee_name} - {item.schedule_description}"
            monthly_data[month_key][payee_schedule_key].append(item)
        
        # Create lookup for weekend adjustments
        weekend_adj_lookup = self._create_weekend_adjustment_lookup(result.weekend_adjustments)
        
        # Create lookup for monthly bill totals and breakdowns
        bill_totals_lookup = {f"{bt.year}-{bt.month:02d}": bt.total_bills 
                             for bt in result.monthly_bill_totals}
        bill_breakdown_lookup = {f"{bt.year}-{bt.month:02d}": bt.bills_due 
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
        
        # Create table without internal lines - using strategic borders instead
        table = Table(
            title=f"12-Month Payment Schedule Starting {result.start_month}/{result.start_year}",
            show_lines=False
        )
        
        # Add columns - new structure: Month | Bills | Bill Amounts | Detail | Payees
        table.add_column("Month", style="bold yellow", no_wrap=True)
        table.add_column("Bills", style="bold", no_wrap=True)
        table.add_column("Bill Amounts", style="bold red", justify="right")
        table.add_column("Detail", style="dim", no_wrap=True)
        
        # Add payee columns with payee names and colors
        for payee_schedule in all_payee_schedules:
            parts = payee_schedule.split(" - ", 1)
            payee_name = parts[0]
            schedule_desc = parts[1] if len(parts) > 1 else ""
            
            # Use payee color and show both name and schedule
            payee_color = payee_colors.get(payee_name, "#ffffff")
            header_text = f"[{payee_color}]{payee_name}[/{payee_color}]\n{schedule_desc}"
            table.add_column(header_text, justify="right", style="green")
        
        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())
        
        # We want to display months_ahead bill months starting from start_month
        # The income data keys represent when income is received, which is used for the NEXT month's bills
        # So we need to find income months that correspond to our desired bill months
        display_months = []
        current_bill_month = result.start_month
        current_bill_year = result.start_year
        
        for i in range(result.months_ahead):
            # For this bill month, find the corresponding income month (previous month)
            if current_bill_month == 1:
                income_month = 12
                income_year = current_bill_year - 1
            else:
                income_month = current_bill_month - 1
                income_year = current_bill_year
            
            income_month_key = f"{income_year}-{income_month:02d}"
            
            # Only include if we have income data for this bill month
            if income_month_key in monthly_data:
                display_months.append(income_month_key)
            
            # Advance to next bill month
            current_bill_month += 1
            if current_bill_month > 12:
                current_bill_month = 1
                current_bill_year += 1
        
        # Payee names are now in column headers, so no separate header row needed
        
        for month_key in display_months:
            month_data = monthly_data[month_key]
            
            # The month_key represents when income is received. We need to find which
            # month's bills this income is responsible for. Based on the payment logic,
            # income from month X pays bills for month X+1
            current_date = date.fromisoformat(f"{month_key}-01")
            if current_date.month == 12:
                bill_month_date = date(current_date.year + 1, 1, 1)
            else:
                bill_month_date = date(current_date.year, current_date.month + 1, 1)
            bill_month_key = bill_month_date.strftime('%Y-%m')
            
            # Display both income month → bill month relationship for clarity
            income_month_display = current_date.strftime('%B')
            bill_month_display = bill_month_date.strftime('%B %Y')
            month_display = f"{income_month_display} → {bill_month_display}"
            
            # Get the bills that this income is responsible for
            bills_due = bill_breakdown_lookup.get(bill_month_key, [])
            actual_bills_total = sum(bill.amount for bill in bills_due)
            
            # Calculate row requirements for both sections
            bills_rows = len(bills_due) + 1 if bills_due else 1  # individual bills + TOTAL (or just "No bills")
            payee_detail_rows = 2  # Payment Dates + TOTAL (removed Income Amount, Percentage, and Required)
            max_rows = max(bills_rows, payee_detail_rows)
            
            # Create bills section data
            bills_section = []
            if bills_due:
                for bill in bills_due:
                    bills_section.append((bill.bill_name, self.formatter.format_currency(bill.amount)))
                bills_section.append(("TOTAL", self.formatter.format_currency(actual_bills_total)))
            else:
                bills_section.append(("No bills due", ""))
            
            # Pad bills section to max_rows
            while len(bills_section) < max_rows:
                bills_section.append(("", ""))
            
            # Create payee detail section data
            payee_details = []
            
            # 1. Payment Dates
            payee_row = ["Payment Dates"]
            for payee_schedule in all_payee_schedules:
                if payee_schedule in month_data:
                    items = month_data[payee_schedule]
                    dates = [self.formatter.format_date_short(item.payment_date) for item in items]
                    payee_row.append(", ".join(dates))
                else:
                    adjustment = self._find_weekend_adjustment(weekend_adj_lookup, payee_schedule, month_key)
                    if adjustment:
                        payee_row.append(f"→{self.formatter.format_date_short(adjustment.adjusted_date)}")
                    else:
                        payee_row.append("-")
            payee_details.append(payee_row)
            
            # 2. TOTAL row for payee section - sum by payee, not by schedule
            payee_row = ["[blue]TOTAL[/blue]"]
            payee_totals = defaultdict(float)
            
            # Calculate totals by payee name
            for payee_schedule in all_payee_schedules:
                if payee_schedule in month_data:
                    payee_name = payee_schedule.split(" - ", 1)[0]
                    items = month_data[payee_schedule]
                    payee_totals[payee_name] += sum(item.required_contribution for item in items)
            
            # Create the row with payee totals, showing total only in first column for each payee
            current_payee = ""
            for payee_schedule in all_payee_schedules:
                payee_name = payee_schedule.split(" - ", 1)[0]
                if payee_name != current_payee:
                    # First column for this payee - show the total in blue
                    if payee_name in payee_totals:
                        payee_row.append(f"[blue]{self.formatter.format_currency(payee_totals[payee_name])}[/blue]")
                    else:
                        payee_row.append("")
                    current_payee = payee_name
                else:
                    # Subsequent columns for same payee - empty to simulate merged cell
                    payee_row.append("")
            payee_details.append(payee_row)
            
            # Pad payee details to max_rows
            while len(payee_details) < max_rows:
                empty_row = [""] + [""] * len(all_payee_schedules)
                payee_details.append(empty_row)
            
            # Create the actual table rows by combining both sections
            for i in range(max_rows):
                # Month column (only show in first row)
                month_col = month_display if i == 0 else ""
                
                # Bills columns
                bill_name, bill_amount = bills_section[i]
                
                # Detail column + payee columns
                detail_and_payees = payee_details[i]
                
                # Combine all columns: Month | Bills | Bill Amounts | Detail | Payees...
                row = [month_col, bill_name, bill_amount] + detail_and_payees
                
                # Apply styling for specific rows
                style = None
                if bill_name == "TOTAL":
                    style = "bold blue"
                elif "[blue]TOTAL[/blue]" in str(detail_and_payees[0]) and bill_name == "":
                    # TOTAL row for payee section - already has blue markup in the detail column
                    style = "bold"
                    
                table.add_row(*row, style=style)
            
            # Add separator between months - using section for strategic borders
            if month_key != display_months[-1]:
                table.add_section()
        
        self.console.print(table)
    
    def _display_payment_summary(self, result: PaymentScheduleResult, show_zero_contribution: bool, payee_colors: Dict[str, str]) -> None:
        """Display comprehensive payment analytics."""
        analytics = result.analytics
        
        # Filter payees based on contribution preference
        displayed_payees = analytics.payee_analytics
        if not show_zero_contribution:
            displayed_payees = {name: payee_analytics for name, payee_analytics in analytics.payee_analytics.items() 
                               if payee_analytics.max_amount > 0}
        
        if not displayed_payees:
            return
        
        # Build comprehensive analytics display
        summary_lines = []
        
        # Period Overview Section
        summary_lines.append("[bold blue]📊 PROJECTION ANALYTICS[/bold blue]\n")
        
        # Period totals and averages
        total_str = self.formatter.format_currency(analytics.total_bills_required)
        avg_str = self.formatter.format_currency(analytics.average_monthly_requirement)
        summary_lines.append(f"[bold]Period Overview ({result.months_ahead} months):[/bold]")
        summary_lines.append(f"  • Total Bills Required: {total_str}")
        summary_lines.append(f"  • Average Monthly Cost: {avg_str}")
        
        # Monthly variation
        if analytics.min_monthly_total != analytics.max_monthly_total:
            min_monthly_str = self.formatter.format_currency(analytics.min_monthly_total)
            max_monthly_str = self.formatter.format_currency(analytics.max_monthly_total)
            min_months_str = ", ".join(analytics.min_months)
            max_months_str = ", ".join(analytics.max_months)
            
            summary_lines.append(f"  • Monthly Range: {min_monthly_str} - {max_monthly_str}")
            summary_lines.append(f"    - Lowest: {min_months_str}")
            summary_lines.append(f"    - Highest: {max_months_str}")
        else:
            consistent_str = self.formatter.format_currency(analytics.min_monthly_total)
            summary_lines.append(f"  • Monthly Cost: {consistent_str} (consistent)")
        
        summary_lines.append("")  # Spacing
        
        # Payee Breakdown Section
        summary_lines.append("[bold]👥 PAYEE BREAKDOWN:[/bold]")
        
        for payee_name in sorted(displayed_payees.keys()):
            payee_analytics = displayed_payees[payee_name]
            color = payee_colors.get(payee_name, "#ffffff")
            
            # Payee header with name
            summary_lines.append(f"[bold][{color}]{payee_name}[/{color}][/bold]:")
            
            # Payment range
            min_amount_str = self.formatter.format_currency(payee_analytics.min_amount)
            max_amount_str = self.formatter.format_currency(payee_analytics.max_amount)
            avg_amount_str = self.formatter.format_currency(payee_analytics.average_amount)
            total_amount_str = self.formatter.format_currency(payee_analytics.total_amount)
            
            if payee_analytics.is_consistent:
                summary_lines.append(f"  • Payment: {max_amount_str}/month (consistent)")
            else:
                min_months_str = ", ".join(payee_analytics.min_months)
                max_months_str = ", ".join(payee_analytics.max_months)
                summary_lines.append(f"  • Range: {min_amount_str} - {max_amount_str}")
                summary_lines.append(f"    - Min: {min_months_str}")
                summary_lines.append(f"    - Max: {max_months_str}")
            
            summary_lines.append(f"  • Average: {avg_amount_str}/month")
            summary_lines.append(f"  • Total: {total_amount_str} over {result.months_ahead} months")
            summary_lines.append("")  # Spacing between payees
        
        # Display in a comprehensive panel
        summary_text = "\n".join(summary_lines)
        panel = Panel(summary_text, title="💰 Payment Planning & Analytics", border_style="blue", padding=(1, 2))
        self.console.print(panel)
        self.console.print()  # Add spacing before table
    
    def _display_payee_payment_summary(self, result: PaymentScheduleResult, payee_name: str, payee_colors: Dict[str, str]) -> None:
        """Display comprehensive payment analytics for a specific payee."""
        analytics = result.analytics
        
        # Get analytics for this specific payee
        payee_analytics = analytics.payee_analytics.get(payee_name)
        if not payee_analytics or payee_analytics.max_amount <= 0:
            return
        
        # Build comprehensive payee analytics
        color = payee_colors.get(payee_name, "#ffffff")
        summary_lines = []
        
        # Header
        summary_lines.append(f"[bold blue]📊 ANALYTICS for [{color}]{payee_name.upper()}[/{color}][/bold blue]\n")
        
        # Individual payee stats
        min_amount_str = self.formatter.format_currency(payee_analytics.min_amount)
        max_amount_str = self.formatter.format_currency(payee_analytics.max_amount)
        avg_amount_str = self.formatter.format_currency(payee_analytics.average_amount)
        total_amount_str = self.formatter.format_currency(payee_analytics.total_amount)
        
        # Payment Analysis
        summary_lines.append("[bold]💰 Payment Analysis:[/bold]")
        if payee_analytics.is_consistent:
            summary_lines.append(f"  • Monthly Payment: {max_amount_str} (consistent)")
        else:
            min_months_str = ", ".join(payee_analytics.min_months)
            max_months_str = ", ".join(payee_analytics.max_months)
            summary_lines.append(f"  • Payment Range: {min_amount_str} - {max_amount_str}")
            summary_lines.append(f"    - Minimum: {min_months_str}")
            summary_lines.append(f"    - Maximum: {max_months_str}")
        
        summary_lines.append(f"  • Average Monthly: {avg_amount_str}")
        summary_lines.append("")
        
        # Period totals
        summary_lines.append(f"[bold]📊 Period Summary ({result.months_ahead} months):[/bold]")
        summary_lines.append(f"  • Total Contribution: {total_amount_str}")
        
        # Calculate percentage of total household costs
        if analytics.total_bills_required > 0:
            percentage = (payee_analytics.total_amount / analytics.total_bills_required) * 100
            summary_lines.append(f"  • Share of Total Bills: {percentage:.1f}%")
        
        # Monthly comparison to household average
        household_avg_str = self.formatter.format_currency(analytics.average_monthly_requirement)
        summary_lines.append(f"  • vs Household Average: {avg_amount_str} vs {household_avg_str}")
        
        # Display in a comprehensive panel
        summary_text = "\n".join(summary_lines)
        panel = Panel(summary_text, title=f"💰 {payee_name} - Payment Planning & Analytics", 
                     border_style="blue", padding=(1, 2))
        self.console.print(panel)
        self.console.print()  # Add spacing before table
    
    def display_payee_schedule(self, result: PaymentScheduleResult, payee_name: str, show_zero_contribution: bool = False) -> None:
        """Display payment schedule for a specific payee only."""
        # Get payee colors
        payee_colors = self._get_payee_colors(result)
        
        # Filter schedule items for this payee
        payee_items = [item for item in result.schedule_items if item.payee_name == payee_name]
        
        # Further filter by contribution if requested
        if not show_zero_contribution:
            payee_items = [item for item in payee_items if item.required_contribution > 0]
        
        # Display payment summary for this specific payee
        self._display_payee_payment_summary(result, payee_name, payee_colors)
        
        if not payee_items:
            self.console.print(f"[yellow]No schedule items found for payee '{payee_name}'[/yellow]")
            return
        
        # Group data by month for this payee
        monthly_data = defaultdict(lambda: defaultdict(list))
        
        for item in payee_items:
            month_key = item.payment_date.strftime('%Y-%m')
            schedule_key = item.schedule_description
            monthly_data[month_key][schedule_key].append(item)
        
        # Create lookup for weekend adjustments
        weekend_adj_lookup = self._create_weekend_adjustment_lookup(result.weekend_adjustments)
        
        # Create lookup for monthly bill totals filtered for this payee
        bill_totals_lookup = {f"{bt.year}-{bt.month:02d}": bt.total_bills 
                             for bt in result.monthly_bill_totals}
        bill_breakdown_lookup = {f"{bt.year}-{bt.month:02d}": bt.bills_due 
                                for bt in result.monthly_bill_totals}
        
        # Get all unique schedules for this payee
        all_schedules = set()
        for month_data in monthly_data.values():
            all_schedules.update(month_data.keys())
        all_schedules = sorted(all_schedules)
        
        # Create table with colored payee name
        payee_color = payee_colors.get(payee_name, "#ffffff")
        table = Table(
            title=f"12-Month Payment Schedule for [bold {payee_color}]{payee_name}[/bold {payee_color}] Starting {result.start_month}/{result.start_year}",
            show_lines=False
        )
        
        # Add columns: Month | Bills | Bill Amounts | Detail | Income Streams
        table.add_column("Month", style="bold yellow", no_wrap=True)
        table.add_column("Bills (Payee Share)", style="bold", no_wrap=True)
        table.add_column("Payee Amount", style="bold red", justify="right")
        table.add_column("Detail", style="dim", no_wrap=True)
        
        # Add income stream columns with payee name
        for schedule in all_schedules:
            # Since this is payee-specific, show the payee name with their color
            payee_color = payee_colors.get(payee_name, "#ffffff")
            header_text = f"[{payee_color}]{payee_name}[/{payee_color}]\n{schedule}"
            table.add_column(header_text, justify="right", style="green")
        
        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())
        
        # We want to display months_ahead bill months starting from start_month
        # The income data keys represent when income is received, which is used for the NEXT month's bills
        # So we need to find income months that correspond to our desired bill months
        display_months = []
        current_bill_month = result.start_month
        current_bill_year = result.start_year
        
        for i in range(result.months_ahead):
            # For this bill month, find the corresponding income month (previous month)
            if current_bill_month == 1:
                income_month = 12
                income_year = current_bill_year - 1
            else:
                income_month = current_bill_month - 1
                income_year = current_bill_year
            
            income_month_key = f"{income_year}-{income_month:02d}"
            
            # Only include if we have income data for this bill month
            if income_month_key in monthly_data:
                display_months.append(income_month_key)
            
            # Advance to next bill month
            current_bill_month += 1
            if current_bill_month > 12:
                current_bill_month = 1
                current_bill_year += 1
        
        for month_key in display_months:
            month_data = monthly_data[month_key]
            
            # Get bills for this month that this payee contributes to
            current_date = date.fromisoformat(f"{month_key}-01")
            if current_date.month == 12:
                bill_month_date = date(current_date.year + 1, 1, 1)
            else:
                bill_month_date = date(current_date.year, current_date.month + 1, 1)
            bill_month_key = bill_month_date.strftime('%Y-%m')
            
            # Display both income month → bill month relationship for clarity
            income_month_display = current_date.strftime('%B')
            bill_month_display = bill_month_date.strftime('%B %Y')
            month_display = f"{income_month_display} → {bill_month_display}"
            
            # Filter bills to only those this payee contributes to
            all_bills_due = bill_breakdown_lookup.get(bill_month_key, [])
            payee_bills = []
            payee_total = 0.0
            
            # Load state to get bill assignments
            from helpers.state_ops import load_state
            state = load_state()
            
            for bill_due in all_bills_due:
                # Find the bill in the state to check payee assignment
                for bill in state.bills:
                    if bill.name == bill_due.bill_name:
                        # Get active payees for this month
                        bill_month_date_obj = date.fromisoformat(f"{bill_month_key}-01")
                        active_payees = [p for p in state.payees if p.is_active_for_month(bill_month_date_obj.year, bill_month_date_obj.month)]
                        
                        # Calculate payee's share using the new system
                        payee_percentage = bill.get_payee_percentage(payee_name, active_payees)
                        if payee_percentage > 0:
                            payee_amount = bill_due.amount * (payee_percentage / 100.0)
                            payee_bills.append((bill_due.bill_name, payee_amount))
                            payee_total += payee_amount
                        break
            
            # Calculate row requirements
            bills_rows = len(payee_bills) + 1 if payee_bills else 1  # individual bills + TOTAL
            income_detail_rows = 2  # Payment Dates + TOTAL (removed Income Amount, Percentage, and Required)
            max_rows = max(bills_rows, income_detail_rows)
            
            # Create bills section data
            bills_section = []
            if payee_bills:
                for bill_name, payee_amount in payee_bills:
                    bills_section.append((bill_name, self.formatter.format_currency(payee_amount)))
                bills_section.append(("TOTAL", self.formatter.format_currency(payee_total)))
            else:
                bills_section.append(("No bills due", ""))
            
            # Pad bills section to max_rows
            while len(bills_section) < max_rows:
                bills_section.append(("", ""))
            
            # Create income detail section data
            income_details = []
            
            # 1. Payment Dates
            income_row = ["Payment Dates"]
            for schedule in all_schedules:
                if schedule in month_data:
                    items = month_data[schedule]
                    dates = [self.formatter.format_date_short(item.payment_date) for item in items]
                    income_row.append(", ".join(dates))
                else:
                    adjustment = self._find_weekend_adjustment(weekend_adj_lookup, f"{payee_name} - {schedule}", month_key)
                    if adjustment:
                        income_row.append(f"→{self.formatter.format_date_short(adjustment.adjusted_date)}")
                    else:
                        income_row.append("-")
            income_details.append(income_row)
            
            # 2. TOTAL row
            income_row = ["[blue]TOTAL[/blue]"]
            total_required = 0.0
            for schedule in all_schedules:
                if schedule in month_data:
                    items = month_data[schedule]
                    schedule_total = sum(item.required_contribution for item in items)
                    total_required += schedule_total
            
            # Show total only in first column, empty for others
            for i, schedule in enumerate(all_schedules):
                if i == 0:
                    income_row.append(f"[blue]{self.formatter.format_currency(total_required)}[/blue]")
                else:
                    income_row.append("")
            
            income_details.append(income_row)
            
            # Pad income details to max_rows
            while len(income_details) < max_rows:
                empty_row = [""] + [""] * len(all_schedules)
                income_details.append(empty_row)
            
            # Create the actual table rows by combining both sections
            for i in range(max_rows):
                # Month column (only show in first row)
                month_col = month_display if i == 0 else ""
                
                # Bills columns
                bill_name, bill_amount = bills_section[i]
                
                # Detail column + income columns
                detail_and_income = income_details[i]
                
                # Combine all columns: Month | Bills | Bill Amounts | Detail | Income...
                row = [month_col, bill_name, bill_amount] + detail_and_income
                
                # Apply styling for specific rows
                style = None
                if bill_name == "TOTAL":
                    style = "bold blue"
                elif "[blue]TOTAL[/blue]" in str(detail_and_income[0]) and bill_name == "":
                    style = "bold"
                    
                table.add_row(*row, style=style)
            
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