import os
import yaml
from pathlib import Path
from lib.constants import default_model, default_temperature, default_max_tokens
from lib.env_vars import OPENAI_API_KEY

CONFIG_DIR = Path(__file__).parent.parent / "config"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "default_config.yaml"

DEFAULT_CONFIG = {
    "model": default_model,
    "temperature": default_temperature,
    "max_tokens": default_max_tokens,
    "api_key": OPENAI_API_KEY or ""
}

def _create_default_config_file():
    if not DEFAULT_CONFIG_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_CONFIG_PATH, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f)

def _load_yaml_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    elif DEFAULT_CONFIG_PATH.exists():
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        _create_default_config_file()
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}

def get_config():
    """
    Returns a dict with config values for model, temperature, max_tokens, api_key.
    Precedence: environment variable > config.yaml > default_config.yaml > constants.py
    """
    config = dict(DEFAULT_CONFIG)
    file_config = _load_yaml_config()
    config.update({k: v for k, v in file_config.items() if v is not None})
    # Environment variable overrides
    config["model"] = os.getenv("LLM_MODEL", config["model"])
    config["temperature"] = float(os.getenv("LLM_TEMPERATURE", config["temperature"]))
    config["max_tokens"] = int(os.getenv("LLM_MAX_TOKENS", config["max_tokens"]))
    config["api_key"] = os.getenv("OPENAI_API_KEY", config["api_key"])
    return config 