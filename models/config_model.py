from dataclasses import dataclass, asdict
import yaml
import os

CONFIG_FILE = 'how2pay_config.yaml'

@dataclass
class AppConfig:
    active_state_file: str = 'how2pay_state.yaml'
    # Add more config options here as needed


def load_config() -> AppConfig:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = yaml.safe_load(f) or {}
            return AppConfig(**data)
    return AppConfig()


def save_config(config: AppConfig):
    with open(CONFIG_FILE, 'w') as f:
        yaml.safe_dump(asdict(config), f)


def get_active_state_file() -> str:
    config = load_config()
    return config.active_state_file


def set_active_state_file(filename: str):
    config = load_config()
    config.active_state_file = filename
    save_config(config)
