"""
Config module for NeuroDesk AI Multi-Agent System.
"""

import json
from pathlib import Path
from typing import Dict, Any


def get_config(config_file: str = "config/config.json") -> Dict[str, Any]:
    """Load configuration from file."""
    config_path = Path(config_file)

    if not config_path.exists():
        return _get_default_config()

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return _get_default_config()


def _get_default_config() -> Dict[str, Any]:
    """Return default configuration."""
    return {
        "MAB": {
            "provider": "Ollama",
            "api_key": "",
            "model": "llama3:8b"
        },
        "SAB1": {
            "provider": "Ollama",
            "api_key": "",
            "model": "llama3:8b"
        },
        "SAB2": {
            "provider": "Ollama",
            "api_key": "",
            "model": "llama3:8b"
        },
        "SAB3": {
            "provider": "Ollama",
            "api_key": "",
            "model": "llama3:8b"
        }
    }


def save_config(config: Dict[str, Any], config_file: str = "config/config.json") -> bool:
    """Save configuration to file."""
    config_path = Path(config_file)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False


def get_pre_instructions(instructions_file: str = "config/pre_instructions.json") -> Dict[str, str]:
    """Load pre-instructions from file."""
    instructions_path = Path(instructions_file)

    if not instructions_path.exists():
        return _get_default_pre_instructions()

    try:
        with open(instructions_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return _get_default_pre_instructions()


def _get_default_pre_instructions() -> Dict[str, str]:
    """Return default pre-instructions."""
    return {
        "MAB": "You are NeuroDesk's Main Agent Brain — the orchestrator and manager of a multi-agent digital marketing team.",
        "SAB1": "You are SAB1 — the Market Research Analyst of NeuroDesk.",
        "SAB2": "You are SAB2 — the Marketing Strategy Specialist of NeuroDesk.",
        "SAB3": "You are SAB3 — the Senior Copywriter of NeuroDesk."
    }


def save_pre_instructions(instructions: Dict[str, str], instructions_file: str = "config/pre_instructions.json") -> bool:
    """Save pre-instructions to file."""
    instructions_path = Path(instructions_file)
    instructions_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(instructions_path, 'w') as f:
            json.dump(instructions, f, indent=2)
        return True
    except IOError:
        return False
