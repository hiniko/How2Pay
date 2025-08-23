import yaml
import os
from models.config_model import AppConfig
CONFIG_FILE = 'how2pay_config.yaml'

def load_config() -> AppConfig:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = yaml.safe_load(f) or {}
            return AppConfig(**data)
    return AppConfig()

def save_config(config: AppConfig):
    from dataclasses import asdict
    with open(CONFIG_FILE, 'w') as f:
        yaml.safe_dump(asdict(config), f)

def get_active_state_file() -> str:
    config = load_config()
    return config.active_state_file

def set_active_state_file(filename: str):
    config = load_config()
    config.active_state_file = filename
    save_config(config)
