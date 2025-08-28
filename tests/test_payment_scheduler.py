import unittest
from datetime import date
from models.state_file import StateFile
from models.bill import Bill
from models.recurrence import Recurrence
from models.schedule_options import ScheduleOptions
from models.payee import Payee, PaySchedule
from scheduler.payment_scheduler import PaymentScheduler


class TestCalculateMonthlyBillTotal(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.schedule_options = ScheduleOptions()
        
    def create_test_state(self, bills):
        """Helper method to create a StateFile with given bills."""
        return StateFile(bills=bills, payees=[], schedule_options=self.schedule_options)
    
    def create_monthly_bill(self, name, amount, start_date):
        """Helper method to create a monthly recurring bill."""
        recurrence = Recurrence(
            kind='calendar',
            interval='monthly',
            start=start_date
        )
        return Bill(name=name, amount=amount, recurrence=recurrence)
    
    def create_bimonthly_bill(self, name, amount, start_date):
        """Helper method to create a bi-monthly recurring bill."""
        recurrence = Recurrence(
            kind='calendar',
            interval='monthly',
            every=2,
            start=start_date
        )
        return Bill(name=name, amount=amount, recurrence=recurrence)
    
    def create_quarterly_bill(self, name, amount, start_date):
        """Helper method to create a quarterly recurring bill."""
        recurrence = Recurrence(
            kind='calendar',
            interval='quarterly',
            start=start_date
        )
        return Bill(name=name, amount=amount, recurrence=recurrence)
    
    def test_no_bills_returns_zero(self):
        """Test that calculate_monthly_bill_total returns 0 when no bills exist."""
        state = self.create_test_state([])
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(total, 0.0)
    
    def test_single_monthly_bill_in_target_month(self):
        """Test calculation with a single monthly bill due in the target month."""
        bill = self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15))
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(total, 1200.0)
    
    def test_single_monthly_bill_not_in_target_month(self):
        """Test that a monthly bill not due in target month doesn't count."""
        bill = self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15))
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        # Check February (bill starts in March)
        total = scheduler.calculate_monthly_bill_total(2, 2024)
        self.assertEqual(total, 0.0)
    
    def test_multiple_monthly_bills_same_month(self):
        """Test calculation with multiple monthly bills in the same month."""
        bills = [
            self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15)),
            self.create_monthly_bill("Utilities", 150.0, date(2024, 3, 20)),
            self.create_monthly_bill("Insurance", 300.0, date(2024, 3, 1))
        ]
        state = self.create_test_state(bills)
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(total, 1650.0)  # 1200 + 150 + 300
    
    def test_bimonthly_bill_in_target_month(self):
        """Test calculation with bi-monthly bill due in target month."""
        bill = self.create_bimonthly_bill("Insurance", 600.0, date(2024, 1, 15))
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        # Should be due in January, March, May, etc.
        january_total = scheduler.calculate_monthly_bill_total(1, 2024)
        self.assertEqual(january_total, 600.0)
        
        march_total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(march_total, 600.0)
        
        # Should not be due in February
        february_total = scheduler.calculate_monthly_bill_total(2, 2024)
        self.assertEqual(february_total, 0.0)
    
    def test_quarterly_bill_in_target_month(self):
        """Test calculation with quarterly bill."""
        # Test with a bill that we know will work correctly
        bill = self.create_quarterly_bill("Property Tax", 1800.0, date(2024, 4, 15))
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        # Should be due in April (start month)
        april_total = scheduler.calculate_monthly_bill_total(4, 2024)
        self.assertEqual(april_total, 1800.0)
        
        # March should be 0 (before start)
        march_total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(march_total, 0.0)
        
        # May should be 0 (quarterly means next due is July)
        may_total = scheduler.calculate_monthly_bill_total(5, 2024)
        self.assertEqual(may_total, 0.0)
    
    def test_bill_with_end_date_expired(self):
        """Test that bills with expired end dates don't count."""
        recurrence = Recurrence(
            kind='calendar',
            interval='monthly',
            start=date(2024, 1, 15),
            end=date(2024, 2, 28)  # Ends in February
        )
        bill = Bill(name="Temp Service", amount=100.0, recurrence=recurrence)
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        # Should count in January and February
        january_total = scheduler.calculate_monthly_bill_total(1, 2024)
        self.assertEqual(january_total, 100.0)
        
        february_total = scheduler.calculate_monthly_bill_total(2, 2024)
        self.assertEqual(february_total, 100.0)
        
        # Should not count in March (expired)
        march_total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(march_total, 0.0)
    
    def test_bill_without_recurrence(self):
        """Test that bills without recurrence are skipped."""
        bill = Bill(name="One-time", amount=500.0, recurrence=None)
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(total, 0.0)
    
    def test_projection_start_month_filter(self):
        """Test that months before projection start are filtered out."""
        bill = self.create_monthly_bill("Rent", 1200.0, date(2024, 1, 15))
        state = self.create_test_state([bill])
        
        # Set projection start to March 2024
        scheduler = PaymentScheduler(state, projection_start_month=3, projection_start_year=2024)
        
        # January and February should return 0 (before projection start)
        january_total = scheduler.calculate_monthly_bill_total(1, 2024)
        self.assertEqual(january_total, 0.0)
        
        february_total = scheduler.calculate_monthly_bill_total(2, 2024)
        self.assertEqual(february_total, 0.0)
        
        # March should return the bill amount (on or after projection start)
        march_total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(march_total, 1200.0)
    
    def test_year_boundary_december(self):
        """Test calculation for December (month boundary case)."""
        bill = self.create_monthly_bill("Rent", 1200.0, date(2024, 12, 15))
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(12, 2024)
        self.assertEqual(total, 1200.0)
    
    def test_leap_year_february(self):
        """Test calculation for February in a leap year."""
        bill = self.create_monthly_bill("Rent", 1200.0, date(2024, 2, 29))  # 2024 is leap year
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(2, 2024)
        self.assertEqual(total, 1200.0)
    
    def test_mixed_recurrence_types(self):
        """Test calculation with bills of different recurrence types in same month."""
        bills = [
            self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15)),
            self.create_bimonthly_bill("Insurance", 400.0, date(2024, 1, 10)),  # Due in March
            # Note: quarterly bill starting Dec 2023 won't be due until April 2024
        ]
        state = self.create_test_state(bills)
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        # Monthly: 1200, Bimonthly: 400 = 1600
        self.assertEqual(total, 1600.0)
    
    def test_edge_case_bill_on_month_boundaries(self):
        """Test bills due on the first and last day of the month."""
        bills = [
            self.create_monthly_bill("First Day Bill", 100.0, date(2024, 3, 1)),
            self.create_monthly_bill("Last Day Bill", 200.0, date(2024, 3, 31))
        ]
        state = self.create_test_state([bills[0], bills[1]])
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(total, 300.0)
    
    def test_interval_based_recurrence(self):
        """Test interval-based recurrence (vs calendar-based)."""
        # Create an interval-based weekly bill
        recurrence = Recurrence(
            kind='interval',
            interval='weekly',
            every=1,
            start=date(2024, 3, 1)  # Friday
        )
        bill = Bill(name="Weekly Service", amount=50.0, recurrence=recurrence)
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        # Should have multiple occurrences in March
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        # March 1, 8, 15, 22, 29 = 5 weeks * $50 = $250
        self.assertEqual(total, 250.0)
    
    def test_multiple_occurrences_same_month(self):
        """Test a bill that occurs multiple times in the same month."""
        # Weekly bill starting March 1
        recurrence = Recurrence(
            kind='interval',
            interval='weekly',
            every=1,
            start=date(2024, 3, 1)
        )
        bill = Bill(name="Weekly Payment", amount=25.0, recurrence=recurrence)
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        total = scheduler.calculate_monthly_bill_total(3, 2024)
        # Should count all weekly occurrences in March
        expected = 5 * 25.0  # 5 Fridays in March 2024
        self.assertEqual(total, expected)
    
    def test_bill_ending_mid_month(self):
        """Test bill that ends partway through the target month."""
        recurrence = Recurrence(
            kind='calendar',
            interval='monthly',
            start=date(2024, 1, 15),
            end=date(2024, 3, 10)  # Ends before monthly due date in March
        )
        bill = Bill(name="Ending Service", amount=200.0, recurrence=recurrence)
        state = self.create_test_state([bill])
        scheduler = PaymentScheduler(state)
        
        # Should count in March since end date is after start of month
        # but the recurrence end is before the due date
        march_total = scheduler.calculate_monthly_bill_total(3, 2024)
        self.assertEqual(march_total, 0.0)  # Ends before March 15th
        
        # Should count in February
        february_total = scheduler.calculate_monthly_bill_total(2, 2024)
        self.assertEqual(february_total, 200.0)


