"""Professional HTML table generation for payment schedules."""

from datetime import date
from typing import Dict, List, Optional
from collections import defaultdict
from scheduler.payment_scheduler import PaymentScheduleResult, PayeeAnalytics, PeriodAnalytics
from helpers.formatting import get_formatter
from helpers.payee_colors import PayeeColorGenerator


class ProfessionalHtmlGenerator:
    """Generates professional HTML tables from payment schedule data."""
    
    def __init__(self):
        self.formatter = get_formatter()
        self.color_generator = PayeeColorGenerator()
    
    def _get_payee_colors(self, result: PaymentScheduleResult) -> Dict[str, str]:
        """Get colors for all payees in the result."""
        # Extract unique payees from schedule items
        payees = list(set(item.payee_name for item in result.schedule_items))
        payees.sort()  # Ensure consistent ordering
        
        colors = {}
        for i, payee_name in enumerate(payees):
            colors[payee_name] = self.color_generator.get_payee_color(i, 'hex')
        
        return colors
    
    def generate_payee_schedule_html(self, result: PaymentScheduleResult, payee_name: str, show_zero_contribution: bool = False) -> str:
        """Generate professional HTML for payee-specific schedule."""
        
        # Filter schedule items for this payee
        payee_items = [item for item in result.schedule_items if item.payee_name == payee_name]
        
        # Further filter by contribution if requested
        if not show_zero_contribution:
            payee_items = [item for item in payee_items if item.required_contribution > 0]
        
        if not payee_items:
            return self._generate_no_data_html(f"No schedule items found for payee '{payee_name}'")
        
        # Group data by month for this payee
        monthly_data = defaultdict(lambda: defaultdict(list))
        for item in payee_items:
            month_key = item.payment_date.strftime('%Y-%m')
            schedule_key = item.schedule_description
            monthly_data[month_key][schedule_key].append(item)
        
        # Get bill breakdown
        bill_breakdown_lookup = {f"{bt.year}-{bt.month:02d}": bt.bills_due 
                               for bt in result.monthly_bill_totals}
        
        # Get all unique schedules for this payee
        all_schedules = set()
        for month_data in monthly_data.values():
            all_schedules.update(month_data.keys())
        all_schedules = sorted(all_schedules)
        
        # Generate payee-specific payment summary
        summary_html = self._generate_payee_payment_summary_html(result, payee_name)
        
        # Generate HTML
        html = self._get_base_html_template(
            title=f"{result.months_ahead}-Month Payment Schedule for {payee_name}",
            subtitle=f"Starting {result.start_month}/{result.start_year}",
            result=result
        )
        
        # Generate table
        table_html = self._generate_payee_table(
            monthly_data, bill_breakdown_lookup, payee_name, all_schedules, result
        )
        
        # Combine summary and table
        content_html = summary_html + table_html
        
        return html.replace("PLACEHOLDER_CONTENT", content_html)
    
    def generate_household_schedule_html(self, result: PaymentScheduleResult, show_zero_contribution: bool = False) -> str:
        """Generate professional HTML for full household schedule."""
        
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
        
        # Get bill breakdown
        bill_breakdown_lookup = {f"{bt.year}-{bt.month:02d}": bt.bills_due 
                               for bt in result.monthly_bill_totals}
        
        # Get all unique payee-schedule combinations
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
        
        html = self._get_base_html_template(
            title=f"{result.months_ahead}-Month Cash Flow Projection", 
            subtitle=f"Starting {result.start_month}/{result.start_year}",
            result=result
        )
        
        # Generate payment summary
        summary_html = self._generate_payment_summary_html(result, show_zero_contribution)
        
        # Generate table
        table_html = self._generate_household_table(
            monthly_data, bill_breakdown_lookup, payee_schedules, all_payee_schedules, result
        )
        
        # Combine summary and table
        content_html = summary_html + table_html
        
        return html.replace("PLACEHOLDER_CONTENT", content_html)
    
    def _generate_payee_table(self, monthly_data: Dict, bill_breakdown_lookup: Dict, 
                             payee_name: str, all_schedules: List[str], result: PaymentScheduleResult) -> str:
        """Generate HTML table for payee-specific schedule."""
        
        # Sort months chronologically and filter to only include months within our projection range
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
        
        # Generate separate sections for each month
        sections_html = ""
        
        for month_idx, month_key in enumerate(display_months):
            section_class = "month-section" if month_idx > 0 else "month-section first-month"
            sections_html += f'<div class="{section_class}">'
            
            # Table header for each section
            header = '<table class="schedule-table"><thead><tr class="month-header-row">'
            header += '<th rowspan="2" class="month-header">Month</th>'
            header += '<th rowspan="2" class="bills-header">Bills (Your Share)</th>'
            header += '<th rowspan="2" class="amount-header">Amount</th>'
            header += '<th rowspan="2" class="detail-header">Detail</th>'
            
            # Income stream headers
            if all_schedules:
                header += f'<th colspan="{len(all_schedules)}" class="income-header">Income Streams</th>'
            header += '</tr><tr>'
            
            for schedule in all_schedules:
                header += f'<th class="stream-header">{schedule}</th>'
            header += '</tr></thead><tbody>'
            
            # Generate body for this month only
            month_body = self._generate_payee_month_body(
                month_key, monthly_data, bill_breakdown_lookup, payee_name, all_schedules, result
            )
            
            sections_html += header + month_body + '</tbody></table></div>'
        
        return sections_html
    
    def _generate_payee_month_body(self, month_key: str, monthly_data: Dict, bill_breakdown_lookup: Dict,
                                  payee_name: str, all_schedules: List[str], result: PaymentScheduleResult) -> str:
        """Generate HTML table body for a single month in payee-specific schedule."""
        
        month_data = monthly_data[month_key]
        
        # month_key is the INCOME month, but we want to display the BILL month (next month)
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
        
        from helpers.state_ops import load_state
        state = load_state()
        
        for bill_due in all_bills_due:
            for bill in state.bills:
                if bill.name == bill_due.bill_name:
                    if bill.has_custom_shares():
                        payee_percentage = bill.get_payee_percentage(payee_name)
                        if payee_percentage > 0:
                            payee_amount = bill_due.amount * (payee_percentage / 100.0)
                            payee_bills.append((bill_due.bill_name, payee_amount))
                            payee_total += payee_amount
                    else:
                        # Equal split among all payees
                        num_payees = len(state.payees)
                        if num_payees > 0:
                            payee_amount = bill_due.amount / num_payees
                            payee_bills.append((bill_due.bill_name, payee_amount))
                            payee_total += payee_amount
                    break
        
        # Calculate rows needed
        max_rows = max(len(payee_bills) + 1, 2)  # bills + TOTAL, or 2 detail rows minimum
        
        # Generate rows
        body = ""
        for row_idx in range(max_rows):
            body += '<tr>'
            
            # Month column (only in first row)
            if row_idx == 0:
                body += f'<td rowspan="{max_rows}" class="month-cell">{month_display}</td>'
            
            # Bill column
            if row_idx < len(payee_bills):
                bill_name, amount = payee_bills[row_idx]
                body += f'<td class="bill-cell">{bill_name}</td>'
                body += f'<td class="amount-cell">{self.formatter.format_currency(amount)}</td>'
            elif row_idx == len(payee_bills) and payee_bills:
                body += '<td class="total-cell"><strong>TOTAL</strong></td>'
                body += f'<td class="total-amount-cell"><strong>{self.formatter.format_currency(payee_total)}</strong></td>'
            else:
                body += '<td class="empty-cell"></td><td class="empty-cell"></td>'
            
            # Detail column
            detail_labels = ["Payment Dates", "TOTAL"]
            if row_idx < len(detail_labels):
                body += f'<td class="detail-cell"><strong>{detail_labels[row_idx]}</strong></td>'
            else:
                body += '<td class="empty-cell"></td>'
            
            # Income stream columns
            for schedule in all_schedules:
                if row_idx == 0:  # Payment Dates
                    if schedule in month_data:
                        items = month_data[schedule]
                        dates = [self.formatter.format_date_short(item.payment_date) for item in items]
                        body += f'<td class="date-cell">{", ".join(dates)}</td>'
                    else:
                        body += '<td class="empty-cell">-</td>'
                elif row_idx == 1:  # TOTAL
                    if schedule in month_data:
                        items = month_data[schedule]
                        total_required = sum(item.required_contribution for item in items)
                        body += f'<td class="income-total-cell"><strong>{self.formatter.format_currency(total_required)}</strong></td>'
                    else:
                        body += '<td class="empty-cell"></td>'
                else:
                    body += '<td class="empty-cell"></td>'
            
            body += '</tr>'
        
        return body
    
    def _generate_household_table(self, monthly_data: Dict, bill_breakdown_lookup: Dict,
                                payee_schedules: Dict, all_payee_schedules: List[str], result: PaymentScheduleResult) -> str:
        """Generate HTML table for household schedule."""
        
        # Sort months chronologically and filter to only include months within our projection range
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
        
        # Generate separate sections for each month
        sections_html = ""
        
        for month_idx, month_key in enumerate(display_months):
            section_class = "month-section" if month_idx > 0 else "month-section first-month"
            sections_html += f'<div class="{section_class}">'
            
            # Table header for each section
            header = '<table class="schedule-table"><thead><tr class="month-header-row">'
            header += '<th rowspan="2" class="month-header">Month</th>'
            header += '<th rowspan="2" class="bills-header">Bills</th>'
            header += '<th rowspan="2" class="amount-header">Amount</th>'
            header += '<th rowspan="2" class="detail-header">Detail</th>'
            
            # Income stream headers by payee
            if all_payee_schedules:
                header += f'<th colspan="{len(all_payee_schedules)}" class="income-header">Income Streams</th>'
            header += '</tr><tr>'
            
            for payee_schedule in all_payee_schedules:
                # Extract payee name and schedule name
                payee_name = payee_schedule.split(" - ", 1)[0]
                schedule_name = payee_schedule.split(" - ", 1)[1] if " - " in payee_schedule else payee_schedule
                
                # Add payee color class to header and show both payee and schedule
                css_class = payee_name.lower().replace(' ', '-').replace('.', '')
                header += f'<th class="stream-header payee-{css_class}-header">{payee_name}<br><small>{schedule_name}</small></th>'
            header += '</tr></thead><tbody>'
            
            # Generate body for this month only
            month_body = self._generate_household_month_body(
                month_key, monthly_data, bill_breakdown_lookup, all_payee_schedules, result
            )
            
            sections_html += header + month_body + '</tbody></table></div>'
        
        return sections_html
    
    def _generate_household_month_body(self, month_key: str, monthly_data: Dict, bill_breakdown_lookup: Dict,
                                      all_payee_schedules: List[str], result: PaymentScheduleResult) -> str:
        """Generate HTML table body for a single month in household schedule."""
        
        month_data = monthly_data[month_key]
        
        # month_key is the INCOME month, but we want to display the BILL month (next month)
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
        
        all_bills_due = bill_breakdown_lookup.get(bill_month_key, [])
        
        # Calculate rows needed
        max_rows = max(len(all_bills_due) + 1, 2)  # bills + TOTAL, or 2 detail rows minimum
        
        # Generate rows
        body = ""
        for row_idx in range(max_rows):
            body += '<tr>'
            
            # Month column (only in first row)
            if row_idx == 0:
                body += f'<td rowspan="{max_rows}" class="month-cell">{month_display}</td>'
            
            # Bill column
            if row_idx < len(all_bills_due):
                bill_due = all_bills_due[row_idx]
                body += f'<td class="bill-cell">{bill_due.bill_name}</td>'
                body += f'<td class="amount-cell">{self.formatter.format_currency(bill_due.amount)}</td>'
            elif row_idx == len(all_bills_due) and all_bills_due:
                total_amount = sum(bd.amount for bd in all_bills_due)
                body += '<td class="total-cell"><strong>TOTAL</strong></td>'
                body += f'<td class="total-amount-cell"><strong>{self.formatter.format_currency(total_amount)}</strong></td>'
            else:
                body += '<td class="empty-cell"></td><td class="empty-cell"></td>'
            
            # Detail column
            detail_labels = ["Payment Dates", "TOTAL"]
            if row_idx < len(detail_labels):
                body += f'<td class="detail-cell"><strong>{detail_labels[row_idx]}</strong></td>'
            else:
                body += '<td class="empty-cell"></td>'
            
            # Income stream columns for each payee
            for payee_schedule_key in all_payee_schedules:
                if row_idx == 0:  # Payment Dates
                    if payee_schedule_key in month_data:
                        items = month_data[payee_schedule_key]
                        dates = [self.formatter.format_date_short(item.payment_date) for item in items]
                        body += f'<td class="date-cell">{", ".join(dates)}</td>'
                    else:
                        body += '<td class="empty-cell">-</td>'
                elif row_idx == 1:  # TOTAL
                    if payee_schedule_key in month_data:
                        items = month_data[payee_schedule_key]
                        total_required = sum(item.required_contribution for item in items)
                        body += f'<td class="income-total-cell"><strong>{self.formatter.format_currency(total_required)}</strong></td>'
                    else:
                        body += '<td class="empty-cell"></td>'
                else:
                    body += '<td class="empty-cell"></td>'
            
            body += '</tr>'
        
        return body
    
    def _generate_no_data_html(self, message: str) -> str:
        """Generate HTML for no data scenarios."""
        html = self._get_base_html_template("No Data", "")
        content = f'<div class="no-data"><h3>⚠️ {message}</h3></div>'
        return html.replace("PLACEHOLDER_CONTENT", content)
    
    def _generate_payment_summary_html(self, result: PaymentScheduleResult, show_zero_contribution: bool = False) -> str:
        """Generate comprehensive HTML analytics with improved PDF layout."""
        analytics = result.analytics
        
        # Filter payees based on contribution preference
        displayed_payees = analytics.payee_analytics
        if not show_zero_contribution:
            displayed_payees = {name: payee_analytics for name, payee_analytics in analytics.payee_analytics.items() 
                               if payee_analytics.max_amount > 0}
        
        if not displayed_payees:
            return ""
        
        # Get payee colors
        payee_colors = self._get_payee_colors(result)
        
        html_parts = []
        
        # Combined Introduction & Period Overview (Page 1)
        html_parts.append('<div class="intro-period-page">')
        
        # Compact Introduction Section
        html_parts.append('<div class="intro-compact">')
        html_parts.append('<h1 class="intro-title-compact">📊 Payment Planning Guide</h1>')
        html_parts.append('<div class="intro-content-compact">')
        html_parts.append('<p class="intro-desc">This report shows your household\'s financial projections with period overview and individual breakdowns.</p>')
        html_parts.append('<div class="intro-sections-compact">')
        html_parts.append('<div class="intro-section-compact">')
        html_parts.append('<strong>📈 Period Overview:</strong> Total costs, monthly averages, and payment ranges.')
        html_parts.append('</div>')
        html_parts.append('<div class="intro-section-compact">')
        html_parts.append('<strong>👥 Individual Breakdown:</strong> Each person\'s payment details and share of bills.')
        html_parts.append('</div>')
        html_parts.append('</div>')
        html_parts.append('<div class="intro-tip-compact">')
        html_parts.append('<strong>💡 Tip:</strong> Use monthly ranges to plan savings - save during low-cost months for high-cost periods.')
        html_parts.append('</div>')
        html_parts.append('</div>')
        html_parts.append('</div>')
        
        # Period Overview Section (Same Page)
        html_parts.append('<div class="period-section-compact">')
        html_parts.append('<h2 class="section-title-compact">📈 Period Overview</h2>')
        
        # Key metrics in a 2x2 grid
        total_str = self.formatter.format_currency(analytics.total_bills_required)
        avg_str = self.formatter.format_currency(analytics.average_monthly_requirement)
        
        html_parts.append('<div class="overview-metrics-compact">')
        html_parts.append(f'<div class="metric-card-compact primary">')
        html_parts.append(f'<div class="metric-icon-compact">💰</div>')
        html_parts.append(f'<div class="metric-label-compact">Total Bills ({result.months_ahead}mo)</div>')
        html_parts.append(f'<div class="metric-value-compact">{total_str}</div>')
        html_parts.append('</div>')
        
        html_parts.append(f'<div class="metric-card-compact primary">')
        html_parts.append(f'<div class="metric-icon-compact">📊</div>')
        html_parts.append(f'<div class="metric-label-compact">Average Monthly</div>')
        html_parts.append(f'<div class="metric-value-compact">{avg_str}</div>')
        html_parts.append('</div>')
        
        # Monthly range metrics
        if analytics.min_monthly_total != analytics.max_monthly_total:
            min_monthly_str = self.formatter.format_currency(analytics.min_monthly_total)
            max_monthly_str = self.formatter.format_currency(analytics.max_monthly_total)
            min_months_str = ", ".join(analytics.min_months)
            max_months_str = ", ".join(analytics.max_months)
            
            html_parts.append(f'<div class="metric-card-compact range">')
            html_parts.append(f'<div class="metric-icon-compact">📈</div>')
            html_parts.append(f'<div class="metric-label-compact">Monthly Range</div>')
            html_parts.append(f'<div class="metric-value-compact">{min_monthly_str} - {max_monthly_str}</div>')
            html_parts.append(f'<div class="metric-detail-compact">Low: {min_months_str}</div>')
            html_parts.append(f'<div class="metric-detail-compact">High: {max_months_str}</div>')
            html_parts.append('</div>')
        else:
            consistent_str = self.formatter.format_currency(analytics.min_monthly_total)
            html_parts.append(f'<div class="metric-card-compact consistent">')
            html_parts.append(f'<div class="metric-icon-compact">✓</div>')
            html_parts.append(f'<div class="metric-label-compact">Monthly Cost</div>')
            html_parts.append(f'<div class="metric-value-compact">{consistent_str}</div>')
            html_parts.append(f'<div class="metric-detail-compact">Consistent</div>')
            html_parts.append('</div>')
        
        html_parts.append('</div>') # Close overview-metrics-compact
        html_parts.append('</div>') # Close period-section-compact
        html_parts.append('</div>') # Close intro-period-page
        
        # Payee Breakdown Section (Page 3+)
        html_parts.append('<div class="payee-page">')
        html_parts.append('<h2 class="page-title">👥 Individual Breakdown</h2>')
        html_parts.append('<div class="payee-grid">')
        
        for payee_name in sorted(displayed_payees.keys()):
            payee_analytics = displayed_payees[payee_name]
            color = payee_colors.get(payee_name, "#333333")
            
            html_parts.append(f'<div class="payee-card-compact" style="border-top: 4px solid {color};">')
            html_parts.append(f'<h4 class="payee-name-compact" style="color: {color};">{payee_name}</h4>')
            
            min_amount_str = self.formatter.format_currency(payee_analytics.min_amount)
            max_amount_str = self.formatter.format_currency(payee_analytics.max_amount)
            avg_amount_str = self.formatter.format_currency(payee_analytics.average_amount)
            total_amount_str = self.formatter.format_currency(payee_analytics.total_amount)
            
            # Payment range
            if payee_analytics.is_consistent:
                html_parts.append('<div class="metric-compact">')
                html_parts.append('<span class="label-compact">Monthly Payment:</span>')
                html_parts.append(f'<span class="value-compact">{max_amount_str}</span>')
                html_parts.append('<div class="detail-compact">Consistent</div>')
                html_parts.append('</div>')
            else:
                min_months_str = ", ".join(payee_analytics.min_months)
                max_months_str = ", ".join(payee_analytics.max_months)
                html_parts.append('<div class="metric-compact">')
                html_parts.append('<span class="label-compact">Range:</span>')
                html_parts.append(f'<span class="value-compact">{min_amount_str} - {max_amount_str}</span>')
                html_parts.append(f'<div class="detail-compact">Min: {min_months_str}</div>')
                html_parts.append(f'<div class="detail-compact">Max: {max_months_str}</div>')
                html_parts.append('</div>')
            
            # Average and total
            html_parts.append('<div class="metric-compact">')
            html_parts.append('<span class="label-compact">Average Monthly:</span>')
            html_parts.append(f'<span class="value-compact">{avg_amount_str}</span>')
            html_parts.append('</div>')
            
            html_parts.append('<div class="metric-compact">')
            html_parts.append(f'<span class="label-compact">Total ({result.months_ahead}mo):</span>')
            html_parts.append(f'<span class="value-compact">{total_amount_str}</span>')
            html_parts.append('</div>')
            
            # Percentage of total
            if analytics.total_bills_required > 0:
                percentage = (payee_analytics.total_amount / analytics.total_bills_required) * 100
                html_parts.append('<div class="metric-compact">')
                html_parts.append('<span class="label-compact">Share of Bills:</span>')
                html_parts.append(f'<span class="value-compact highlight">{percentage:.1f}%</span>')
                html_parts.append('</div>')
            
            html_parts.append('</div>') # Close payee-card-compact
        
        html_parts.append('</div>') # Close payee-grid
        html_parts.append('</div>') # Close payee-page
        
        return '\n'.join(html_parts)
    
    def _get_payee_colors_from_items(self, items: List) -> Dict[str, str]:
        """Get payee colors from schedule items."""
        payees = list(set(item.payee_name for item in items))
        payees.sort()
        
        colors = {}
        for i, payee_name in enumerate(payees):
            colors[payee_name] = self.color_generator.get_payee_color(i, 'hex')
        
        return colors
    
    def _generate_payee_payment_summary_html(self, result: PaymentScheduleResult, payee_name: str) -> str:
        """Generate comprehensive HTML analytics for a specific payee."""
        analytics = result.analytics
        
        # Get analytics for this specific payee
        payee_analytics = analytics.payee_analytics.get(payee_name)
        if not payee_analytics or payee_analytics.max_amount <= 0:
            return ""
        
        # Get payee color
        payee_colors = self._get_payee_colors(result)
        color = payee_colors.get(payee_name, "#333333")
        
        # Generate comprehensive HTML analytics for payee
        html_parts = []
        html_parts.append('<div class="analytics-container payee-analytics">')
        html_parts.append(f'<h2 class="analytics-title" style="color: {color};">📊 Analytics for {payee_name.upper()}</h2>')
        
        # Payment Analysis Section
        html_parts.append('<div class="payment-analysis">')
        html_parts.append('<h3 class="section-title">💰 Payment Analysis</h3>')
        html_parts.append('<div class="analysis-grid">')
        
        min_amount_str = self.formatter.format_currency(payee_analytics.min_amount)
        max_amount_str = self.formatter.format_currency(payee_analytics.max_amount)
        avg_amount_str = self.formatter.format_currency(payee_analytics.average_amount)
        total_amount_str = self.formatter.format_currency(payee_analytics.total_amount)
        
        # Payment range card
        html_parts.append(f'<div class="metric-card primary-card" style="border-top: 3px solid {color};">')
        if payee_analytics.is_consistent:
            html_parts.append(f'<div class="metric-label">Monthly Payment</div>')
            html_parts.append(f'<div class="metric-value">{max_amount_str}</div>')
            html_parts.append(f'<div class="metric-detail">Consistent across all months</div>')
        else:
            min_months_str = ", ".join(payee_analytics.min_months)
            max_months_str = ", ".join(payee_analytics.max_months)
            html_parts.append(f'<div class="metric-label">Payment Range</div>')
            html_parts.append(f'<div class="metric-value">{min_amount_str} - {max_amount_str}</div>')
            html_parts.append(f'<div class="metric-detail">Min: {min_months_str}</div>')
            html_parts.append(f'<div class="metric-detail">Max: {max_months_str}</div>')
        html_parts.append('</div>')
        
        # Average monthly
        html_parts.append(f'<div class="metric-card">')
        html_parts.append(f'<div class="metric-label">Average Monthly</div>')
        html_parts.append(f'<div class="metric-value">{avg_amount_str}</div>')
        html_parts.append('</div>')
        
        html_parts.append('</div>') # Close analysis-grid
        html_parts.append('</div>') # Close payment-analysis
        
        # Period Summary Section
        html_parts.append('<div class="period-summary">')
        html_parts.append(f'<h3 class="section-title">📊 Period Summary ({result.months_ahead} months)</h3>')
        html_parts.append('<div class="summary-grid">')
        
        # Total contribution
        html_parts.append(f'<div class="metric-card">')
        html_parts.append(f'<div class="metric-label">Total Contribution</div>')
        html_parts.append(f'<div class="metric-value">{total_amount_str}</div>')
        html_parts.append('</div>')
        
        # Percentage of total
        if analytics.total_bills_required > 0:
            percentage = (payee_analytics.total_amount / analytics.total_bills_required) * 100
            html_parts.append(f'<div class="metric-card">')
            html_parts.append(f'<div class="metric-label">Share of Total Bills</div>')
            html_parts.append(f'<div class="metric-value">{percentage:.1f}%</div>')
            html_parts.append('</div>')
        
        # vs Household average
        household_avg_str = self.formatter.format_currency(analytics.average_monthly_requirement)
        html_parts.append(f'<div class="metric-card comparison-card">')
        html_parts.append(f'<div class="metric-label">vs Household Average</div>')
        html_parts.append(f'<div class="metric-value">{avg_amount_str}</div>')
        html_parts.append(f'<div class="metric-detail">Household: {household_avg_str}</div>')
        html_parts.append('</div>')
        
        html_parts.append('</div>') # Close summary-grid
        html_parts.append('</div>') # Close period-summary
        html_parts.append('</div>') # Close analytics-container
        
        return '\n'.join(html_parts)
    
    def _load_css(self) -> str:
        """Load CSS from external file."""
        import os
        css_path = os.path.join(os.path.dirname(__file__), 'html_assets', 'schedule.css')
        try:
            with open(css_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to basic styling if CSS file not found
            return """
            body { font-family: Arial, sans-serif; padding: 20px; }
            .schedule-table { width: 100%; border-collapse: collapse; }
            .schedule-table th, .schedule-table td { border: 1px solid #ddd; padding: 8px; }
            """
    
    def _get_base_html_template(self, title: str, subtitle: str, result: PaymentScheduleResult = None) -> str:
        """Get the base HTML template with professional styling."""
        css_content = self._load_css()
        
        # Add payee-specific CSS if we have result data
        payee_css = ""
        if result:
            payee_colors = self._get_payee_colors(result)
            payee_css_rules = []
            
            for payee_name, color in payee_colors.items():
                # CSS class names can't have spaces, so replace with hyphens
                css_class = payee_name.lower().replace(' ', '-').replace('.', '')
                payee_css_rules.append(f"""
        .payee-{css_class} {{
            color: {color} !important;
            font-weight: bold;
        }}
        
        .payee-{css_class}-bg {{
            background-color: {color}15 !important;
            border-left: 3px solid {color} !important;
        }}
        
        .payee-{css_class}-header {{
            background: linear-gradient(135deg, {color} 0%, {color}cc 100%) !important;
            color: white !important;
        }}""")
            
            payee_css = "\n        /* Payee-specific colors */\n" + "\n".join(payee_css_rules)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{css_content}{payee_css}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="subtitle">{subtitle}</div>
        <div class="generated">Generated on {date.today().strftime("%d %B %Y")}</div>
    </div>
    
    PLACEHOLDER_CONTENT
    
</body>
</html>'''
    
    @staticmethod
    def generate_payment_schedule_html(result: PaymentScheduleResult, show_zero_contribution: bool = False) -> str:
        """Static method to generate household schedule HTML."""
        generator = ProfessionalHtmlGenerator()
        return generator.generate_household_schedule_html(result, show_zero_contribution)