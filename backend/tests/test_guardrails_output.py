"""
Tests for output stage guardrails.
"""

import pytest

from src.guardrails import (
    GuardrailEngine,
    GuardrailBlockError,
    truncate_string,
    truncate_field,
    apply_fallback,
)


class TestOutputGuardrails:
    """Tests for output stage guardrail checking."""

    def test_output_guardrails_pass(self):
        """Output guardrails should pass for valid output."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "valid_category",
                            "threat": "quality",
                            "rule": "valid_enum(output.category, ['A', 'B', 'C'])",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        output = {"category": "A", "value": 123}
        modified, results = engine.check_output("test", {}, output)

        assert modified == output
        assert len(results) == 1
        assert results[0].triggered is False

    def test_output_guardrails_block(self):
        """Output guardrails should block invalid output."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "valid_category",
                            "threat": "quality",
                            "rule": "valid_enum(output.category, ['A', 'B', 'C'])",
                            "response": "block",
                            "error_message": "Invalid category",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        output = {"category": "INVALID"}

        with pytest.raises(GuardrailBlockError) as exc_info:
            engine.check_output("test", {}, output)

        assert exc_info.value.guardrail_name == "valid_category"
        assert exc_info.value.stage == "output"
        assert "Invalid category" in exc_info.value.message

    def test_output_block_http_status(self):
        """Output block should return 500 status."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "check",
                            "threat": "quality",
                            "rule": "required(output.missing)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        with pytest.raises(GuardrailBlockError) as exc_info:
            engine.check_output("test", {}, {"other": "field"})

        assert exc_info.value.to_http_status() == 500

    def test_output_truncate(self):
        """Truncate response should shorten output."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "truncate_text",
                            "threat": "scope",
                            "rule": "max_length(output.text, 10)",
                            "response": "truncate",
                            "truncate_to": 10,
                            "suffix": "...",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        output = {"text": "this is a very long text that should be truncated"}
        modified, results = engine.check_output("test", {}, output)

        assert len(modified["text"]) == 13  # 10 + "..."
        assert modified["text"].endswith("...")
        assert results[0].triggered is True
        assert results[0].response == "truncate"
        assert results[0].details["original_length"] == 49

    def test_output_fallback(self):
        """Fallback response should substitute default value."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "fallback_confidence",
                            "threat": "quality",
                            "rule": "valid_enum(output.confidence, ['HIGH', 'MEDIUM', 'LOW'])",
                            "response": "fallback",
                            "fallback_value": "MEDIUM",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        output = {"confidence": "INVALID_VALUE"}
        modified, results = engine.check_output("test", {}, output)

        assert modified["confidence"] == "MEDIUM"
        assert results[0].triggered is True
        assert results[0].response == "fallback"
        assert results[0].details["original_value"] == "INVALID_VALUE"
        assert results[0].details["fallback_value"] == "MEDIUM"

    def test_output_flag(self):
        """Flag response should log but not modify."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "flag_suspicious",
                            "threat": "security",
                            "rule": "max_length(output.text, 10)",
                            "response": "flag",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        output = {"text": "this is flagged but not modified"}
        modified, results = engine.check_output("test", {}, output)

        assert modified == output  # Unchanged
        assert results[0].triggered is True
        assert results[0].response == "flag"

    def test_output_not_mutated(self):
        """Original output should not be mutated."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "truncate",
                            "threat": "scope",
                            "rule": "max_length(output.text, 5)",
                            "response": "truncate",
                            "truncate_to": 5,
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        original = {"text": "long text here"}
        original_copy = original["text"]  # Save original value

        modified, _ = engine.check_output("test", {}, original)

        # Original should be unchanged
        assert original["text"] == original_copy
        # Modified should be different
        assert modified["text"] != original["text"]

    def test_multiple_output_guardrails(self):
        """Multiple output guardrails should all be applied."""
        config = {
            "agents": {
                "test": {
                    "output": [
                        {
                            "name": "check1",
                            "threat": "quality",
                            "rule": "required(output.field1)",
                            "response": "flag",
                        },
                        {
                            "name": "truncate1",
                            "threat": "scope",
                            "rule": "max_length(output.text, 10)",
                            "response": "truncate",
                            "truncate_to": 10,
                        },
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        output = {"text": "very long text", "field1": "value"}
        modified, results = engine.check_output("test", {}, output)

        assert len(results) == 2
        assert results[0].triggered is False  # field1 exists
        assert results[1].triggered is True  # text too long
        assert len(modified["text"]) == 13  # truncated


class TestTruncateHelpers:
    """Tests for truncation helper functions."""

    def test_truncate_string(self):
        """truncate_string should truncate long strings."""
        result, was_truncated = truncate_string("hello world", 5)
        assert result == "hello..."
        assert was_truncated is True

    def test_truncate_string_short(self):
        """truncate_string should not modify short strings."""
        result, was_truncated = truncate_string("hi", 10)
        assert result == "hi"
        assert was_truncated is False

    def test_truncate_string_custom_suffix(self):
        """truncate_string should use custom suffix."""
        result, _ = truncate_string("hello world", 5, suffix="[...]")
        assert result == "hello[...]"

    def test_truncate_field(self):
        """truncate_field should truncate nested field."""
        obj = {"nested": {"text": "long text here"}}
        result, original_length = truncate_field(obj, "nested.text", 4)
        assert result["nested"]["text"] == "long..."
        assert original_length == 14

    def test_truncate_field_short(self):
        """truncate_field should not modify short fields."""
        obj = {"text": "short"}
        result, original_length = truncate_field(obj, "text", 100)
        assert result["text"] == "short"
        assert original_length is None


class TestFallbackHelper:
    """Tests for fallback helper function."""

    def test_apply_fallback(self):
        """apply_fallback should substitute value."""
        obj = {"status": "invalid"}
        result, original = apply_fallback(obj, "status", "default")
        assert result["status"] == "default"
        assert original == "invalid"

    def test_apply_fallback_nested(self):
        """apply_fallback should work with nested paths."""
        obj = {"response": {"code": "invalid"}}
        result, original = apply_fallback(obj, "response.code", "OK")
        assert result["response"]["code"] == "OK"
        assert original == "invalid"

    def test_apply_fallback_creates_path(self):
        """apply_fallback should create missing path."""
        obj = {}
        result, original = apply_fallback(obj, "new_field", "value")
        assert result["new_field"] == "value"
        assert original is None


class TestEngineSummary:
    """Tests for engine summary functionality."""

    def test_summary_tracks_all_stages(self):
        """Summary should track results from all stages."""
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
                    "output": [
                        {
                            "name": "output_check",
                            "threat": "quality",
                            "rule": "required(output.result)",
                            "response": "flag",
                        }
                    ],
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        engine.check_input("test", {"text": "input"})
        engine.check_output("test", {}, {"result": "value"})

        summary = engine.get_summary()
        assert len(summary["input"]) == 1
        assert len(summary["output"]) == 1
        assert summary["blocked"] is False

    def test_summary_reset(self):
        """Reset should clear summary."""
        config = {
            "agents": {
                "test": {
                    "input": [
                        {
                            "name": "check",
                            "threat": "cost",
                            "rule": "max_length(request.text, 100)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)

        engine.check_input("test", {"text": "input"})
        assert len(engine.get_summary()["input"]) == 1

        engine.reset()
        assert len(engine.get_summary()["input"]) == 0
