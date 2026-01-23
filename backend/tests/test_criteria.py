"""
Tests for the criteria loading module.
"""

import pytest
import tempfile
import os

from src.evaluation.criteria import load_criteria, validate_config


class TestLoadCriteria:
    """Tests for loading evaluation criteria."""

    def test_load_from_dict(self):
        """Should load criteria from dict."""
        config = {
            "version": "1.0",
            "agents": {
                "classifier": {
                    "description": "Test agent",
                    "criteria": [
                        {
                            "name": "test_criterion",
                            "pillar": "effectiveness",
                            "layer": 1,
                            "signal": "error",
                            "threshold": "must be null",
                        }
                    ],
                }
            },
        }

        result = load_criteria(config_dict=config)

        assert "classifier" in result
        assert len(result["classifier"]) == 1
        assert result["classifier"][0].name == "test_criterion"
        assert result["classifier"][0].pillar == "effectiveness"
        assert result["classifier"][0].layer == 1

    def test_load_from_yaml_file(self):
        """Should load criteria from YAML file."""
        yaml_content = """
version: "1.0"
agents:
  test_agent:
    criteria:
      - name: latency_check
        pillar: efficiency
        layer: 2
        signal: duration_ms
        threshold: "< 5000"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                result = load_criteria(config_path=f.name)
                assert "test_agent" in result
                assert result["test_agent"][0].name == "latency_check"
            finally:
                os.unlink(f.name)

    def test_missing_file_returns_empty(self):
        """Missing config file should return empty dict (graceful fallback)."""
        result = load_criteria(config_path="/nonexistent/path.yaml")
        assert result == {}

    def test_invalid_pillar_raises_error(self):
        """Invalid pillar value should raise validation error."""
        config = {
            "agents": {
                "test": {
                    "criteria": [
                        {
                            "name": "bad",
                            "pillar": "invalid_pillar",
                            "layer": 1,
                            "signal": "error",
                            "threshold": "must be null",
                        }
                    ]
                }
            }
        }

        with pytest.raises(ValueError, match="Invalid pillar"):
            load_criteria(config_dict=config)

    def test_invalid_layer_raises_error(self):
        """Invalid layer value should raise validation error."""
        config = {
            "agents": {
                "test": {
                    "criteria": [
                        {
                            "name": "bad",
                            "pillar": "effectiveness",
                            "layer": 4,  # Invalid
                            "signal": "error",
                            "threshold": "must be null",
                        }
                    ]
                }
            }
        }

        with pytest.raises(ValueError, match="Invalid layer"):
            load_criteria(config_dict=config)

    def test_global_criteria_added_to_all_agents(self):
        """Global criteria should be added to all agents."""
        config = {
            "global_criteria": [
                {
                    "name": "global_check",
                    "pillar": "effectiveness",
                    "layer": 1,
                    "signal": "error",
                    "threshold": "must be null",
                }
            ],
            "agents": {
                "agent1": {
                    "criteria": [
                        {
                            "name": "agent1_check",
                            "pillar": "efficiency",
                            "layer": 2,
                            "signal": "duration_ms",
                            "threshold": "< 5000",
                        }
                    ]
                },
                "agent2": {"criteria": []},
            },
        }

        result = load_criteria(config_dict=config)

        # Agent1 should have global + its own
        assert len(result["agent1"]) == 2
        assert result["agent1"][0].name == "global_check"
        assert result["agent1"][1].name == "agent1_check"

        # Agent2 should have global only
        assert len(result["agent2"]) == 1
        assert result["agent2"][0].name == "global_check"

    def test_disabled_criterion_loaded(self):
        """Disabled criteria should still be loaded."""
        config = {
            "agents": {
                "test": {
                    "criteria": [
                        {
                            "name": "disabled_check",
                            "pillar": "effectiveness",
                            "layer": 1,
                            "signal": "error",
                            "threshold": "must be null",
                            "enabled": False,
                        }
                    ]
                }
            }
        }

        result = load_criteria(config_dict=config)
        assert result["test"][0].enabled is False

    def test_sample_rate_validation(self):
        """Sample rate must be between 0 and 1."""
        config = {
            "agents": {
                "test": {
                    "criteria": [
                        {
                            "name": "bad",
                            "pillar": "trustworthiness",
                            "layer": 3,
                            "signal": "output",
                            "threshold": "mean >= 4",
                            "sample_rate": 1.5,  # Invalid
                        }
                    ]
                }
            }
        }

        with pytest.raises(ValueError, match="sample_rate"):
            load_criteria(config_dict=config)


class TestValidateConfig:
    """Tests for config validation."""

    def test_validate_valid_config(self):
        """Valid config should return no errors."""
        yaml_content = """
version: "1.0"
agents:
  test:
    criteria:
      - name: check
        pillar: effectiveness
        layer: 1
        signal: error
        threshold: "must be null"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                errors = validate_config(f.name)
                assert errors == []
            finally:
                os.unlink(f.name)

    def test_validate_invalid_config(self):
        """Invalid config should return errors."""
        yaml_content = """
agents:
  test:
    criteria:
      - name: bad
        pillar: not_a_pillar
        layer: 1
        signal: error
        threshold: "must be null"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                errors = validate_config(f.name)
                assert len(errors) > 0
                assert "pillar" in errors[0].lower()
            finally:
                os.unlink(f.name)
