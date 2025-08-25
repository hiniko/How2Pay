"""PDF export functionality for schedule displays."""

import os
from datetime import datetime
from rich.console import Console
from typing import Optional
from scheduler.cash_flow import PaymentScheduleResult
from .html_generator import ProfessionalHtmlGenerator


class PdfExporter:
    """Handles PDF export of schedule data."""
    
    @staticmethod
    def is_available() -> bool:
        """Check if PDF export dependencies are available."""
        try:
            import weasyprint
            return True
        except ImportError:
            return False
    
    @staticmethod
    def export_schedule_to_pdf(
        result: PaymentScheduleResult,
        output_path: str,
        payee_name: Optional[str] = None,
        show_zero_contribution: bool = False
    ) -> bool:
        """
        Export schedule to professional PDF. Handles both payee-specific and household schedules.
        
        Args:
            result: PaymentScheduleResult data
            output_path: Path where PDF should be saved
            payee_name: If provided, exports payee-specific schedule. If None, exports household schedule.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if payee_name:
            return PdfExporter.export_professional_payee_schedule_to_pdf(
                result=result,
                payee_name=payee_name,
                output_path=output_path,
                show_zero_contribution=show_zero_contribution
            )
        else:
            return PdfExporter.export_professional_household_schedule_to_pdf(
                result=result,
                output_path=output_path,
                show_zero_contribution=show_zero_contribution
            )
    
    @staticmethod
    def export_professional_payee_schedule_to_pdf(
        result: PaymentScheduleResult,
        payee_name: str,
        output_path: str,
        show_zero_contribution: bool = False
    ) -> bool:
        """
        Export payee schedule to professional PDF using direct HTML generation.
        
        Args:
            result: PaymentScheduleResult data
            payee_name: Name of the payee
            output_path: Path where PDF should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "PDF export requires weasyprint. Install with: pip install -e '.[pdf]'"
            )
        
        # Generate professional HTML
        html_generator = ProfessionalHtmlGenerator()
        html_content = html_generator.generate_payee_schedule_html(result, payee_name, show_zero_contribution)
        
        # Convert to PDF with professional CSS optimized for landscape
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string='''
                @page {
                    size: A4 landscape;
                    margin: 12mm 8mm;
                }
                
                body {
                    font-size: 9px;
                }
                
                .schedule-table th {
                    font-size: 8px;
                    padding: 8px 6px;
                }
                
                .schedule-table td {
                    font-size: 8px;
                    padding: 6px 4px;
                }
            ''')]
        )
        return True
    
    @staticmethod
    def export_professional_household_schedule_to_pdf(
        result: PaymentScheduleResult,
        output_path: str,
        show_zero_contribution: bool = False
    ) -> bool:
        """
        Export household schedule to professional PDF.
        
        Args:
            result: PaymentScheduleResult data
            output_path: Path where PDF should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "PDF export requires weasyprint. Install with: pip install -e '.[pdf]'"
            )
        
        # Generate professional HTML
        html_generator = ProfessionalHtmlGenerator()
        html_content = html_generator.generate_household_schedule_html(result, show_zero_contribution)
        
        # Convert to PDF
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string='''
                @page {
                    size: A4 landscape;
                    margin: 12mm 8mm;
                }
            ''')]
        )
        return True
    
    @staticmethod
    def export_console_to_pdf(
        console: Console, 
        output_path: str, 
        title: Optional[str] = None,
        width: int = 120
    ) -> bool:
        """
        Export Rich console output to PDF.
        
        Args:
            console: Rich console with recorded output
            output_path: Path where PDF should be saved
            title: Optional title for the PDF
            width: Console width for rendering
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError(
                "PDF export requires weasyprint. Install with: pip install -e '.[pdf]'"
            )
        
        # Get HTML from console
        html_content = console.export_html(inline_styles=True)
        
        # Create custom CSS for better PDF formatting
        css_styles = """
        body {
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            font-size: 8px;
            margin: 8mm;
            background: white;
            color: black;
            line-height: 1.0;
        }
        
        /* Table styling */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 3px 0;
            page-break-inside: avoid;
        }
        
        /* Pre-formatted text (main content) */
        pre {
            white-space: pre;
            overflow: visible;
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            font-size: 7px;
            line-height: 0.95;
            margin: 0;
            padding: 3px;
            width: 100%;
            max-width: none;
        }
        
        /* Title styling */
        .title {
            font-weight: bold;
            text-align: center;
            margin-bottom: 8px;
            font-size: 10px;
        }
        
        /* Page breaks and size - optimized for landscape */
        @page {
            margin: 8mm 6mm;
            size: A4 landscape;
        }
        
        /* Colors - ensure they work in PDF */
        .r1 { color: #800080; } /* purple/magenta */
        .r2 { font-weight: bold; }
        .r3 { color: #808000; font-weight: bold; } /* yellow */
        .r4 { color: #800000; font-weight: bold; } /* red */
        .r5 { color: #008000; } /* green */
        .r6 { color: #000080; font-weight: bold; } /* blue */
        .r7 { color: #008080; font-weight: bold; } /* cyan */
        .r8 { opacity: 0.7; } /* dim */
        
        /* Additional color classes that Rich might use */
        .bright_yellow { color: #FFFF00; font-weight: bold; }
        .bright_red { color: #FF0000; font-weight: bold; }
        .bright_green { color: #00FF00; }
        .bright_blue { color: #0000FF; font-weight: bold; }
        .bright_cyan { color: #00FFFF; font-weight: bold; }
        .bright_magenta { color: #FF00FF; }
        .dim { opacity: 0.7; }
        .bold { font-weight: bold; }
        """
        
        # Add title if provided
        title_html = ""
        if title:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            title_html = f"""
            <div class="title">
                <h2>{title}</h2>
                <p>Generated on {timestamp}</p>
            </div>
            """
        
        # Create complete HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title or 'Payment Schedule'}</title>
            <style>{css_styles}</style>
        </head>
        <body>
            {title_html}
            {html_content}
        </body>
        </html>
        """
        
        # Convert to PDF
        HTML(string=full_html).write_pdf(output_path)
        return True


