# How 2 Bill Sharie

## Overview
The bill sharing system provides a flexible way to handle how bills are split between payees.

## Features

### 1. Payee-Level Default Percentages
Set a default share percentage for any payee that applies to all bills (unless overridden):

```yaml
payees:
- name: Bob
  default_share_percentage: 30  # Paulette pays 30% by default
  pay_schedules: [...]
- name: Alice 
  # No default_share_percentage = equal split of remaining
  pay_schedules: [...]
```

### 2. Simplified Bill Sharing

#### Equal Split (Default)
If no `share` configuration is specified, the bill is split equally among all active payees:

```yaml
- name: Rent
  amount: 1000
  # No share field = equal split among all payees
```

#### Exclusions Only
Exclude specific payees from a bill, remaining payees split equally:

```yaml
- name: Cat Food
  amount: 50
  share:
    exclude: [Bob]  # Everyone except Bob splits equally
```

#### Custom Percentages with Optional Exclusions
Specify exact percentages for some payees, with optional exclusions:

```yaml
- name: Special Bill
  amount: 100
  share:
    exclude: [Alice]
    custom:
      Bob: 60  # bob pays 60%
      #  Alice and Charlie 40% equally
```

## Calculation Logic

1. **Exclusions**: Remove excluded payees from consideration
2. **Custom Percentages**: Apply bill-specific custom percentages  
3. **Default Percentages**: Use payee default percentages for remaining amount
4. **Equal Split**: Split any remaining amount equally among payees without defaults

## Examples

### Scenario: Bob has 30% default, others have no defaults

```yaml
payees:
- name: Bob 
  default_share_percentage: 30
- name: Alice 
- name: Charlie 
```

**Bill Results:**
- `Rent (no share config)`: Bob 30%, others 23.33% each
- `Cat Food (exclude Andrew)`: Bob 30%, Alice & Charlie 35% each  
- `Special (custom: Paulette 60%, exclude Andrew)`: Bob 60%, Alice & Charlie 20% each

## Validation

The system automatically validates:
- Total percentages equal 100%
- No negative percentages
- Referenced payees exist
- Default percentages are between 0-100