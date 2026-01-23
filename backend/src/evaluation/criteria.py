"""
Evaluation criteria configuration loader.

Loads and validates evaluation criteria from evaluation.yaml files.
"""

import os
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator, ValidationError

from .models import EvaluationCriterion, Pillar, Layer


logger = logging.getLogger(__name__)


class CriterionConfig(BaseModel):
    """Pydantic model for validating criterion configuration."""
    name: str
    pillar: str
    layer: int
    signal: str
    threshold: str
    description: str | None = None
    warning: str | None = None
    enabled: bool = True
    evaluation_method: str | None = None
    prompt: str | None = None
    sample_rate: float = 1.0

    @field_validator("pillar")
    @classmethod
    def validate_pillar(cls, v: str) -> str:
        valid = ["effectiveness", "efficiency", "reliability", "trustworthiness"]
        if v.lower() not in valid:
            raise ValueError(f"Invalid pillar '{v}'. Must be one of: {valid}")
        return v.lower()

    @field_validator("layer")
    @classmethod
    def validate_layer(cls, v: int) -> int:
        if v not in [1, 2, 3]:
            raise ValueError(f"Invalid layer {v}. Must be 1, 2, or 3")
        return v

    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"sample_rate must be between 0.0 and 1.0, got {v}")
        return v

    def to_criterion(self) -> EvaluationCriterion:
        """Convert to EvaluationCriterion dataclass."""
        return EvaluationCriterion(
            name=self.name,
            pillar=self.pillar,  # type: ignore
            layer=self.layer,  # type: ignore
            signal=self.signal,
            threshold=self.threshold,
            description=self.description,
            warning=self.warning,
            enabled=self.enabled,
            evaluation_method=self.evaluation_method,
            prompt=self.prompt,
            sample_rate=self.sample_rate,
        )


class AgentConfig(BaseModel):
    """Configuration for a single agent's evaluation criteria."""
    description: str | None = None
    criteria: list[CriterionConfig] = []


class EvaluationConfig(BaseModel):
    """Root configuration for evaluation.yaml."""
    version: str = "1.0"
    agents: dict[str, AgentConfig] = {}

    # Global criteria applied to all agents
    global_criteria: list[CriterionConfig] = []


def load_criteria(
    config_path: str | Path | None = None,
    config_dict: dict | None = None
) -> dict[str, list[EvaluationCriterion]]:
    """
    Load evaluation criteria from YAML file or dict.

    Args:
        config_path: Path to evaluation.yaml (default: backend/evaluation.yaml)
        config_dict: Optional dict to use instead of file

    Returns:
        Dict mapping agent names to lists of EvaluationCriterion

    Raises:
        ValueError: If configuration is invalid
    """
    # Load from dict if provided
    if config_dict is not None:
        return _parse_config(config_dict)

    # Determine config path
    if config_path is None:
        # Look in standard locations
        candidates = [
            Path("evaluation.yaml"),
            Path("backend/evaluation.yaml"),
            Path(__file__).parent.parent.parent / "evaluation.yaml",
        ]
        config_path = None
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break
    else:
        config_path = Path(config_path)

    # Return empty if no config found (graceful fallback)
    if config_path is None or not config_path.exists():
        logger.info("No evaluation.yaml found, running without evaluation criteria")
        return {}

    # Load and parse YAML
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}") from e

    if data is None:
        return {}

    return _parse_config(data)


def _parse_config(data: dict[str, Any]) -> dict[str, list[EvaluationCriterion]]:
    """Parse and validate configuration dict."""
    try:
        config = EvaluationConfig(**data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"  {loc}: {error['msg']}")
        raise ValueError(f"Invalid evaluation config:\n" + "\n".join(errors)) from e

    result: dict[str, list[EvaluationCriterion]] = {}

    # Convert global criteria
    global_criteria = [c.to_criterion() for c in config.global_criteria]

    # Process each agent
    for agent_name, agent_config in config.agents.items():
        criteria = [c.to_criterion() for c in agent_config.criteria]
        # Add global criteria to each agent
        result[agent_name] = global_criteria + criteria

    # If only global criteria defined, add to "default" agent
    if global_criteria and not config.agents:
        result["default"] = global_criteria

    return result


def validate_config(config_path: str | Path) -> list[str]:
    """
    Validate an evaluation.yaml file and return any errors.

    Args:
        config_path: Path to evaluation.yaml

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    try:
        load_criteria(config_path)
    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected error: {e}")

    return errors
