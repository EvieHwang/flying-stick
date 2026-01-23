"""
Configuration loading for guardrails.

Loads guardrails from YAML configuration files.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .models import GuardrailConfig, VALID_STAGES, VALID_THREATS, VALID_RESPONSES


logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def load_guardrails(
    config_path: str | None = None,
    config_dict: dict | None = None,
) -> dict[str, dict[str, list[GuardrailConfig]]]:
    """
    Load guardrails configuration.

    Returns a nested dict: agent -> stage -> list of GuardrailConfig

    Args:
        config_path: Path to YAML configuration file
        config_dict: Configuration dictionary (takes precedence over path)

    Returns:
        Dictionary mapping agent names to stage dictionaries,
        where each stage contains a list of GuardrailConfig objects.
        Structure: {agent: {stage: [GuardrailConfig, ...]}}
    """
    if config_dict is not None:
        return _parse_config(config_dict)

    if config_path is None:
        config_path = os.environ.get(
            "GUARDRAILS_CONFIG_PATH",
            "guardrails.yaml"
        )

    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Guardrails config not found at {config_path}, using empty config")
        return {}

    try:
        with open(path) as f:
            config_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"Invalid YAML in {config_path}: {e}")

    if config_dict is None:
        return {}

    return _parse_config(config_dict)


def _parse_config(
    config: dict[str, Any],
) -> dict[str, dict[str, list[GuardrailConfig]]]:
    """Parse configuration dictionary into GuardrailConfig objects."""
    result: dict[str, dict[str, list[GuardrailConfig]]] = {}

    # Load global guardrails
    global_guardrails: dict[str, list[GuardrailConfig]] = {
        "input": [],
        "behavioral": [],
        "output": [],
    }

    if "global" in config:
        global_section = config["global"]
        for stage in VALID_STAGES:
            if stage in global_section:
                for g_dict in global_section[stage]:
                    guardrail = _parse_guardrail(g_dict, stage)
                    global_guardrails[stage].append(guardrail)

    # Load agent-specific guardrails
    agents_section = config.get("agents", {})
    for agent_name, agent_config in agents_section.items():
        result[agent_name] = {
            "input": list(global_guardrails["input"]),
            "behavioral": list(global_guardrails["behavioral"]),
            "output": list(global_guardrails["output"]),
        }

        for stage in VALID_STAGES:
            if stage in agent_config:
                for g_dict in agent_config[stage]:
                    guardrail = _parse_guardrail(g_dict, stage)
                    result[agent_name][stage].append(guardrail)

    # If we have global guardrails but no agents, create a "default" agent
    if not result and any(global_guardrails.values()):
        result["default"] = global_guardrails

    return result


def _parse_guardrail(g_dict: dict[str, Any], stage: str) -> GuardrailConfig:
    """Parse a single guardrail dictionary into a GuardrailConfig."""
    # Required fields
    required_fields = ["name", "threat", "rule", "response"]
    for field in required_fields:
        if field not in g_dict:
            raise ConfigValidationError(
                f"Guardrail missing required field '{field}': {g_dict}"
            )

    # Validate threat
    threat = g_dict["threat"]
    if threat not in VALID_THREATS:
        raise ConfigValidationError(
            f"Invalid threat '{threat}' in guardrail '{g_dict.get('name')}'. "
            f"Must be one of: {VALID_THREATS}"
        )

    # Validate response
    response = g_dict["response"]
    if response not in VALID_RESPONSES:
        raise ConfigValidationError(
            f"Invalid response '{response}' in guardrail '{g_dict.get('name')}'. "
            f"Must be one of: {VALID_RESPONSES}"
        )

    # Create config
    try:
        return GuardrailConfig(
            name=g_dict["name"],
            stage=stage,
            threat=threat,
            detection=g_dict.get("detection", "deterministic"),
            rule=g_dict["rule"],
            response=response,
            enabled=g_dict.get("enabled", True),
            error_message=g_dict.get("error_message"),
            fallback_value=g_dict.get("fallback_value"),
            truncate_to=g_dict.get("truncate_to"),
            suffix=g_dict.get("suffix", "..."),
        )
    except ValueError as e:
        raise ConfigValidationError(str(e))


def validate_config(config_path: str) -> list[str]:
    """
    Validate a configuration file and return any errors.

    Returns:
        List of error messages. Empty list if valid.
    """
    errors = []

    try:
        path = Path(config_path)
        if not path.exists():
            return [f"Configuration file not found: {config_path}"]

        with open(path) as f:
            config = yaml.safe_load(f)

        if config is None:
            return ["Configuration file is empty"]

        # Try to parse (will raise on errors)
        load_guardrails(config_dict=config)

    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
    except ConfigValidationError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected error: {e}")

    return errors


def get_settings(config_path: str | None = None) -> dict[str, Any]:
    """
    Get settings section from configuration.

    Returns default settings if not specified.
    """
    default_settings = {
        "fail_open": False,
        "log_all_activations": True,
        "attach_to_traces": True,
    }

    if config_path is None:
        config_path = os.environ.get("GUARDRAILS_CONFIG_PATH", "guardrails.yaml")

    path = Path(config_path)
    if not path.exists():
        return default_settings

    try:
        with open(path) as f:
            config = yaml.safe_load(f) or {}
        settings = config.get("settings", {})
        return {**default_settings, **settings}
    except Exception:
        return default_settings