class TestCalculateProportionalContributions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.schedule_options = ScheduleOptions(cutoff_day=28)
    
    def create_simple_test_state(self, bills, payees):
        """Helper method to create a StateFile with given bills and payees."""
        return StateFile(bills=bills, payees=payees, schedule_options=self.schedule_options)
    
    def create_monthly_bill(self, name, amount, start_date):
        """Helper method to create a monthly recurring bill."""
        recurrence = Recurrence(kind='calendar', interval='monthly', start=start_date)
        return Bill(name=name, amount=amount, recurrence=recurrence)
    
    def create_monthly_payee(self, name, amount, start_date, description=None):
        """Helper method to create a payee with monthly income."""
        recurrence = Recurrence(kind='calendar', interval='monthly', start=start_date)
        schedule = PaySchedule(amount=amount, recurrence=recurrence, description=description)
        return Payee(name=name, pay_schedules=[schedule])
    
    def create_payee_with_custom_percentage(self, name, amount, start_date, percentage, description=None):
        """Helper method to create a payee with custom contribution percentage."""
        recurrence = Recurrence(kind='calendar', interval='monthly', start=start_date)
        schedule = PaySchedule(
            amount=amount, 
            recurrence=recurrence, 
            description=description,
            contribution_percentage=percentage
        )
        return Payee(name=name, pay_schedules=[schedule])
    
    def test_no_bills_returns_empty(self):
        """Test that no bills results in empty schedule."""
        bills = []
        payees = [self.create_monthly_payee("Alice", 3000.0, date(2024, 2, 15))]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        self.assertEqual(result.schedule_items, [])
    
    def test_no_payees_returns_empty(self):
        """Test that no payees results in empty schedule."""
        bills = [self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15))]
        payees = []
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        self.assertEqual(result.schedule_items, [])
    
    def test_single_payee_single_bill_proportional_split(self):
        """Test basic scenario with one payee and one bill."""
        bills = [self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15))]
        payees = [self.create_monthly_payee("Alice", 3000.0, date(2024, 2, 15))]  # Income in Feb
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        self.assertEqual(len(result.schedule_items), 1)
        item = result.schedule_items[0]
        self.assertEqual(item.payee_name, "Alice")
        self.assertEqual(item.income_amount, 3000.0)
        self.assertEqual(item.required_contribution, 1200.0)  # Full bill amount since single payee
        self.assertEqual(item.contribution_percentage, 40.0)  # 1200/3000 * 100
        self.assertTrue(item.is_before_cutoff)
    
    def test_multiple_payees_equal_split(self):
        """Test bill splitting between multiple payees."""
        bills = [self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15))]
        payees = [
            self.create_monthly_payee("Alice", 3000.0, date(2024, 2, 15)),
            self.create_monthly_payee("Bob", 2000.0, date(2024, 2, 15))
        ]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        self.assertEqual(len(result.schedule_items), 2)
        
        # Each payee should be responsible for 600 (1200/2)
        alice_item = next(item for item in result.schedule_items if item.payee_name == "Alice")
        bob_item = next(item for item in result.schedule_items if item.payee_name == "Bob")
        
        self.assertEqual(alice_item.required_contribution, 600.0)
        self.assertEqual(alice_item.contribution_percentage, 20.0)  # 600/3000 * 100
        
        self.assertEqual(bob_item.required_contribution, 600.0)
        self.assertEqual(bob_item.contribution_percentage, 30.0)  # 600/2000 * 100
    
    def test_payee_no_income_previous_month(self):
        """Test payee with no income in funding month."""
        bills = [self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15))]
        payees = [
            self.create_monthly_payee("Alice", 3000.0, date(2024, 2, 15)),  # Income in Feb
            self.create_monthly_payee("Bob", 2000.0, date(2024, 4, 15))     # Income in Apr (not Feb)
        ]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        self.assertEqual(len(result.schedule_items), 2)
        
        alice_item = next(item for item in result.schedule_items if item.payee_name == "Alice")
        bob_item = next(item for item in result.schedule_items if item.payee_name == "Bob")
        
        # Alice has income, pays proportionally
        self.assertEqual(alice_item.required_contribution, 600.0)  # 1200/2
        self.assertEqual(alice_item.income_amount, 3000.0)
        
        # Bob has no income in Feb, still responsible for share but shows as placeholder
        self.assertEqual(bob_item.required_contribution, 600.0)  # 1200/2  
        self.assertEqual(bob_item.income_amount, 0.0)
        self.assertEqual(bob_item.schedule_description, "No income in previous month")
        self.assertFalse(bob_item.is_before_cutoff)
    
    def test_custom_contribution_percentage(self):
        """Test payee with custom contribution percentage.
        
        Note: Custom percentages only affect allocation within each payee's own schedules,
        not across payees. Each payee still gets their full per-payee responsibility.
        """
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        payees = [
            self.create_payee_with_custom_percentage("Alice", 3000.0, date(2024, 2, 15), 30.0),
            self.create_monthly_payee("Bob", 2000.0, date(2024, 2, 15))
        ]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        self.assertEqual(len(result.schedule_items), 2)
        
        alice_item = next(item for item in result.schedule_items if item.payee_name == "Alice")
        bob_item = next(item for item in result.schedule_items if item.payee_name == "Bob")
        
        # Per payee responsibility = 1000/2 = 500 each
        # Alice has custom percentage (30% of her payee responsibility) = 500 * 0.3 = 150
        self.assertEqual(alice_item.required_contribution, 150.0)
        self.assertEqual(alice_item.contribution_percentage, 5.0)  # 150/3000 * 100
        
        # Bob has no custom percentage, so gets full payee responsibility proportionally
        self.assertEqual(bob_item.required_contribution, 500.0)
        self.assertEqual(bob_item.contribution_percentage, 25.0)  # 500/2000 * 100
    
    def test_multiple_months_projection(self):
        """Test multi-month projection."""
        bills = [self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15))]
        payees = [self.create_monthly_payee("Alice", 3000.0, date(2024, 2, 15))]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 3)  # 3 months
        
        # Should have 3 items (one for each month: Mar, Apr, May)
        self.assertEqual(len(result.schedule_items), 3)
        
        # All should be for Alice with same contribution
        for item in result.schedule_items:
            self.assertEqual(item.payee_name, "Alice")
            self.assertEqual(item.required_contribution, 1200.0)
            self.assertEqual(item.income_amount, 3000.0)
    
    def test_year_rollover(self):
        """Test projection that crosses year boundary."""
        bills = [self.create_monthly_bill("Rent", 1200.0, date(2024, 12, 15))]  # Dec 2024
        payees = [self.create_monthly_payee("Alice", 3000.0, date(2024, 11, 15))]  # Nov income
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(12, 2024, 2)  # Dec 2024, Jan 2025
        
        self.assertEqual(len(result.schedule_items), 2)
        
        # Both months should work correctly across year boundary
        for item in result.schedule_items:
            self.assertEqual(item.payee_name, "Alice")
            self.assertEqual(item.required_contribution, 1200.0)
    
    def test_projection_start_month_filtering(self):
        """Test that bills before projection start are filtered out."""
        bills = [self.create_monthly_bill("Rent", 1200.0, date(2024, 1, 15))]  # Starts Jan
        payees = [self.create_monthly_payee("Alice", 3000.0, date(2024, 2, 15))]  # Income Feb
        state = self.create_simple_test_state(bills, payees)
        
        # Set projection start to March (so Jan-Feb bills should be filtered)
        scheduler = PaymentScheduler(state, projection_start_month=3, projection_start_year=2024)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 3)  # Mar, Apr, May
        
        self.assertEqual(len(result.schedule_items), 3)  # Should have results for all 3 months
        
        # All should have the rent bill
        for item in result.schedule_items:
            self.assertEqual(item.required_contribution, 1200.0)
    
    def test_multiple_bills_same_month(self):
        """Test multiple bills due in same month."""
        bills = [
            self.create_monthly_bill("Rent", 1200.0, date(2024, 3, 15)),
            self.create_monthly_bill("Utilities", 300.0, date(2024, 3, 20))
        ]
        payees = [self.create_monthly_payee("Alice", 3000.0, date(2024, 2, 15))]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        self.assertEqual(len(result.schedule_items), 1)
        item = result.schedule_items[0]
        
        # Should contribute for total bills (1200 + 300 = 1500)
        self.assertEqual(item.required_contribution, 1500.0)
        self.assertEqual(item.contribution_percentage, 50.0)  # 1500/3000 * 100
    
    def test_payee_with_multiple_income_streams(self):
        """Test payee with multiple income streams in same month."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        
        # Alice has two income streams in February
        alice_monthly = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 15))
        alice_weekly = Recurrence(kind='interval', interval='weekly', every=1, start=date(2024, 2, 8))
        
        alice_schedules = [
            PaySchedule(amount=2000.0, recurrence=alice_monthly, description="Salary"),
            PaySchedule(amount=500.0, recurrence=alice_weekly, description="Freelance")  # 4 payments = 2000
        ]
        alice = Payee(name="Alice", pay_schedules=alice_schedules)
        
        payees = [alice]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        # Should have 5 items: 1 monthly salary + 4 weekly freelance payments
        self.assertEqual(len(result.schedule_items), 5)
        
        # All should be for Alice
        for item in result.schedule_items:
            self.assertEqual(item.payee_name, "Alice")
        
        # Check salary item
        salary_items = [item for item in result.schedule_items if item.schedule_description == "Salary"]
        self.assertEqual(len(salary_items), 1)
        
        # Check freelance items  
        freelance_items = [item for item in result.schedule_items if item.schedule_description == "Freelance"]
        self.assertEqual(len(freelance_items), 4)
        
        # Total contributions should add up to full bill amount
        total_contribution = sum(item.required_contribution for item in result.schedule_items)
        self.assertEqual(total_contribution, 1000.0)
    
    def test_multiple_payees_multiple_income_streams(self):
        """Test complex scenario with multiple payees having multiple income streams."""
        bills = [self.create_monthly_bill("Rent", 2000.0, date(2024, 3, 15))]
        
        # Alice: Monthly salary + weekly freelance
        alice_monthly = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 15))
        alice_weekly = Recurrence(kind='interval', interval='weekly', every=1, start=date(2024, 2, 8))
        alice_schedules = [
            PaySchedule(amount=3000.0, recurrence=alice_monthly, description="Salary"),
            PaySchedule(amount=200.0, recurrence=alice_weekly, description="Freelance")  # 4 * 200 = 800
        ]
        alice = Payee(name="Alice", pay_schedules=alice_schedules)
        
        # Bob: Just monthly salary
        bob = self.create_monthly_payee("Bob", 2000.0, date(2024, 2, 15), "Salary")
        
        payees = [alice, bob]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        # Alice: 5 items (1 monthly + 4 weekly), Bob: 1 item
        self.assertEqual(len(result.schedule_items), 6)
        
        alice_items = [item for item in result.schedule_items if item.payee_name == "Alice"]
        bob_items = [item for item in result.schedule_items if item.payee_name == "Bob"]
        
        self.assertEqual(len(alice_items), 5)
        self.assertEqual(len(bob_items), 1)
        
        # Each payee responsible for 1000 (2000/2)
        alice_total = sum(item.required_contribution for item in alice_items)
        bob_total = sum(item.required_contribution for item in bob_items)
        
        self.assertEqual(alice_total, 1000.0)
        self.assertEqual(bob_total, 1000.0)
    
    def test_payee_with_mixed_custom_and_proportional_schedules(self):
        """Test payee with some schedules having custom percentages and others proportional."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        
        # Alice has mixed schedule types
        monthly_recurrence = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 15))
        weekly_recurrence = Recurrence(kind='interval', interval='weekly', every=1, start=date(2024, 2, 8))
        
        alice_schedules = [
            PaySchedule(amount=2000.0, recurrence=monthly_recurrence, description="Salary", contribution_percentage=40.0),
            PaySchedule(amount=500.0, recurrence=weekly_recurrence, description="Freelance")  # No custom percentage
        ]
        alice = Payee(name="Alice", pay_schedules=alice_schedules)
        
        payees = [alice]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        # Should have 5 items: 1 salary + 4 freelance
        self.assertEqual(len(result.schedule_items), 5)
        
        salary_item = next(item for item in result.schedule_items if item.schedule_description == "Salary")
        freelance_items = [item for item in result.schedule_items if item.schedule_description == "Freelance"]
        
        # Salary: 40% of per_payee_responsibility (1000) = 400
        self.assertEqual(salary_item.required_contribution, 400.0)
        
        # Freelance: gets remaining 60% distributed proportionally among the 4 payments
        # Total freelance income = 4 * 500 = 2000
        # Remaining bill percentage = 100% - 40% = 60%
        # Each freelance payment gets: 1000 * 0.6 * (500/2000) = 1000 * 0.6 * 0.25 = 150
        for item in freelance_items:
            self.assertAlmostEqual(item.required_contribution, 150.0)
        
        # Verify total adds up
        total = salary_item.required_contribution + sum(item.required_contribution for item in freelance_items)
        self.assertEqual(total, 1000.0)
    
    def test_cutoff_date_in_payment_schedule_item(self):
        """Test that cutoff date is properly set in payment schedule items."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        payees = [self.create_monthly_payee("Alice", 2000.0, date(2024, 2, 15))]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        self.assertEqual(len(result.schedule_items), 1)
        item = result.schedule_items[0]
        
        # payment_date shows the income date (Feb 15)
        self.assertEqual(item.payment_date, date(2024, 2, 15))  # Income date
        # Note: cutoff_date is used in the logic but payment_date shows income date
        
        # The cutoff date affects the calculation but payment_date shows the income date
        self.assertTrue(item.is_before_cutoff)

    def test_multiple_income_streams_with_100_percent_contribution_bug(self):
        """Test bug: Multiple income streams with 100% contribution should split responsibility, not double it."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        
        # Alice has two 4-weekly payments that both occur in February (month before March bills)
        # Both have 100% contribution - they should SPLIT the responsibility, not both take 100%
        four_weekly_1 = Recurrence(kind='interval', interval='weekly', every=4, start=date(2024, 2, 1))
        four_weekly_2 = Recurrence(kind='interval', interval='weekly', every=4, start=date(2024, 2, 15))
        
        alice_schedules = [
            PaySchedule(amount=500.0, recurrence=four_weekly_1, description="Job A", contribution_percentage=100.0),
            PaySchedule(amount=500.0, recurrence=four_weekly_2, description="Job B", contribution_percentage=100.0)
        ]
        alice = Payee(name="Alice", pay_schedules=alice_schedules)
        
        payees = [alice]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        # Alice is the only payee, so her per-payee responsibility is 1000.0
        # She has two income streams both with 100% contribution
        # The bug: both streams get 1000.0 contribution (total 2000.0)
        # Expected: both streams should split the 1000.0 (500.0 each)
        
        alice_items = [item for item in result.schedule_items if item.payee_name == "Alice"]
        total_alice_contribution = sum(item.required_contribution for item in alice_items)
        
        # This should be 1000.0 (her full responsibility), not 2000.0 (double)
        self.assertEqual(total_alice_contribution, 1000.0, 
                        f"Expected 1000.0 total contribution, got {total_alice_contribution}. "
                        f"Individual contributions: {[item.required_contribution for item in alice_items]}")

    def test_custom_percentages_over_100_percent_normalized(self):
        """Test that custom percentages over 100% are normalized proportionally."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        
        # Alice has two income streams: one with 80% and one with 60% (total 140%)
        # They should be normalized to 80/140 and 60/140 of the total responsibility
        monthly_1 = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 10))
        monthly_2 = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 20))
        
        alice_schedules = [
            PaySchedule(amount=2000.0, recurrence=monthly_1, description="Job A", contribution_percentage=80.0),
            PaySchedule(amount=1500.0, recurrence=monthly_2, description="Job B", contribution_percentage=60.0)
        ]
        alice = Payee(name="Alice", pay_schedules=alice_schedules)
        
        payees = [alice]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        alice_items = [item for item in result.schedule_items if item.payee_name == "Alice"]
        
        # Total should still be 1000.0 (her full responsibility)
        total_alice_contribution = sum(item.required_contribution for item in alice_items)
        self.assertEqual(total_alice_contribution, 1000.0)
        
        # Job A should get 80/140 = 4/7 of 1000 = ~571.43
        # Job B should get 60/140 = 3/7 of 1000 = ~428.57
        job_a_item = next(item for item in alice_items if item.schedule_description == "Job A")
        job_b_item = next(item for item in alice_items if item.schedule_description == "Job B")
        
        expected_a = 1000.0 * (80.0 / 140.0)  # ~571.43
        expected_b = 1000.0 * (60.0 / 140.0)  # ~428.57
        
        self.assertAlmostEqual(job_a_item.required_contribution, expected_a, places=2)
        self.assertAlmostEqual(job_b_item.required_contribution, expected_b, places=2)

    def test_mixed_custom_and_no_percentage_schedules(self):
        """Test scenario with some schedules having custom percentages and others without."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        
        # Alice has 3 income streams:
        # - Job A: 60% custom contribution 
        # - Job B: no custom percentage (should get proportional share of remaining 40%)
        # - Job C: no custom percentage (should get proportional share of remaining 40%)
        monthly_1 = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 10))
        monthly_2 = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 15))
        monthly_3 = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 20))
        
        alice_schedules = [
            PaySchedule(amount=3000.0, recurrence=monthly_1, description="Job A", contribution_percentage=60.0),
            PaySchedule(amount=2000.0, recurrence=monthly_2, description="Job B"),  # No custom percentage
            PaySchedule(amount=1000.0, recurrence=monthly_3, description="Job C")   # No custom percentage
        ]
        alice = Payee(name="Alice", pay_schedules=alice_schedules)
        
        payees = [alice]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        alice_items = [item for item in result.schedule_items if item.payee_name == "Alice"]
        
        # Total should be 1000.0 (her full responsibility)
        total_alice_contribution = sum(item.required_contribution for item in alice_items)
        self.assertEqual(total_alice_contribution, 1000.0)
        
        job_a_item = next(item for item in alice_items if item.schedule_description == "Job A")
        job_b_item = next(item for item in alice_items if item.schedule_description == "Job B") 
        job_c_item = next(item for item in alice_items if item.schedule_description == "Job C")
        
        # Job A should get 60% = 600.0
        self.assertAlmostEqual(job_a_item.required_contribution, 600.0, places=2)
        
        # Jobs B and C should split the remaining 40% (400.0) proportionally by income:
        # Job B: 2000/(2000+1000) * 400 = 2/3 * 400 = ~266.67
        # Job C: 1000/(2000+1000) * 400 = 1/3 * 400 = ~133.33
        remaining_amount = 400.0
        total_remaining_income = 2000.0 + 1000.0
        expected_b = remaining_amount * (2000.0 / total_remaining_income)
        expected_c = remaining_amount * (1000.0 / total_remaining_income)
        
        self.assertAlmostEqual(job_b_item.required_contribution, expected_b, places=2)
        self.assertAlmostEqual(job_c_item.required_contribution, expected_c, places=2)

    def test_zero_contribution_streams_exist(self):
        """Test that 0% contribution streams can be generated."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        
        # Alice has 2 income streams:
        # - Job A: 100% contribution (should handle all the bills)
        # - Job B: 0% contribution (should contribute nothing, effectively "savings only")
        monthly_1 = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 10))
        monthly_2 = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 20))
        
        alice_schedules = [
            PaySchedule(amount=2000.0, recurrence=monthly_1, description="Job A", contribution_percentage=100.0),
            PaySchedule(amount=500.0, recurrence=monthly_2, description="Job B", contribution_percentage=0.0)  # Savings stream
        ]
        alice = Payee(name="Alice", pay_schedules=alice_schedules)
        
        payees = [alice]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        alice_items = [item for item in result.schedule_items if item.payee_name == "Alice"]
        
        # Should have 2 items (both streams)
        self.assertEqual(len(alice_items), 2)
        
        # Job A should handle 100% of bills = 1000.0
        job_a_item = next(item for item in alice_items if item.schedule_description == "Job A")
        job_b_item = next(item for item in alice_items if item.schedule_description == "Job B")
        
        self.assertEqual(job_a_item.required_contribution, 1000.0)
        self.assertEqual(job_b_item.required_contribution, 0.0)  # This is the 0% contribution stream

    def test_payee_start_date_excludes_inactive_payees(self):
        """Test that payees with start dates in the future are excluded from bill calculations."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 3, 15))]
        
        # Alice is active from the beginning (no start date)
        # Bob starts in April 2024, so shouldn't contribute to March 2024 bills
        monthly_recurrence = Recurrence(kind='calendar', interval='monthly', start=date(2024, 2, 15))
        
        alice_schedules = [
            PaySchedule(amount=2000.0, recurrence=monthly_recurrence, description="Alice Job")
        ]
        bob_schedules = [
            PaySchedule(amount=1500.0, recurrence=monthly_recurrence, description="Bob Job")
        ]
        
        alice = Payee(name="Alice", pay_schedules=alice_schedules)  # No start date = always active
        bob = Payee(name="Bob", pay_schedules=bob_schedules, start_date=date(2024, 4, 1))  # Starts April 1st
        
        payees = [alice, bob]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        # Test March 2024 - Bob should not contribute
        result = scheduler.calculate_proportional_contributions(3, 2024, 1)
        
        # Should only have Alice's items (Bob is inactive)
        alice_items = [item for item in result.schedule_items if item.payee_name == "Alice"]
        bob_items = [item for item in result.schedule_items if item.payee_name == "Bob"]
        
        self.assertEqual(len(alice_items), 1)  # Alice should have 1 item
        self.assertEqual(len(bob_items), 0)    # Bob should have no items (inactive)
        
        # Alice should be responsible for the full $1000 since Bob is inactive
        alice_item = alice_items[0]
        self.assertEqual(alice_item.required_contribution, 1000.0)
        
    def test_payee_start_date_includes_active_payees(self):
        """Test that payees become active after their start date."""
        bills = [self.create_monthly_bill("Rent", 1000.0, date(2024, 5, 15))]
        
        # Alice is active from the beginning
        # Bob starts in April 2024, so should contribute to May 2024 bills
        monthly_recurrence = Recurrence(kind='calendar', interval='monthly', start=date(2024, 4, 15))
        
        alice_schedules = [
            PaySchedule(amount=2000.0, recurrence=monthly_recurrence, description="Alice Job")
        ]
        bob_schedules = [
            PaySchedule(amount=1500.0, recurrence=monthly_recurrence, description="Bob Job")
        ]
        
        alice = Payee(name="Alice", pay_schedules=alice_schedules)  # No start date = always active
        bob = Payee(name="Bob", pay_schedules=bob_schedules, start_date=date(2024, 4, 1))  # Starts April 1st
        
        payees = [alice, bob]
        state = self.create_simple_test_state(bills, payees)
        scheduler = PaymentScheduler(state)
        
        # Test May 2024 - Both should contribute (Bob is active by then)
        result = scheduler.calculate_proportional_contributions(5, 2024, 1)
        
        alice_items = [item for item in result.schedule_items if item.payee_name == "Alice"]
        bob_items = [item for item in result.schedule_items if item.payee_name == "Bob"]
        
        self.assertEqual(len(alice_items), 1)  # Alice should have 1 item
        self.assertEqual(len(bob_items), 1)    # Bob should have 1 item (now active)
        
        # Both should split the $1000 equally (500 each)
        alice_item = alice_items[0]
        bob_item = bob_items[0]
        self.assertEqual(alice_item.required_contribution, 500.0)
        self.assertEqual(bob_item.required_contribution, 500.0)


