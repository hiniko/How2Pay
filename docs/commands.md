# Commands Reference

Complete reference for all How2Pay CLI commands with syntax, options, and examples.

## Table of Contents

- [Schedule Commands](#schedule-commands)
  - [schedule show](#schedule-show)
  - [schedule payee](#schedule-payee)
  - [schedule config](#schedule-config)
- [Bill Commands](#bill-commands)
  - [bills add](#bills-add)
  - [bills list](#bills-list)
- [Payee Commands](#payee-commands)
  - [payee add](#payee-add)
  - [payee list](#payee-list)
- [Global Options](#global-options)

---

## Schedule Commands

### `schedule show`
Generate household payment projection showing all payees and bills.

**Syntax:**
```bash
how2pay schedule show [OPTIONS]
```

**Options:**
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--months` | `-m` | int | 12 | Number of months to project |
| `--start-month` | | int | current | Starting month (1-12) |
| `--start-year` | | int | current | Starting year |
| `--pdf` | | flag | false | Export to PDF (auto-generates filename) |
| `--export` | | string | none | Export to CSV file |
| `--show-zero` | | flag | false | Show income streams with 0% contribution |

**Examples:**
```bash
# Basic 12-month projection
how2pay schedule show

# 6-month projection starting June 2024
how2pay schedule show --months 6 --start-month 6 --start-year 2024

# Export to PDF (filename: state_file_name.pdf)
how2pay schedule show --pdf

# Export to CSV
how2pay schedule show --export my_schedule.csv

# Include zero-contribution income streams
how2pay schedule show --show-zero
```

**Output Features:**
- **Payment Planning Summary**: Min/max payment ranges for each payee
- **Month Headers**: Show income month → bill month relationship
- **Color-coded Payees**: Consistent colors across all views
- **Bill Details**: Payment dates, amounts, and totals
- **Professional Layout**: Clean tables with proper spacing

---

### `schedule payee`
Generate payment schedule for a specific payee showing only their contributions.

**Syntax:**
```bash
how2pay schedule payee PAYEE_NAME [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `PAYEE_NAME` | Yes | Name of the payee (case-insensitive) |

**Options:**
Same as `schedule show` except automatically focuses on single payee.

**Examples:**
```bash
# Alice's 3-month schedule  
how2pay schedule payee Alice --months 3

# Export Bob's schedule to PDF (filename: state_file_name-Bob.pdf)
how2pay schedule payee Bob --pdf

# Charlie's schedule including zero contributions
how2pay schedule payee Charlie --show-zero
```

**Output Features:**
- **Individual Payment Summary**: Min/max range for just this payee
- **Personalized View**: Only bills the payee contributes to
- **Share Amounts**: Shows payee's portion of each bill
- **Income Streams**: All payee's income sources with dates

---

### `schedule config`
Manage schedule configuration settings.

#### `schedule config show`
Display current configuration.

```bash
how2pay schedule config show
```

#### `schedule config set`
Interactively update configuration settings.

```bash  
how2pay schedule config set
```

**Configurable Settings:**
- **Cutoff Day** (1-31): Day of month when bills are considered due
- **Weekend Adjustment**: How to handle weekend due dates
  - `last_working_day`: Move to preceding Friday
  - `next_working_day`: Move to following Monday
- **Default Projection Months** (1-60): Default number of months for projections

#### `schedule config test`
Test cutoff date calculations with sample data.

```bash
how2pay schedule config test
```

---

## Bill Commands

### `bills add`
Interactively add a new recurring bill.

**Syntax:**
```bash
how2pay bills add
```

**Interactive Prompts:**
1. **Bill name** (e.g., "Rent", "Electricity")
2. **Amount** (numeric, e.g., 1200.50)
3. **Recurrence pattern**:
   - **Calendar-based**: Specific day of month/week
   - **Interval-based**: Every N days/weeks/months
4. **Start date** (YYYY-MM-DD format)
5. **End date** (optional, for temporary bills)
6. **Custom sharing** (optional):
   - Choose payees and their percentage contributions
   - Must total 100%

**Example Session:**
```
Bill name: Rent
Amount: 1200
Recurrence kind (calendar/interval): calendar  
Interval (daily/weekly/monthly/quarterly/yearly): monthly
Start date (YYYY-MM-DD): 2024-01-01
End date (optional, YYYY-MM-DD): 
Custom payee percentages? (y/n): y
Available payees: Alice, Bob, Charlie
Alice percentage (0-100): 40
Bob percentage (0-100): 30  
Charlie percentage (0-100): 30
✓ Bill 'Rent' added successfully
```

---

### `bills list`
Display all configured bills with details.

**Syntax:**
```bash
how2pay bills list
```

**Output includes:**
- Bill name and amount
- Recurrence pattern and frequency
- Start/end dates
- Custom sharing percentages (if any)
- Next due date

**Example Output:**
```
Bills:
1. Rent - £1,200.00
   Recurrence: Monthly (calendar) starting 2024-01-01
   Next due: 2024-08-01
   
2. Groceries - £120.00  
   Recurrence: Weekly (interval) starting 2024-01-07
   Custom sharing: Alice 25%, Bob 35%, Charlie 40%
   Next due: 2024-07-28
```

---

## Payee Commands

### `payee add`
Interactively add a new payee with income streams.

**Syntax:**
```bash
how2pay payee add
```

**Interactive Prompts:**
1. **Payee name** (e.g., "Alice", "Bob Smith")
2. **Description** (optional, e.g., "Software Engineer")
3. **Start date** (optional, when they start contributing)
4. **Pay schedules** (can add multiple):
   - Amount per payment
   - Description (e.g., "Salary", "Freelance")
   - Recurrence pattern
   - Custom contribution percentage (optional)

**Example Session:**
```
Payee name: Alice
Description: Software Engineer
Start date (YYYY-MM-DD, optional): 
Add pay schedule? (y/n): y

Pay Schedule #1:
Amount: 2200
Description: Monthly Salary
Recurrence kind (calendar/interval): calendar
Interval: monthly
Start date: 2024-01-28
Custom contribution percentage (optional): 

Add another pay schedule? (y/n): y

Pay Schedule #2:  
Amount: 450
Description: Freelance Work
Recurrence kind: calendar
Interval: monthly
Start date: 2024-01-15
End date: 2024-06-15
Custom contribution percentage: 100

✓ Payee 'Alice' added with 2 pay schedules
```

---

### `payee list`
Display all configured payees with their income details.

**Syntax:**
```bash
how2pay payee list
```

**Output includes:**
- Payee name and description
- Start date (if applicable) 
- All pay schedules with amounts and recurrence
- Custom contribution percentages

**Example Output:**
```
Payees:
1. Alice (Software Engineer)
   Pay schedules (2):
     • Monthly Salary: £2,200.00 - Monthly starting 2024-01-28
     • Freelance Work: £450.00 - Monthly starting 2024-01-15, ends 2024-06-15 (100% contribution)

2. Bob (Part-time Teacher)
   Pay schedules (2):
     • Teaching Salary: £1,200.00 - Monthly starting 2024-01-25
     • Tutoring: £300.00 - Weekly starting 2024-01-12
     
3. Charlie (Graduate Student)  
   Start date: 2024-03-01
   Pay schedules (2):
     • Stipend: £800.00 - Monthly starting 2024-03-01
     • Weekend Job: £200.00 - Weekly starting 2024-03-02
```

---

## Global Options

### Help System
Get help for any command:

```bash
# General help
how2pay schedule --help

# Command-specific help  
how2pay schedule show --help
how2pay bills add --help
```

### File Management
Commands automatically use the active state file. To switch files:

```bash
# Set active state file
how2pay config context set secret_family_household.yaml

# Show current active state file
how2pay config context show
```

### Export Filenames
PDF exports automatically generate filenames:
- **Household schedules**: `{state_file_name}.pdf`
- **Payee schedules**: `{state_file_name}-{payee_name}.pdf`

**Examples:**
- `my_household.yaml` → `my_household.pdf`
- `family_budget.yaml` + Alice → `family_budget-Alice.pdf`

---

## Error Handling

### Common Issues

**"Payee not found"**
```bash
# List available payees
how2pay payee list
```

**"No bills or payees configured"**
```bash
# Add bills and payees first
how2pay bills add
how2pay payee add
```

**"PDF export failed"**
```bash
# Install PDF dependencies
pip install -e ".[pdf]"
```

### Validation Errors
- **Date formats**: Use YYYY-MM-DD (e.g., 2024-08-25)
- **Percentages**: Must be 0-100 and total 100% for bill sharing
- **Months**: Must be 1-12 for month selection
- **Projection limits**: Maximum 60 months ahead

For more troubleshooting, see [Configuration Guide](configuration.md) and [Features Guide](features.md).