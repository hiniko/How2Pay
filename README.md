# How2Pay CLI - Personal Finance Management Tool

A command-line tool for managing bills, payees, and generating cash flow projections to help you plan your personal finances.

## Features

- **Bill Management**: Track recurring bills with flexible recurrence patterns
- **Payee Management**: Manage income sources and payment schedules  
- **Cash Flow Projections**: Generate detailed payment schedules up to 60 months ahead
- **Payee-Specific Schedules**: View individual schedules showing only bills each payee contributes to
- **Locale Support**: Configurable currency symbols and date formats (UK £, US $, EU €)
- **Rich TUI Display**: Beautiful terminal tables with detailed breakdowns and color-coded payee identification
- **PDF Export**: Generate professional PDFs with color-coded payee headers and page breaks per month (optional dependency)
- **CSV Export**: Export schedules for use in spreadsheets
- **Color-Coded Payees**: Automatic color assignment using golden ratio distribution for easy identification across all views
- **Flexible Configuration**: Customizable cutoff dates and weekend adjustments
- **Well Tested**: Comprehensive test suite with 44 unit tests

## Installation

### Prerequisites
- Python 3.13 or higher
- pip

### Install for Development
```bash
git clone <repository-url>
cd Finances
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Install for Production
```bash
pip install -e .

# For PDF export functionality (optional)
pip install -e ".[pdf]"
```

## Quick Start

### Option 1: Start from Example
1. **Use the comprehensive example household:**
   ```bash
   how2pay init --filename example_household.yaml
   cp example_household.yaml example_household.yaml.backup  # Keep original as reference
   ```

2. **View the example schedule:**
   ```bash
   how2pay schedule show --months 3
   ```

3. **Explore individual payee schedules:**
   ```bash
   how2pay payee schedule Alice
   how2pay payee schedule Bob
   how2pay payee schedule Charlie
   ```

### Option 2: Start from Scratch
1. **Initialize a new state file:**
   ```bash
   how2pay init
   ```

2. **Add some bills:**
   ```bash
   how2pay bills add
   ```

3. **Add income sources (payees):**
   ```bash
   how2pay payee add
   ```

4. **Generate a cash flow projection:**
   ```bash
   how2pay schedule show
   ```

### Example Household Features

The `example_household.yaml` demonstrates a realistic three-person household with:

**Bills showcasing different assignment types:**
- **Equal splits**: Electricity, Internet, Council Tax (split equally among all 3 payees)
- **Custom percentages**: Groceries (Alice 25%, Bob 35%, Charlie 40%)
- **Single payer**: Netflix (Bob pays 100%), Gym (Alice 60%, Charlie 40%)
- **Various frequencies**: Monthly bills, weekly groceries, bi-monthly supplies

**Payees with diverse income patterns:**
- **Alice** (Software Engineer): £2,200 monthly salary + £450 freelance (temporary)
- **Bob** (Part-time Teacher): £1,200 monthly + £300 weekly tutoring
- **Charlie** (Graduate Student): £800 monthly stipend + £200 weekly weekend job

**Configuration:**
- Cutoff day: 22nd of each month
- Weekend adjustment: Move to last working day
- 12-month default projections

This example shows real-world complexity including temporary income, mixed bill responsibilities, and different earning patterns.

## Usage Guide

### Bill Management

**Add a new bill:**
```bash
how2pay bills add
# Interactive prompts will guide you through:
# - Bill name and amount
# - Recurrence pattern (daily, weekly, monthly, quarterly, yearly)
# - Start and end dates
```

**List all bills:**
```bash
how2pay bills list
```

### Payee Management

**Add a new payee (income source):**
```bash
how2pay payee add
# Configure:
# - Payee name
# - Payment schedules with amounts and recurrence
# - Custom contribution percentages (optional)
```

**List all payees:**
```bash
how2pay payee list
```

### Cash Flow Projections

**Generate a 12-month projection:**
```bash
how2pay schedule show
```

**Custom projection options:**
```bash
# Start from specific month/year
how2pay schedule show --start-month 6 --start-year 2024

