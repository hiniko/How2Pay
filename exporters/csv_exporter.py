import csv
from typing import List
from scheduler.cash_flow import PaymentScheduleResult


class CsvExporter:
    """Handles exporting payment schedules to CSV format."""
    
    @staticmethod
    def export_payment_schedule(result: PaymentScheduleResult, filename: str) -> None:
        """Export payment schedule to CSV file."""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'payee_name', 
                'schedule_description', 
                'income_amount', 
                'required_contribution', 
                'contribution_percentage', 
                'payment_date', 
                'is_before_cutoff'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in result.schedule_items:
                writer.writerow({
                    'payee_name': item.payee_name,
                    'schedule_description': item.schedule_description,
                    'income_amount': f"{item.income_amount:.2f}",
                    'required_contribution': f"{item.required_contribution:.2f}",
                    'contribution_percentage': f"{item.contribution_percentage:.1f}%",
                    'payment_date': item.payment_date.strftime('%Y-%m-%d'),
                    'is_before_cutoff': item.is_before_cutoff
                })