"""
Tests for input stage guardrails.
"""

import pytest

from src.guardrails import (
    GuardrailEngine,
    GuardrailBlockError,
    load_guardrails,
)


class TestInputGuardrails:
    """Tests for input stage guardrail checking."""

    def test_input_guardrails_pass(self):
        """Input guardrails should pass for valid input."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "max_length",
                            "threat": "cost",
                            "rule": "max_length(request.text, 100)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "short input"}
        results = engine.check_input("test", request)

        assert len(results) == 1
        assert results[0].triggered is False

    def test_input_guardrails_block(self):
        """Input guardrails should block invalid input."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "max_length",
                            "threat": "cost",
                            "rule": "max_length(request.text, 10)",
                            "response": "block",
                            "error_message": "Input too long",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "this input is way too long for the limit"}

        with pytest.raises(GuardrailBlockError) as exc_info:
            engine.check_input("test", request)

        assert exc_info.value.guardrail_name == "max_length"
        assert exc_info.value.stage == "input"
        assert "Input too long" in exc_info.value.message

    def test_input_guardrails_flag_continues(self):
        """Flag response should log but not block."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "suspicious_pattern",
                            "threat": "security",
                            "rule": "max_length(request.text, 10)",
                            "response": "flag",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "this input is flagged but not blocked"}
        results = engine.check_input("test", request)

        assert len(results) == 1
        assert results[0].triggered is True
        assert results[0].response == "flag"
        # No exception raised - request continues

    def test_multiple_input_guardrails(self):
        """Multiple input guardrails should all be checked."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "max_length",
                            "threat": "cost",
                            "rule": "max_length(request.text, 100)",
                            "response": "block",
                        },
                        {
                            "name": "min_length",
                            "threat": "quality",
                            "rule": "min_length(request.text, 5)",
                            "response": "block",
                        },
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "valid input text"}
        results = engine.check_input("test", request)

        assert len(results) == 2
        assert all(r.triggered is False for r in results)

    def test_input_guardrails_short_circuit(self):
        """Should stop checking after first block."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "first_check",
                            "threat": "cost",
                            "rule": "max_length(request.text, 5)",
                            "response": "block",
                        },
                        {
                            "name": "second_check",
                            "threat": "quality",
                            "rule": "required(request.missing)",
                            "response": "block",
                        },
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "this is too long"}

        with pytest.raises(GuardrailBlockError) as exc_info:
            engine.check_input("test", request)

        # First check should have blocked
        assert exc_info.value.guardrail_name == "first_check"

    def test_disabled_guardrails_skipped(self):
        """Disabled guardrails should not be evaluated."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "disabled_check",
                            "threat": "cost",
                            "rule": "max_length(request.text, 5)",
                            "response": "block",
                            "enabled": False,
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "this would fail if check was enabled"}
        results = engine.check_input("test", request)

        # No results because check was disabled
        assert len(results) == 0

    def test_default_agent_fallback(self):
        """Should use 'default' agent if specific agent not found."""
        config = {
            "agents": {
                "default": {
                    "input": [
                        {
                            "name": "default_check",
                            "threat": "cost",
                            "rule": "max_length(request.text, 100)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "test"}
        results = engine.check_input("unknown_agent", request)

        assert len(results) == 1
        assert results[0].name == "default_check"

    def test_block_error_http_status(self):
        """Input block should return 400 status."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "check",
                            "threat": "cost",
                            "rule": "max_length(request.text, 5)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "too long"}

        with pytest.raises(GuardrailBlockError) as exc_info:
            engine.check_input("test", request)

        assert exc_info.value.to_http_status() == 400
        response = exc_info.value.to_response()
        assert response["statusCode"] == 400

    def test_summary_tracks_input_results(self):
        """Summary should include input guardrail results."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "check1",
                            "threat": "cost",
                            "rule": "max_length(request.text, 100)",
                            "response": "block",
                        },
                        {
                            "name": "check2",
                            "threat": "quality",
                            "rule": "min_length(request.text, 3)",
                            "response": "flag",
                        },
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        request = {"text": "test input"}
        engine.check_input("test", request)

        summary = engine.get_summary()
        assert len(summary["input"]) == 2
        assert summary["blocked"] is False