# Project for specific number of months
how2pay schedule show --months 18

# Export to CSV
how2pay schedule show --export payment_schedule.csv

# Export to PDF (requires PDF dependencies)
how2pay schedule show --pdf payment_schedule.pdf
```

### Configuration

**View current settings:**
```bash
how2pay schedule config show
```

**Update configuration:**
```bash
how2pay schedule config set
# Configure:
# - Cutoff day of month (when bills are considered "due")
# - Weekend adjustment strategy
# - Default projection months
```

**Test cutoff dates:**
```bash
how2pay schedule config test
```

### Locale Configuration

**Set locale to a preset:**
```bash
# UK format: £, dd/mm/yyyy dates
how2pay config locale preset uk

# US format: $, mm/dd/yyyy dates  
how2pay config locale preset us

# EU format: €, dd/mm/yyyy dates (currency after amount)
how2pay config locale preset eu
```

**Custom locale configuration:**
```bash
how2pay config locale set
# Interactive setup for currency symbol, position, date format, separators
```

**View current locale:**
```bash
how2pay config locale show
```

### Payee-Specific Schedules

**View schedule for a specific payee:**
```bash
how2pay payee schedule Alice

# Export payee schedule to PDF
how2pay payee schedule Alice --pdf alice_schedule.pdf
```

This shows:
- Only bills the payee contributes to (with their portion amounts)
- Payment dates for their income streams with color-coded payee names
- Required contributions and percentages
- Clean focus on what that individual needs to pay
- Color-coded headers for easy payee identification in household views

## Configuration Options

### Cutoff Day
- Sets which day of the month bills are considered due
- Used to determine which income should fund which bills
- Range: 1-31 days

### Weekend Adjustment
- **last_working_day**: Move weekend due dates to preceding Friday
- **next_working_day**: Move weekend due dates to following Monday

### Bill Recurrence Patterns
- **Interval-based**: Every N days/weeks/months from start date
- **Calendar-based**: Specific days of week/month (coming soon)

## Planned Features

### Income Amount Display (Optional)
Currently, schedule displays show only payment dates, required contributions, and percentages for income streams. A future enhancement will add:

- **Optional income amount display**: `--show-amounts` flag to display actual income amounts
- **Coverage warnings**: Automatic alerts when income streams won't cover required contributions
- **Shortfall analysis**: Detailed breakdown of months where income is insufficient
- **Buffer recommendations**: Suggestions for maintaining adequate cash reserves

**Example with income amounts:**
```
Payment Dates │ 22/08 │ 26/08
Income Amount │ £865  │ £135  ← Optional display
Required      │ £97   │ £15   
Coverage      │ ✓     │ ⚠️    ← Warn if insufficient
```

### Advanced Bill Assignment
- **Percentage-based splitting**: Assign custom percentages per bill per payee
- **Conditional assignments**: Bills that apply only in certain months
- **Priority-based allocation**: Specify which payees pay which bills first

### Enhanced Reporting
- **Monthly summaries**: Total income vs expenses per payee
- **Trend analysis**: Spending patterns over time
- **Budget variance**: Compare actual vs planned expenses

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. tests/

# Run specific test class
pytest tests/test_cash_flow.py::TestCalculateMonthlyBillTotal -v
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .
```

### Development Dependencies
Install development dependencies with:
```bash
pip install -e ".[dev]"
```

Includes:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting  
- `black` - Code formatter
- `ruff` - Fast Python linter

## Support

### Getting Help
```bash
# General help
how2pay --help

# Command-specific help
how2pay schedule --help
how2pay bills --help
```

### Version Information
```bash
how2pay --version
```

## License

This project is for personal use and development.

---

*Built with Python, Typer, and Rich for an excellent CLI experience.*