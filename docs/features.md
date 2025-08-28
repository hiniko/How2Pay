# Features Guide

Comprehensive guide to all How2Pay features with detailed explanations and advanced usage patterns.

## Table of Contents

- [Payment Range Planning](#payment-range-planning)
- [Price History & Bill Increases](#price-history--bill-increases)
- [Custom Bill Splitting](#custom-bill-splitting)
- [Payee Start Dates](#payee-start-dates)
- [Income Stream Management](#income-stream-management)
- [Export Options](#export-options)
- [Color-Coded Payee System](#color-coded-payee-system)
- [Advanced Scheduling](#advanced-scheduling)
- [Configuration Management](#configuration-management)

---

## Payment Range Planning

### Overview
Every schedule starts with a payment summary showing min/max amounts each payee needs to contribute across the projection period, helping with budget planning and payment management.

### What It Shows
```
💰 Payment Planning
Alice: £649.97 - £677.47 (min: March 2024, max: January 2024)
Bob: £561.65 - £589.15 (min: March 2024, max: January 2024)
Charlie: £332.00 (consistent)
```

**For each payee:**
- **Minimum amount**: Lowest monthly contribution needed
- **Maximum amount**: Highest monthly contribution needed  
- **Min months**: When minimum payments occur 
- **Max months**: When maximum payments occur 
- **Consistent**: Shows when amounts are the same every month

### Use Cases

**Budget Planning**: Know your highest and lowest payment months to plan savings and expenses.

**Payment Management**: Prepare for higher payment periods by saving during lower ones.

**Income Timing**: Align income sources with higher payment requirements.

**Financial Communication**: Share payment expectations with household members upfront.

### Technical Details
- Calculations include all active bills for each payee
- Takes into account payee start dates and bill end dates
- Considers custom bill sharing percentages
- Updates automatically when bill amounts or schedules change

---

## Price History & Bill Increases

### Overview
Track bill increases over time with automatic scheduling. Instead of single amounts, bills can have multiple price periods with different amounts and effective dates.

### Configuration Format
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
      - amount: 1350.0  # 12.5% increase
        start_date: "2024-07-01"
        recurrence:
          kind: "calendar"
          interval: "monthly"
          start: "2024-07-01"
      - amount: 1500.0  # Another increase
        start_date: "2025-01-01"
        recurrence:
          kind: "calendar"
          interval: "monthly"
          start: "2025-01-01"
```

### How It Works
1. **Sorted by Date**: Price entries are automatically sorted by start_date
2. **Automatic Selection**: Scheduler picks the appropriate price for each payment date
3. **Seamless Transitions**: Bills automatically use new amounts starting from effective dates
4. **Future Planning**: Project costs with known future increases

### Use Cases

**Rent Increases**: Model annual rent increases with specific effective dates.

**Utility Rate Changes**: Handle seasonal pricing or rate adjustments.

**Subscription Changes**: Track streaming service or software price changes.

**Contract Renewals**: Plan for known price changes at contract renewal dates.

### Example Scenario
With the rent example above:
- **Jan-Jun 2024**: £1,200/month
- **Jul-Dec 2024**: £1,350/month  
- **Jan+ 2025**: £1,500/month

The payment planning summary will reflect these changes, showing different amounts for different months.

### Backward Compatibility
Existing bills with single `amount` and `recurrence` fields automatically convert to price_history format for seamless upgrades.

---

## Custom Bill Splitting

### Overview
Control exactly how bills are split between payees with custom percentages, supporting complex household arrangements.

### Equal Splitting (Default)
Without custom percentages, bills split equally among all active payees:
```yaml
bills:
  - name: "Electricity"
    amount: 120.0
    # Splits equally: 3 payees = £40 each
```

### Custom Percentages
Specify exact contributions per payee:
```yaml
bills:
  - name: "Groceries"
    amount: 200.0
    share:
      - payee: "Alice"
        percentage: 25.0  # £50
      - payee: "Bob"  
        percentage: 35.0  # £70
      - payee: "Charlie"
        percentage: 40.0  # £80
    # Total must equal 100%
```

### Single Payer Bills
Have one person pay specific bills:
```yaml
bills:
  - name: "Netflix"
    amount: 12.99
    share:
      - payee: "Bob"
        percentage: 100.0  # Bob pays all
```

### Mixed Scenarios
Some bills equal split, others custom:
```yaml
bills:
  - name: "Rent"
    amount: 1500.0
    # Equal split: £500 each
    
  - name: "Groceries"
    amount: 300.0
    share:
      - payee: "Alice"
        percentage: 30.0  # £90
      - payee: "Bob"
        percentage: 70.0  # £210
    # Charlie pays nothing for groceries
    
  - name: "Internet"  
    amount: 50.0
    # Equal split: £16.67 each
```

### Validation Rules
- Percentages must be between 0-100
- All percentages for a bill must total exactly 100%
- Payee names must match existing payees
- Missing payees get 0% (don't contribute to that bill)

### Use Cases

**Different Income Levels**: Higher earners pay more of shared expenses.

**Usage-Based Splitting**: Split utilities based on actual usage patterns.

**Personal vs Shared**: Some expenses (Netflix) paid by one person, others shared.

**Temporary Arrangements**: Custom splits during transition periods.

---

## Payee Start Dates

### Overview
Handle people joining households mid-year with start dates that control when they begin contributing to bills.

### Configuration
```yaml
payees:
  - name: "Alice"
    # No start_date = active from beginning
    
  - name: "Bob"
    start_date: "2024-06-01"  # Starts contributing June 1st
    
  - name: "Charlie"  
    start_date: "2024-09-15"  # Starts mid-September
```

### How It Works
- **Before Start Date**: Payee appears in schedules but shows "-" for payments
- **After Start Date**: Payee becomes active and contributes to bill calculations
- **Equal Split Impact**: Only active payees count for equal splitting
- **Custom Splits**: Inactive payees with custom percentages still show 0 contribution

### Example Impact
For a £300 bill with equal splitting:

**Before Charlie joins (2 active payees):**
- Alice: £150
- Bob: £150  
- Charlie: - (not active)

**After Charlie joins (3 active payees):**
- Alice: £100
- Bob: £100
- Charlie: £100

### Use Cases

**New Roommates**: Someone moving in mid-lease period.

**Seasonal Residents**: Students home for summer/winter breaks.

**Relationship Changes**: Partners moving in together.

**Trial Periods**: Temporary arrangements before permanent commitments.

### Display Behavior
- **TUI**: Shows "-" for inactive payees in payment columns
- **PDF**: Same behavior, clearly indicating non-active status
- **Payment Summary**: Only includes months when payee is active

---

## Income Stream Management

### Overview
Payees can have multiple income sources with different schedules, amounts, and contribution percentages.

### Multiple Income Streams
```yaml
payees:
  - name: "Alice"
    pay_schedules:
      - description: "Salary"
        recurrence:
          kind: "calendar"
          interval: "monthly"
          start: "2024-01-28"
          
      - description: "Freelance"
        recurrence:
          kind: "calendar"  
          interval: "monthly"
          start: "2024-01-15"
          end: "2024-06-15"  # Temporary income
        contribution_percentage: 100.0  # All goes to bills
```

### Income Stream Types

**Regular Salary**: Monthly/weekly consistent amounts

**Freelance/Contract**: Variable or temporary income with end dates

**Part-time Work**: Weekly or bi-weekly smaller amounts

**Benefits/Stipends**: Monthly government or institutional payments

**Investment Income**: Quarterly dividends or rental income

### Custom Contribution Percentages
Control what percentage of each income stream goes to bills:

```yaml
pay_schedules:
  - amount: 3000.0
    description: "Salary" 
    # No percentage = uses proportional calculation
    
  - amount: 500.0
    description: "Side Business"
    contribution_percentage: 100.0  # All goes to bills
    
  - amount: 200.0
    description: "Investments"
    contribution_percentage: 0.0    # None goes to bills
```

### Contribution Calculation
- **No percentage**: Income contributes proportionally to total household needs
- **Custom percentage**: Fixed percentage regardless of household needs
- **100% streams**: All income dedicated to bills (good for temporary income)
- **0% streams**: Personal income not used for shared expenses

### Display Features
- **Income stream names** in column headers
- **Payment dates** for each stream
- **Zero contributions** hidden by default (use `--show-zero` to display)
- **Multiple streams** per payee clearly separated

---

## Export Options

### Terminal Display (Default)
Rich, color-coded tables with:
- Payment planning summary at top
- Month-by-month breakdown
- Color-coded payee identification
- Professional table formatting

### PDF Export
Professional reports with:
- **Page 1**: Payment planning summary only
- **Page 2+**: Detailed monthly tables
- **Auto-generated filenames**: 
  - Household: `state_file_name.pdf`
  - Payee: `state_file_name-payee_name.pdf`
- **Color-coded headers**: Consistent payee colors
- **Professional styling**: Corporate report appearance

**Usage:**
```bash
# Household PDF
how2pay schedule show --pdf

# Payee PDF  
how2pay schedule payee Alice --pdf
```

### CSV Export
Spreadsheet-compatible format for:
- Further analysis in Excel/Sheets
- Integration with accounting software
- Custom reporting and charts
- Data manipulation and filtering

**Usage:**
```bash
how2pay schedule show --export my_schedule.csv
```

**CSV Structure:**
```csv
Month,Year,Bill,Amount,Payee,Income_Stream,Payment_Date,Required_Contribution
2024,8,Rent,1200.0,Alice,Salary,2024-07-28,400.0
2024,8,Rent,1200.0,Bob,Teaching,2024-07-25,400.0
```

### Export Comparison

| Feature | Terminal | PDF | CSV |
|---------|----------|-----|-----|
| Payment summary | ✓ | ✓ | ✗ |
| Color coding | ✓ | ✓ | ✗ |
| Professional layout | ✓ | ✓ | ✗ |
| Data analysis | ✗ | ✗ | ✓ |
| Printing | Limited | ✓ | ✗ |
| Sharing | Screenshot | ✓ | ✓ |

---

## Color-Coded Payee System

### Overview
Automatic color assignment using golden ratio distribution ensures consistent, visually distinct colors for each payee across all views.

### How It Works
- **Golden Ratio Algorithm**: Uses φ (1.618...) to distribute colors evenly across the spectrum
- **Consistent Assignment**: Same payee always gets same color
- **High Contrast**: Colors chosen for readability and distinction
- **WCAG Compliance**: 4.5:1 contrast ratio for accessibility

### Color Applications

**Terminal (TUI)**: Rich markup colors for payee names and headers

**PDF Export**: Hex colors for professional appearance  

**HTML Generation**: CSS-compatible color values

### Payee Color Examples
```
Payee 1: #E74C3C (Red)
Payee 2: #3498DB (Blue)  
Payee 3: #2ECC71 (Green)
Payee 4: #F39C12 (Orange)
Payee 5: #9B59B6 (Purple)
```

### Benefits
- **Quick Identification**: Instantly recognize payee data across complex tables
- **Visual Consistency**: Same colors in TUI, PDF, and HTML outputs
- **Professional Appearance**: Carefully chosen palette looks professional
- **Accessibility**: High contrast ensures readability for all users

---

## Advanced Scheduling

### Recurrence Types

#### Calendar-Based
Fixed days of month with automatic month-end handling:
```yaml
recurrence:
  kind: "calendar"
  interval: "monthly"
  start: "2024-01-31"  # Automatically adjusts for shorter months
```

#### Interval-Based  
Fixed intervals from start date:
```yaml
recurrence:
  kind: "interval"
  interval: "weekly"
  every: 2  # Every 2 weeks
  start: "2024-01-07"
```

### Weekend Adjustments
Handle bills due on weekends:

**Last Working Day**: Friday if due on weekend
**Next Working Day**: Monday if due on weekend

### Frequency Options
- **Daily**: Every N days
- **Weekly**: Every N weeks  
- **Monthly**: Every N months
- **Quarterly**: Every 3 months
- **Yearly**: Every 12 months

### Complex Scenarios
```yaml
# Bi-monthly bill starting mid-year
recurrence:
  kind: "interval"
  interval: "monthly" 
  every: 2
  start: "2024-06-15"
  end: "2025-12-31"
  
# Quarterly payments on specific date
recurrence:
  kind: "calendar"
  interval: "quarterly"
  start: "2024-03-31"  # March, June, September, December
```

---

## Configuration Management

### Schedule Options

#### Cutoff Day (1-31)
Determines which income funds which bills:
- **22nd**: Income from month X pays bills due in month X+1 after the 22nd
- **Impact**: Changes payment date calculations and payment timing
- **Use case**: Align with actual pay schedules and bill due dates

#### Weekend Adjustment
- **last_working_day**: Move weekend bills to Friday
- **next_working_day**: Move weekend bills to Monday
- **Impact**: Affects actual payment dates and payment calculations

#### Default Projection Months (1-60)
- Controls default schedule length
- Can be overridden with `--months` flag
- **Recommendation**: 12 months for annual planning, 3-6 for short-term

### State File Management
Multiple household configurations:
```bash
# Family household
how2pay config context set family.yaml

# Roommate situation  
how2pay config context set roommates.yaml

# Personal bills only
how2pay config context set personal.yaml
```

### Locale Configuration
Currency and date formatting:
- **UK**: £, dd/mm/yyyy
- **US**: $, mm/dd/yyyy  
- **EU**: €, dd/mm/yyyy (currency after amount)
- **Custom**: Define your own formats

### Validation and Testing
Built-in validation for:
- Date format requirements
- Percentage calculations (must total 100%)
- Payee name consistency
- Recurrence pattern validity
- Future date limits (60 months maximum)

---

For specific command syntax and options, see the [Commands Reference](commands.md). For real-world usage examples, check the [Examples Guide](examples.md).