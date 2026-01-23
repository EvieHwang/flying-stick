"""
Tests for guardrails configuration loading.
"""

import pytest
import tempfile
import os

from src.guardrails import (
    load_guardrails,
    validate_config,
    ConfigValidationError,
)


class TestLoadGuardrails:
    """Tests for loading guardrails configuration."""

    def test_load_from_dict(self):
        """Should load guardrails from dict."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "test_guardrail",
                            "threat": "cost",
                            "rule": "max_length(request.input, 100)",
                            "response": "block",
                        }
                    ]
                }
            }
        }

        result = load_guardrails(config_dict=config)

        assert "test" in result
        assert "input" in result["test"]
        assert len(result["test"]["input"]) == 1
        assert result["test"]["input"][0].name == "test_guardrail"
        assert result["test"]["input"][0].stage == "input"
        assert result["test"]["input"][0].threat == "cost"

    def test_load_from_yaml_file(self):
        """Should load guardrails from YAML file."""
        yaml_content = """
version: "1.0"
agents:
  test_agent:
    input:
      - name: length_check
        threat: cost
        rule: "max_length(request.text, 1000)"
        response: block
        error_message: "Input too long"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                result = load_guardrails(config_path=f.name)
                assert "test_agent" in result
                assert result["test_agent"]["input"][0].name == "length_check"
            finally:
                os.unlink(f.name)

    def test_missing_file_returns_empty(self):
        """Missing config file should return empty dict."""
        result = load_guardrails(config_path="/nonexistent/path.yaml")
        assert result == {}

    def test_invalid_threat_raises_error(self):
        """Invalid threat value should raise validation error."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "bad",
                            "threat": "invalid_threat",
                            "rule": "test",
                            "response": "block",
                        }
                    ]
                }
            }
        }

        with pytest.raises(ConfigValidationError, match="Invalid threat"):
            load_guardrails(config_dict=config)

    def test_invalid_response_raises_error(self):
        """Invalid response value should raise validation error."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "bad",
                            "threat": "cost",
                            "rule": "test",
                            "response": "invalid_response",
                        }
                    ]
                }
            }
        }

        with pytest.raises(ConfigValidationError, match="Invalid response"):
            load_guardrails(config_dict=config)

    def test_global_guardrails_merged(self):
        """Global guardrails should be merged with agent-specific."""
        config = {
            "global": {
                "input": [
                    {
                        "name": "global_check",
                        "threat": "quality",
                        "rule": "valid_json(request)",
                        "response": "block",
                    }
                ]
            },
            "agents": {
                "agent1": {
                    "input": [
                        {
                            "name": "agent1_check",
                            "threat": "cost",
                            "rule": "max_length(request.text, 100)",
                            "response": "block",
                        }
                    ]
                },
                "agent2": {
                    "input": []
                },
            },
        }

        result = load_guardrails(config_dict=config)

        # Agent1 should have global + its own
        assert len(result["agent1"]["input"]) == 2
        assert result["agent1"]["input"][0].name == "global_check"
        assert result["agent1"]["input"][1].name == "agent1_check"

        # Agent2 should have global only
        assert len(result["agent2"]["input"]) == 1
        assert result["agent2"]["input"][0].name == "global_check"

    def test_truncate_requires_truncate_to(self):
        """Truncate response should require truncate_to field."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "bad",
                            "threat": "scope",
                            "rule": "max_length(output.text, 100)",
                            "response": "truncate",
                            # Missing truncate_to
                        }
                    ]
                }
            }
        }

        with pytest.raises(ConfigValidationError, match="truncate_to"):
            load_guardrails(config_dict=config)

    def test_all_stages_supported(self):
        """Should support input, behavioral, and output stages."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "input_check",
                            "threat": "cost",
                            "rule": "max_length(request.text, 100)",
                            "response": "block",
                        }
                    ],
                    "behavioral": [
                        {
                            "name": "behavioral_check",
                            "threat": "cost",
                            "rule": "max_tool_calls(context, 5)",
                            "response": "block",
                        }
                    ],
                    "output": [
                        {
                            "name": "output_check",
                            "threat": "quality",
                            "rule": "required(output.text)",
                            "response": "flag",
                        }
                    ],
                }
            }
        }

        result = load_guardrails(config_dict=config)

        assert len(result["test"]["input"]) == 1
        assert len(result["test"]["behavioral"]) == 1
        assert len(result["test"]["output"]) == 1
        assert result["test"]["input"][0].stage == "input"
        assert result["test"]["behavioral"][0].stage == "behavioral"
        assert result["test"]["output"][0].stage == "output"


class TestValidateConfig:
    """Tests for config validation."""

    def test_validate_valid_config(self):
        """Valid config should return no errors."""
        yaml_content = """
version: "1.0"
agents:
  test:
    input:
      - name: check
        threat: cost
        rule: "max_length(request.text, 100)"
        response: block
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
    input:
      - name: bad
        threat: not_a_threat
        rule: test
        response: block
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                errors = validate_config(f.name)
                assert len(errors) > 0
                assert "threat" in errors[0].lower()
            finally:
                os.unlink(f.name)
