from dataclasses import dataclass, asdict
import yaml
import os

CONFIG_FILE = 'how2pay_config.yaml'

@dataclass
class LocaleConfig:
    currency_symbol: str = '£'
    currency_position: str = 'before'  # 'before' or 'after'
    date_format: str = 'dd/mm/yyyy'  # 'dd/mm/yyyy' or 'mm/dd/yyyy'
    decimal_separator: str = '.'
    thousands_separator: str = ','

@dataclass
class AppConfig:
    active_state_file: str = 'how2pay_state.yaml'
    locale: LocaleConfig = None
    
    def __post_init__(self):
        if self.locale is None:
            self.locale = LocaleConfig()


def load_config() -> AppConfig:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = yaml.safe_load(f) or {}
            # Handle nested locale config
            if 'locale' in data and isinstance(data['locale'], dict):
                data['locale'] = LocaleConfig(**data['locale'])
            return AppConfig(**data)
    return AppConfig()


def save_config(config: AppConfig):
    with open(CONFIG_FILE, 'w') as f:
        yaml.safe_dump(asdict(config), f, default_flow_style=False)


def get_active_state_file() -> str:
    config = load_config()
    return config.active_state_file


def set_active_state_file(filename: str):
    config = load_config()
    config.active_state_file = filename
    save_config(config)
