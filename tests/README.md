# Finances Project Tests

This directory contains unit tests for the personal finance management tool.

## Running Tests

### Using the test runner (recommended):
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
python run_tests.py

# Run specific test file
python run_tests.py test_cash_flow

# Run specific test class
python run_tests.py TestCalculateMonthlyBillTotal
```

### Using unittest directly:
```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test class
python -m unittest tests.test_cash_flow.TestCalculateMonthlyBillTotal -v

# Run specific test method
python -m unittest tests.test_cash_flow.TestCalculateMonthlyBillTotal.test_no_bills_returns_zero -v
```

## Test Structure

### test_cash_flow.py
Contains comprehensive unit tests for cash flow functions in `scheduler/cash_flow.py`.

#### TestCalculateMonthlyBillTotal
Tests for the `calculate_monthly_bill_total` function:
- ✅ Empty bill lists
- ✅ Single monthly bills (in and out of target month)
- ✅ Multiple bills in the same month
- ✅ Bi-monthly recurrence patterns
- ✅ Quarterly recurrence patterns  
- ✅ Bills with end dates (expired and active)
- ✅ Bills without recurrence (should be skipped)
- ✅ Projection start month filtering
- ✅ Year boundary cases (December)
- ✅ Leap year handling (February 29th)
- ✅ Mixed recurrence types in same month
- ✅ Month boundary edge cases (first/last day)
- ✅ Interval-based recurrence (weekly bills)
- ✅ Multiple occurrences in same month
- ✅ Bills ending mid-month

#### TestCalculateProportionalContributions
Tests for the `calculate_proportional_contributions` function:
- ✅ Empty bills and payees (edge cases)
- ✅ Single payee with single bill
- ✅ Multiple payees with equal responsibility splitting
- ✅ Payees with no income in funding month
- ✅ Custom contribution percentages (within payee schedules)
- ✅ Multi-month projections with year rollover
- ✅ Projection start month filtering
- ✅ Multiple bills in same month
- ✅ Payees with multiple income streams
- ✅ Complex scenarios with multiple payees and income streams
- ✅ Mixed custom and proportional schedule allocation
- ✅ Cutoff date integration

#### TestGetPayeeIncomeInMonth  
Tests for the `get_payee_income_in_month` function:
- ✅ Empty pay schedules
- ✅ Single monthly payments (in and out of target month)
- ✅ Multiple weekly payments in same month
- ✅ Bi-weekly payment patterns
- ✅ Multiple pay schedules for same payee
- ✅ Weekend adjustment logic (both directions)
- ✅ Payments moved outside month by weekend adjustment
- ✅ Duplicate payment date handling
- ✅ Pay schedules with end dates (expired and during month)
- ✅ Leap year handling (February 29th)
- ✅ Year boundary cases (December)

**Key Test Scenarios:**

1. **Basic Functionality**: Verifies core calculation works with simple cases
2. **Recurrence Patterns**: Tests different bill frequencies (monthly, bi-monthly, quarterly)
3. **Edge Cases**: Handles boundary conditions like leap years, month ends, year rollover
4. **Filtering**: Ensures projection start dates work correctly
5. **Complex Scenarios**: Multiple bills with different patterns in same month

## Test Data Patterns

The tests use helper methods to create consistent test data:

- `create_monthly_bill(name, amount, start_date)` - Creates monthly recurring bill
- `create_bimonthly_bill(name, amount, start_date)` - Creates bi-monthly bill  
- `create_quarterly_bill(name, amount, start_date)` - Creates quarterly bill
- `create_test_state(bills)` - Creates StateFile with bills for testing

## Test Summary

- **44 total tests** across 3 test classes
- **16 tests** for `calculate_monthly_bill_total` function
- **14 tests** for `calculate_proportional_contributions` function
- **14 tests** for `get_payee_income_in_month` function
- All edge cases covered including leap years, weekend adjustments, multiple recurrence patterns, and complex contribution scenarios

## Future Test Additions

When adding new cash flow functions, consider testing:

- Income calculation functions  
- Payee contribution calculations
- Weekend adjustment logic
- CSV export functionality
- Rich table display formatting

## Dependencies

Tests require the project's virtual environment with:
- rich
- PyYAML

Setup:
```bash
python -m venv venv
source venv/bin/activate  
pip install rich PyYAML
```