import yaml
import os
from helpers.config_ops import get_active_state_file

from models.state_file import StateFile

def load_state():
    filename = get_active_state_file()
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = yaml.safe_load(f) or {}
        return StateFile.from_dict(data)
    return StateFile()

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
