# How2Pay - Personal Finance Management CLI

A powerful command-line tool for managing household finances, tracking bills, and generating payment schedules.

## ✨ Key Features

- **💰 Payment Planning**: Min/max payment ranges with month details for budget planning
- **📊 Payment Projections**: Generate detailed schedules up to 60 months ahead  
- **👥 Multi-Payee Support**: Handle complex households with multiple income sources
- **💡 Smart Bill Splitting**: Equal splits or custom percentages per bill per person
- **📈 Price History**: Track bill increases over time with automatic scheduling
- **⏰ Flexible Scheduling**: Calendar-based and interval-based recurrence patterns
- **🎨 Rich Terminal UI**: Color-coded payees with professional table layouts
- **📄 PDF Export**: Professional reports with payment summaries (optional dependency)
- **🌍 Locale Support**: Multiple currencies (£, $, €) and date formats

## 🚀 Quick Start

### Installation

#### Option 1: Using pipx (Recommended for CLI tools)
```bash
# Install globally with isolated dependencies
pipx install /path/to/how2pay
# Then run anywhere with:
how2pay --help
```

#### Option 2: From source with virtual environment
```bash
git clone <repository-url>
cd how2pay
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[pdf]"  # Include PDF support
# Then run with:
how2pay --help
```

#### Option 3: User installation
```bash
pip install --user /path/to/how2pay
# Then run with:
how2pay --help
```

### Try the Example
```bash
# Copy the example household configuration
cp example_household.yaml my_household.yaml

# Set it as active
python -c "
import sys; sys.path.append('.')
from helpers.config_ops import save_config
from models.config_model import AppConfig
save_config(AppConfig(active_state_file='my_household.yaml'))
"

# View the 3-person household schedule
how2pay schedule show --months 3
```

This shows a realistic household with Alice (Software Engineer), Bob (Part-time Teacher), and Charlie (Graduate Student) sharing rent, utilities, and groceries with different contribution levels.

**Example Output:**
```
💰 Payment Planning
Alice: £649.97 - £677.47 (min: March 2024, max: January 2024)
Bob: £561.65 - £589.15 (min: March 2024, max: January 2024) 
Charlie: £332.00 (consistent)

                     3-Month Payment Schedule Starting 1/2024
┌──────────────────────────┬─────────────────────────┬─────────────────┬──────────┐
│ Month                    │ Bills                   │ Detail          │ Payees   │
├──────────────────────────┼─────────────────────────┼─────────────────┼──────────┤
│ December → January 2024  │ Rent                    │ Payment Dates   │ 28/12    │
│                          │ Electricity             │ TOTAL           │ £649.97  │
│                          │ Internet                │                 │          │
│                          │ Groceries (4x)          │                 │          │
│                          │ Netflix                 │                 │          │
│                          │ TOTAL                   │                 │          │
└──────────────────────────┴─────────────────────────┴─────────────────┴──────────┘
```

### Create Your Own
```bash
# Start fresh
python -c "
import sys; sys.path.append('.')
from helpers.config_ops import save_config  
from models.config_model import AppConfig
save_config(AppConfig(active_state_file='my_finances.yaml'))
"

# Add bills and payees interactively
how2pay bills add
how2pay payee add

# Generate your schedule
how2pay schedule show
```

## 📋 Core Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `schedule show` | Household payment projection | `schedule show --months 6 --pdf` |
| `schedule payee <name>` | Individual payee schedule | `schedule payee Alice --pdf` |
| `bills add/list` | Manage recurring bills | `bills add` |
| `payee add/list` | Manage income sources | `payee add` |
| `schedule config set` | Configure settings | `schedule config set` |

## 🔧 Advanced Features

### Payment Range Planning
Each schedule starts with a payment summary showing min/max amounts and when they occur:
```
💰 Payment Planning
Alice: £649.97 - £677.47 (min: March 2024, max: January 2024)
Bob: £561.65 - £589.15 (min: March 2024, max: January 2024)
```

### Price History Support
Track bill increases over time:
```yaml
bills:
  - name: "Rent"
    price_history:
      - amount: 1200.0
        start_date: "2024-01-01"
        recurrence:
          kind: "calendar"
          interval: "monthly"
          start: "2024-01-01"
      - amount: 1350.0  # Rent increase
        start_date: "2024-07-01" 
        recurrence:
          kind: "calendar"
          interval: "monthly"
          start: "2024-07-01"
```

### Custom Bill Splitting
```yaml
bills:
  - name: "Groceries"
    amount: 120.0
    share:
      - payee: "Alice"
        percentage: 25.0  # Alice pays 25%
      - payee: "Bob"
        percentage: 35.0  # Bob pays 35%
      - payee: "Charlie"
        percentage: 40.0  # Charlie pays 40%
```

### Payee Start Dates
Handle people joining mid-year:
```yaml
payees:
  - name: "Charlie"
    start_date: "2024-03-01"  # Starts contributing March 1st
    pay_schedules:
      - amount: 800.0
        description: "Stipend"
```

## 📚 Documentation

For detailed documentation on all features, configuration options, and advanced usage:

**[📖 View Full Documentation →](docs/)**

- [Commands Reference](docs/commands.md) - Complete command guide
- [Configuration](docs/configuration.md) - All settings and options  
- [Features Guide](docs/features.md) - Advanced functionality
- [Examples](docs/examples.md) - Common use cases and patterns

## 🔄 Export Options

- **PDF**: Professional reports with payment summaries on page 1, detailed tables on following pages
- **CSV**: Spreadsheet-compatible format for further analysis
- **Terminal**: Rich, color-coded display with payment planning summaries

## 🛠️ Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python run_tests.py

# Format code
black .

# Lint code  
ruff check .
```

## 🆘 Getting Help

```bash
# General help
how2pay --help

# Command-specific help
how2pay schedule show --help
how2pay payee --help
```

---

*Built with Python, Typer, and Rich for an excellent CLI experience.*