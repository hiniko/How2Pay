import yaml
import os
from helpers.config_ops import get_active_state_file

from models.state_file import StateFile

def load_state():
    filename = get_active_state_file()
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Validate state structure before creating StateFile
            validation_errors = _validate_state_structure(data, filename)
            if validation_errors:
                for error in validation_errors:
                    print(error)
                exit(1)
            
            return StateFile.from_dict(data)
        except yaml.YAMLError as e:
            # Extract just the relevant error message and line number
            error_msg = str(e).split('\n')[0] if '\n' in str(e) else str(e)
            line_info = ""
            if hasattr(e, 'problem_mark') and e.problem_mark:
                line_info = f" (line {e.problem_mark.line + 1})"
            print(f"❌ YAML Error in '{filename}'{line_info}: {error_msg}")
            exit(1)
        except ValueError as e:
            # Handle date validation and other value errors
            error_msg = str(e)
            line_info = _find_error_line(filename, error_msg)
            if "day is out of range for month" in error_msg:
                print(f"❌ Invalid date in '{filename}'{line_info}: Check for dates like 2025-06-31 (June has only 30 days)")
            else:
                print(f"❌ Data Error in '{filename}'{line_info}: {error_msg}")
            exit(1)
        except Exception as e:
            print(f"❌ Error loading '{filename}': {str(e)}")
            exit(1)
    return StateFile()

def _validate_state_structure(data: dict, filename: str) -> list[str]:
    """Validate that state file has required fields and structure."""
    errors = []
    
    # Validate bills structure
    bills = data.get('bills', [])
    if isinstance(bills, list):
        for i, bill in enumerate(bills, 1):
            if not isinstance(bill, dict):
                continue
                
            bill_name = bill.get('name', f'Bill #{i}')
            
            # Check required fields - support both old and new format
            has_old_format = 'amount' in bill and 'recurrence' in bill
            has_new_format = 'price_history' in bill and isinstance(bill['price_history'], list) and len(bill['price_history']) > 0
            
            if not has_old_format and not has_new_format:
                if not bill.get('amount'):
                    errors.append(f"❌ Bill '{bill_name}': Missing required 'amount' field (or use 'price_history' for time-based pricing)")
                
                # Check recurrence structure for old format
                if 'recurrence' not in bill:
                    # Check if recurrence fields are at bill level (common mistake)
                    if any(key in bill for key in ['every', 'interval', 'kind', 'start']):
                        errors.append(f"❌ Bill '{bill_name}': Recurrence fields should be nested under 'recurrence:' key")
                    else:
                        errors.append(f"❌ Bill '{bill_name}': Missing required 'recurrence' field (or use 'price_history' for time-based pricing)")
            elif has_new_format:
                # Validate price_history structure
                for j, price_entry in enumerate(bill['price_history']):
                    if not isinstance(price_entry, dict):
                        continue
                    if not price_entry.get('amount'):
                        errors.append(f"❌ Bill '{bill_name}' price_history[{j}]: Missing 'amount' field")
                    if not price_entry.get('recurrence'):
                        errors.append(f"❌ Bill '{bill_name}' price_history[{j}]: Missing 'recurrence' field")
                    if not price_entry.get('start_date'):
                        errors.append(f"❌ Bill '{bill_name}' price_history[{j}]: Missing 'start_date' field")
            elif has_old_format and bill['recurrence'] is not None:
                recurrence = bill['recurrence']
                if not isinstance(recurrence, dict):
                    errors.append(f"❌ Bill '{bill_name}': 'recurrence' should be a dictionary")
                else:
                    if not recurrence.get('kind'):
                        errors.append(f"❌ Bill '{bill_name}': Missing 'kind' in recurrence")
                    if not recurrence.get('start'):
                        errors.append(f"❌ Bill '{bill_name}': Missing 'start' date in recurrence")
                    
                    # Check interval requirements
                    kind = recurrence.get('kind')
                    if kind == 'calendar' and not recurrence.get('interval'):
                        errors.append(f"❌ Bill '{bill_name}': Calendar recurrence missing 'interval' (monthly, quarterly, yearly)")
                    elif kind == 'interval' and not recurrence.get('interval'):
                        errors.append(f"❌ Bill '{bill_name}': Interval recurrence missing 'interval' (daily, weekly, monthly, etc.)")
    
    # Validate payees structure  
    payees = data.get('payees', [])
    if isinstance(payees, list):
        for i, payee in enumerate(payees, 1):
            if not isinstance(payee, dict):
                continue
                
            payee_name = payee.get('name', f'Payee #{i}')
            
            # Check pay_schedules
            pay_schedules = payee.get('pay_schedules', [])
            if not isinstance(pay_schedules, list):
                errors.append(f"❌ Payee '{payee_name}': 'pay_schedules' should be a list")
            elif len(pay_schedules) == 0:
                errors.append(f"❌ Payee '{payee_name}': No pay schedules defined")
            else:
                for j, schedule in enumerate(pay_schedules, 1):
                    if not isinstance(schedule, dict):
                        continue
                    
                    # Amount is optional for payees (since we don't display them)
                    # The system will use a default value for calculations if missing
                    
                    if 'recurrence' not in schedule:
                        errors.append(f"❌ Payee '{payee_name}', Schedule #{j}: Missing required 'recurrence' field")
                    elif schedule['recurrence'] is not None:
                        recurrence = schedule['recurrence']
                        if isinstance(recurrence, dict):
                            kind = recurrence.get('kind')
                            if kind == 'calendar' and not recurrence.get('interval'):
                                errors.append(f"❌ Payee '{payee_name}', Schedule #{j}: Calendar recurrence missing 'interval' (monthly, quarterly, yearly)")
                            elif kind == 'interval' and not recurrence.get('interval'):
                                errors.append(f"❌ Payee '{payee_name}', Schedule #{j}: Interval recurrence missing 'interval' (daily, weekly, monthly, etc.)")
    
    return errors

def _find_error_line(filename: str, error_msg: str) -> str:
    """Try to find the line number where an error occurred by searching for problematic content."""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Look for invalid dates in the error message
        if "day is out of range for month" in error_msg:
            # Search for dates like 2025-06-31
            import re
            for i, line in enumerate(lines, 1):
                if re.search(r'2025-06-31|2025-04-31|2025-09-31|2025-11-31', line):
                    return f" (line {i})"
                # Also check for other impossible dates
                if re.search(r'\d{4}-02-3[01]|\d{4}-04-31|\d{4}-06-31|\d{4}-09-31|\d{4}-11-31', line):
                    return f" (line {i})"
        
        return ""
    except:
        return ""

def make_yaml_safe(obj):
    if isinstance(obj, dict):
        return {k: make_yaml_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_yaml_safe(v) for v in obj]
    elif hasattr(obj, "__dict__"):
        return make_yaml_safe(obj.__dict__)
    else:
        return obj

def save_state(state_file: StateFile):
    filename = get_active_state_file()
    safe_state = make_yaml_safe(state_file.to_dict())
    with open(filename, 'w') as f:
        yaml.safe_dump(safe_state, f)