class TestGetPayeeIncomeInMonth(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.schedule_options = ScheduleOptions()
        self.scheduler = PaymentScheduler(StateFile(bills=[], payees=[], schedule_options=self.schedule_options))
    
    def create_payee_with_monthly_income(self, name, amount, start_date, description=None):
        """Helper method to create a payee with monthly income."""
        recurrence = Recurrence(
            kind='calendar',
            interval='monthly',
            start=start_date
        )
        schedule = PaySchedule(
            amount=amount,
            recurrence=recurrence,
            description=description
        )
        return Payee(name=name, pay_schedules=[schedule])
    
    def create_payee_with_weekly_income(self, name, amount, start_date, description=None):
        """Helper method to create a payee with weekly income."""
        recurrence = Recurrence(
            kind='interval',
            interval='weekly',
            every=1,
            start=start_date
        )
        schedule = PaySchedule(
            amount=amount,
            recurrence=recurrence,
            description=description
        )
        return Payee(name=name, pay_schedules=[schedule])
    
    def create_payee_with_biweekly_income(self, name, amount, start_date, description=None):
        """Helper method to create a payee with bi-weekly income."""
        recurrence = Recurrence(
            kind='interval',
            interval='weekly',
            every=2,
            start=start_date
        )
        schedule = PaySchedule(
            amount=amount,
            recurrence=recurrence,
            description=description
        )
        return Payee(name=name, pay_schedules=[schedule])
    
    def test_no_pay_schedules_returns_empty(self):
        """Test that payee with no pay schedules returns empty list."""
        payee = Payee(name="No Income", pay_schedules=[])
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        self.assertEqual(result, [])
    
    def test_single_monthly_payment_in_month(self):
        """Test payee with single monthly payment due in target month."""
        payee = self.create_payee_with_monthly_income("Alice", 3000.0, date(2024, 3, 15))
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        self.assertEqual(len(result), 1)
        schedule, payment_date = result[0]
        self.assertEqual(schedule.amount, 3000.0)
        self.assertEqual(payment_date, date(2024, 3, 15))
    
    def test_monthly_payment_not_in_target_month(self):
        """Test that monthly payment not due in target month is not included."""
        payee = self.create_payee_with_monthly_income("Bob", 2500.0, date(2024, 4, 15))
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        self.assertEqual(result, [])
    
    def test_multiple_weekly_payments_in_month(self):
        """Test payee with multiple weekly payments in target month."""
        payee = self.create_payee_with_weekly_income("Charlie", 500.0, date(2024, 3, 1))  # Friday
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        # March 2024 has 5 Fridays: 1, 8, 15, 22, 29
        self.assertEqual(len(result), 5)
        
        expected_dates = [date(2024, 3, 1), date(2024, 3, 8), date(2024, 3, 15), 
                         date(2024, 3, 22), date(2024, 3, 29)]
        actual_dates = [payment_date for _, payment_date in result]
        
        self.assertEqual(actual_dates, expected_dates)
        
        # Each payment should be $500
        for schedule, _ in result:
            self.assertEqual(schedule.amount, 500.0)
    
    def test_biweekly_payments_in_month(self):
        """Test payee with bi-weekly payments."""
        payee = self.create_payee_with_biweekly_income("Diana", 1500.0, date(2024, 3, 1))
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        # Bi-weekly from March 1: March 1, March 15, March 29
        self.assertEqual(len(result), 3)
        
        expected_dates = [date(2024, 3, 1), date(2024, 3, 15), date(2024, 3, 29)]
        actual_dates = [payment_date for _, payment_date in result]
        
        self.assertEqual(actual_dates, expected_dates)
        
        # Each payment should be $1500
        for schedule, _ in result:
            self.assertEqual(schedule.amount, 1500.0)
    
    def test_multiple_pay_schedules_same_payee(self):
        """Test payee with multiple different pay schedules."""
        monthly_recurrence = Recurrence(kind='calendar', interval='monthly', start=date(2024, 3, 15))
        weekly_recurrence = Recurrence(kind='interval', interval='weekly', every=1, start=date(2024, 3, 8))
        
        schedules = [
            PaySchedule(amount=2000.0, recurrence=monthly_recurrence, description="Salary"),
            PaySchedule(amount=300.0, recurrence=weekly_recurrence, description="Part-time")
        ]
        
        payee = Payee(name="Multi-Income", pay_schedules=schedules)
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        # Should have 1 monthly payment + 4 weekly payments
        # Weekly: March 8, 15, 22, 29 (4 payments)  
        # Monthly: March 15 (1 payment)
        self.assertEqual(len(result), 5)
        
        # Check we have both salary and part-time payments
        amounts = [schedule.amount for schedule, _ in result]
        self.assertIn(2000.0, amounts)  # Salary
        self.assertEqual(amounts.count(300.0), 4)  # 4 part-time payments
    
    def test_weekend_adjustment_moves_payment_date(self):
        """Test that weekend adjustment affects the payment date."""
        # Create a payment due on Saturday (March 2, 2024)
        recurrence = Recurrence(kind='calendar', interval='monthly', start=date(2024, 3, 2))
        schedule = PaySchedule(
            amount=3000.0,
            recurrence=recurrence,
            weekend_adjustment='last_working_day'
        )
        payee = Payee(name="Weekend Worker", pay_schedules=[schedule])
        
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        self.assertEqual(len(result), 1)
        _, adjusted_date = result[0]
        
        # March 2, 2024 is Saturday, should be moved to Friday March 1, 2024
        self.assertEqual(adjusted_date, date(2024, 3, 1))
    
    def test_weekend_adjustment_next_working_day(self):
        """Test weekend adjustment moving to next working day."""
        # Create a payment due on Sunday (March 3, 2024)
        recurrence = Recurrence(kind='calendar', interval='monthly', start=date(2024, 3, 3))
        schedule = PaySchedule(
            amount=2500.0,
            recurrence=recurrence,
            weekend_adjustment='next_working_day'
        )
        payee = Payee(name="Sunday Worker", pay_schedules=[schedule])
        
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        self.assertEqual(len(result), 1)
        _, adjusted_date = result[0]
        
        # March 3, 2024 is Sunday, should be moved to Monday March 4, 2024
        self.assertEqual(adjusted_date, date(2024, 3, 4))
    
    def test_payment_moved_outside_month_by_weekend_adjustment(self):
        """Test payment that gets moved outside target month by weekend adjustment."""
        # Create a payment due on Saturday March 30, 2024 (last Saturday of month)
        recurrence = Recurrence(kind='calendar', interval='monthly', start=date(2024, 3, 30))
        schedule = PaySchedule(
            amount=3500.0,
            recurrence=recurrence,
            weekend_adjustment='next_working_day'
        )
        payee = Payee(name="Month Edge", pay_schedules=[schedule])
        
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        # Payment should be moved to Monday April 1, which is outside March
        # So it should not be included in March results
        self.assertEqual(len(result), 0)
    
    def test_no_duplicate_payments_same_date(self):
        """Test that duplicate payments on same date are handled correctly."""
        payee = self.create_payee_with_monthly_income("Duplicate Test", 1000.0, date(2024, 3, 15))
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        # Should only have one payment even with potential duplicate logic
        self.assertEqual(len(result), 1)
        
        # Verify the date tracking logic works (found_dates set)
        schedule, payment_date = result[0]
        self.assertEqual(payment_date, date(2024, 3, 15))
        self.assertEqual(schedule.amount, 1000.0)
    
    def test_payment_with_end_date_before_month(self):
        """Test payment schedule that ended before target month."""
        recurrence = Recurrence(
            kind='calendar',
            interval='monthly',
            start=date(2024, 1, 15),
            end=date(2024, 2, 28)  # Ends in February
        )
        schedule = PaySchedule(amount=2000.0, recurrence=recurrence)
        payee = Payee(name="Ended Job", pay_schedules=[schedule])
        
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        # Should have no payments since recurrence ended in February
        self.assertEqual(result, [])
    
    def test_payment_with_end_date_during_month(self):
        """Test payment schedule that ends during target month."""
        recurrence = Recurrence(
            kind='calendar',
            interval='monthly',
            start=date(2024, 1, 15),
            end=date(2024, 3, 10)  # Ends March 10
        )
        schedule = PaySchedule(amount=1800.0, recurrence=recurrence)
        payee = Payee(name="Ending Job", pay_schedules=[schedule])
        
        month_start = date(2024, 3, 1)
        month_end = date(2024, 3, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        # Should have no payments since March 15 payment would be after end date of March 10
        self.assertEqual(result, [])
    
    def test_february_leap_year(self):
        """Test payment calculation in February of leap year."""
        payee = self.create_payee_with_monthly_income("Leap Year", 2400.0, date(2024, 2, 29))
        month_start = date(2024, 2, 1)
        month_end = date(2024, 2, 29)  # 2024 is leap year
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        self.assertEqual(len(result), 1)
        _, payment_date = result[0]
        self.assertEqual(payment_date, date(2024, 2, 29))
    
    def test_december_year_boundary(self):
        """Test payment calculation in December (year boundary)."""
        payee = self.create_payee_with_monthly_income("Year End", 3200.0, date(2024, 12, 31))
        month_start = date(2024, 12, 1)
        month_end = date(2024, 12, 31)
        
        result = self.scheduler.get_payee_income_in_month(payee, month_start, month_end)
        
        self.assertEqual(len(result), 1)
        _, payment_date = result[0]
        self.assertEqual(payment_date, date(2024, 12, 31))
    


if __name__ == '__main__':
    unittest.main()