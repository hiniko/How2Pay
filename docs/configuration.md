# Configuration Guide

Complete guide to configuring How2Pay for your specific needs, including advanced settings and customization options.

## Table of Contents

- [Configuration Files](#configuration-files)
- [Schedule Options](#schedule-options)
- [Locale Settings](#locale-settings)
- [State File Management](#state-file-management)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

---

## Configuration Files

### Application Configuration
How2Pay uses a simple configuration file to track settings:

**Location**: `how2pay_config.yaml` (in your working directory)

**Structure**:
```yaml
active_state_file: "my_household.yaml"
```

### State Files
Your financial data is stored in YAML state files:

**Structure**:
```yaml
bills: []          # List of recurring bills
payees: []         # List of income sources  
schedule_options:  # Schedule configuration
  cutoff_day: 22
  default_projection_months: 12
  weekend_adjustment: "last_working_day"
```

### File Management Commands
```bash
# Switch to different state file
how2pay config context set new_file.yaml

# Check current active file
how2pay config context show
```

---

## Schedule Options

### Cutoff Day

**Purpose**: Determines which income pays for which bills based on when bills are considered "due".

**Range**: 1-31 days

**Logic**: Bills due after the cutoff day in month X are paid by income received in month X. Bills due before the cutoff are paid by previous month's income.

**Example with cutoff day 22**:
```
Bill due Jan 25 → Paid by January income
Bill due Jan 15 → Paid by December income  
```

**Configuration**:
```bash
how2pay schedule config set
# Follow prompts to set cutoff day
```

**Choosing the Right Cutoff**:
- **Early month (1-10)**: Most bills paid by previous month's income
- **Mid month (15-20)**: Balanced approach, good for mixed bill timing
- **Late month (25-31)**: Most bills paid by current month's income

**Use Cases**:
- **Salary on 25th**: Set cutoff to 22-24 to align with pay dates
- **Mixed pay schedules**: Use 15-20 for balanced payments
- **End-of-month pay**: Set cutoff to 28-31

### Weekend Adjustment

**Purpose**: Handle bills that fall due on weekends when banks are closed.

**Options**:

#### `last_working_day`
- Moves weekend bills to the preceding Friday
- Conservative approach, money leaves accounts earlier
- Good for tight budgets where early payment is safer

#### `next_working_day`  
- Moves weekend bills to the following Monday
- Keeps money in accounts longer
- Good when maximizing interest or investment time

**Example**:
```
Bill due: Saturday, March 15, 2024

last_working_day → Friday, March 14, 2024
next_working_day → Monday, March 17, 2024
```

**Configuration**:
```bash
how2pay schedule config set
# Select weekend adjustment strategy
```

### Default Projection Months

**Purpose**: How many months to project by default (can be overridden per command).

**Range**: 1-60 months

**Recommendations**:
- **3-6 months**: Short-term planning, tight budgets
- **12 months**: Annual budgeting, most common
- **18-24 months**: Long-term planning, major life changes
- **36-60 months**: Multi-year projections, major purchases

**Configuration**:
```bash
how2pay schedule config set
# Set default projection period
```

---

## Locale Settings

### Currency Configuration

**Purpose**: Display amounts in your local currency with proper formatting.

**Supported Presets**:

#### UK Format (£)
```yaml
currency_symbol: "£"
currency_position: "before"  # £100.00
date_format: "dd/mm/yyyy"    # 25/08/2024
decimal_separator: "."
thousands_separator: ","
```

#### US Format ($)
```yaml
currency_symbol: "$"
currency_position: "before"  # $100.00  
date_format: "mm/dd/yyyy"    # 08/25/2024
decimal_separator: "."
thousands_separator: ","
```

#### EU Format (€)
```yaml
currency_symbol: "€"
currency_position: "after"   # 100.00€
date_format: "dd/mm/yyyy"    # 25/08/2024  
decimal_separator: ","
thousands_separator: "."
```

### Setting Locale

**Preset Configuration**:
```bash
# UK locale
how2pay config locale preset uk

# US locale
how2pay config locale preset us

# EU locale  
how2pay config locale preset eu
```

**Custom Configuration**:
```bash
how2pay config locale set
# Interactive setup for custom formatting
```

**View Current Locale**:
```bash
how2pay config locale show
```

---

## State File Management

### Multiple Households

**Scenario**: Managing finances for different households or situations.

**Setup**:
```bash
# Create separate state files
cp example_household.yaml family_home.yaml
cp example_household.yaml rental_property.yaml

# Switch between them
# Use family home
how2pay config context set family_home.yaml

# Work with family home data
how2pay schedule show

# Switch to rental property
how2pay config context set rental_property.yaml

# Work with rental data
how2pay schedule show
```

### Backup and Versioning

**Regular Backups**:
```bash
# Create timestamped backup
cp my_household.yaml "my_household_$(date +%Y%m%d).yaml"

# Keep monthly backups
cp my_household.yaml "my_household_$(date +%Y%m).yaml"
```

**Version Control** (recommended):
```bash
# Initialize git repository
git init
git add *.yaml
git commit -m "Initial financial configuration"

# Track changes over time
git add my_household.yaml
git commit -m "Updated rent amount and added new payee"
```

### File Organization

**Recommended Structure**:
```
finances/
├── current_household.yaml      # Main active file
├── backups/
│   ├── household_202408.yaml   # Monthly backup
│   └── household_202407.yaml
├── scenarios/
│   ├── roommate_leaves.yaml    # What-if scenarios  
│   └── salary_increase.yaml
└── templates/
    ├── new_household.yaml      # Template for new setups
    └── single_person.yaml      # Single person template
```

---

## Advanced Configuration

### Validation Rules

**Bills**:
- Bill names must be unique within a state file
- Amounts must be positive numbers
- Recurrence patterns must be valid
- Custom sharing percentages must total 100%
- Start dates must be valid YYYY-MM-DD format

**Payees**:
- Payee names must be unique within a state file  
- Pay schedule amounts must be positive
- Start dates must be valid YYYY-MM-DD format
- Contribution percentages must be 0-100

**Schedule Options**:
- Cutoff day must be 1-31
- Default projection months must be 1-60
- Weekend adjustment must be valid option

### Testing Configuration

**Test Cutoff Calculations**:
```bash
how2pay schedule config test
```

This shows sample bill due dates and how they're affected by your cutoff day setting.

**Validate State File**:
```bash
# Check for configuration errors
python -c "
import sys; sys.path.append('.')
from helpers.state_ops import load_state
try:
    state = load_state()
    print('✓ State file is valid')
    print(f'  Bills: {len(state.bills)}')
    print(f'  Payees: {len(state.payees)}')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

### Performance Tuning

**Large Datasets**:
- Limit projection months for faster calculation (use `--months`)
- Use `--show-zero false` to reduce display clutter
- Consider splitting very complex households into multiple state files

**Memory Usage**:
- Each month of projection uses minimal memory
- PDF generation requires more memory for complex layouts
- CSV export is most memory-efficient for large datasets

---

## Troubleshooting

### Common Issues

#### "State file not found"
```bash
# Check active file setting
how2pay config context show

# Create missing file or switch to existing one
cp example_household.yaml missing_file.yaml
```

#### "YAML parsing error"
```bash
# Check YAML syntax - common issues:
# - Inconsistent indentation (use spaces, not tabs)
# - Missing quotes around dates
# - Invalid date formats (must be YYYY-MM-DD)
# - Incorrect percentage values (must be numbers, not percentages)

# Validate YAML syntax
python -c "
import yaml
with open('my_household.yaml', 'r') as f:
    try:
        yaml.safe_load(f)
        print('✓ YAML syntax is valid')
    except yaml.YAMLError as e:
        print(f'✗ YAML error: {e}')
"
```

#### "Percentage validation error"
```bash
# Check bill sharing percentages
# Common issues:
# - Percentages don't total 100%
# - Using percentage symbols (use 25.0, not 25%)
# - Negative percentages
# - Payee names don't match exactly
```

#### "Date validation error"
```bash
# Check date formats
# Must be: YYYY-MM-DD
# ✓ 2024-08-25
# ✗ 25/08/2024
# ✗ August 25, 2024
# ✗ 2024-8-25 (needs zero padding)
```

### Performance Issues

#### "Slow generation"
```bash
# Reduce projection period
how2pay schedule show --months 6

# Check for complex recurrence patterns
# - Very frequent intervals (daily bills)  
# - Many overlapping bills
# - Complex sharing arrangements
```

#### "PDF generation fails"
```bash
# Install PDF dependencies
pip install -e ".[pdf]"

# Check available memory for large reports
# Consider reducing projection months for PDF export
```

### Data Recovery

#### "Corrupted state file"
```bash
# Restore from backup
cp my_household_backup.yaml my_household.yaml

# Or start fresh with example
cp example_household.yaml my_household.yaml
```

#### "Lost configuration"
```bash
# Reset to defaults
rm how2pay_config.yaml
# Will recreate with defaults on next run
```

### Getting Help

**Debug Information**:
```bash
# Show current configuration
how2pay config context show

# Additional debug info can be shown via Python if needed:
python -c "
import sys; sys.path.append('.')
from helpers.config_ops import load_config
from helpers.state_ops import load_state

config = load_config()
print(f'Config: {config}')
state = load_state()  
print(f'Bills: {len(state.bills)}, Payees: {len(state.payees)}')
"
```

**Log Output**:
Most errors include helpful context. Look for:
- Line numbers in YAML parsing errors
- Specific field names in validation errors
- Suggested fixes in error messages

For additional help, see the [Commands Reference](commands.md) for syntax details or [Examples](examples.md) for working configurations.