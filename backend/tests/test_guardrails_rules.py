"""
Tests for guardrails rules and rule parser.
"""

import pytest

from src.guardrails import (
    evaluate_rule,
    RuleParseError,
    GuardrailContext,
)
from src.guardrails.rules import (
    max_length,
    min_length,
    required,
    valid_json,
    valid_enum,
    in_range,
    required_fields,
    max_tool_calls,
    max_iterations,
    allowed_tools,
)


class TestBuiltInRules:
    """Tests for built-in rule functions."""

    def test_max_length_pass(self):
        """max_length should pass when under limit."""
        assert max_length("hello", 10) is True
        assert max_length("hello", 5) is True

    def test_max_length_fail(self):
        """max_length should fail when over limit."""
        assert max_length("hello world", 5) is False

    def test_max_length_none(self):
        """max_length should pass for None."""
        assert max_length(None, 10) is True

    def test_min_length_pass(self):
        """min_length should pass when over minimum."""
        assert min_length("hello", 3) is True
        assert min_length("hello world", 5) is True

    def test_min_length_fail(self):
        """min_length should fail when under minimum."""
        assert min_length("hi", 5) is False
        assert min_length("", 1) is False

    def test_min_length_strips_whitespace(self):
        """min_length should strip whitespace before checking."""
        assert min_length("  hi  ", 2) is True
        assert min_length("   ", 1) is False

    def test_min_length_none(self):
        """min_length should fail for None."""
        assert min_length(None, 1) is False

    def test_required_pass(self):
        """required should pass for truthy values."""
        assert required("hello") is True
        assert required(123) is True
        assert required({"key": "value"}) is True
        assert required([1, 2, 3]) is True

    def test_required_fail(self):
        """required should fail for falsy values."""
        assert required(None) is False
        assert required("") is False
        assert required("   ") is False
        assert required([]) is False
        assert required({}) is False

    def test_valid_json_pass(self):
        """valid_json should pass for valid JSON."""
        assert valid_json('{"key": "value"}') is True
        assert valid_json("[1, 2, 3]") is True
        assert valid_json({"already": "parsed"}) is True
        assert valid_json([1, 2, 3]) is True

    def test_valid_json_fail(self):
        """valid_json should fail for invalid JSON."""
        assert valid_json("not json") is False
        assert valid_json("{invalid}") is False
        assert valid_json(None) is False

    def test_valid_enum_pass(self):
        """valid_enum should pass for values in list."""
        assert valid_enum("A", ["A", "B", "C"]) is True
        assert valid_enum(1, [1, 2, 3]) is True

    def test_valid_enum_fail(self):
        """valid_enum should fail for values not in list."""
        assert valid_enum("D", ["A", "B", "C"]) is False
        assert valid_enum(4, [1, 2, 3]) is False

    def test_in_range_pass(self):
        """in_range should pass for values in range."""
        assert in_range(5, 0, 10) is True
        assert in_range(0, 0, 10) is True
        assert in_range(10, 0, 10) is True
        assert in_range(5.5, 0, 10) is True

    def test_in_range_fail(self):
        """in_range should fail for values out of range."""
        assert in_range(-1, 0, 10) is False
        assert in_range(11, 0, 10) is False
        assert in_range("not a number", 0, 10) is False
        assert in_range(None, 0, 10) is False

    def test_required_fields_pass(self):
        """required_fields should pass when all fields present."""
        obj = {"a": 1, "b": 2, "c": 3}
        assert required_fields(obj, ["a", "b"]) is True

    def test_required_fields_fail(self):
        """required_fields should fail when fields missing."""
        obj = {"a": 1}
        assert required_fields(obj, ["a", "b"]) is False
        assert required_fields("not a dict", ["a"]) is False


class TestBehavioralRules:
    """Tests for behavioral stage rules."""

    def test_max_tool_calls_pass(self):
        """max_tool_calls should pass when under limit."""
        ctx = GuardrailContext(agent="test", request={})
        ctx.tool_call_count = 3
        assert max_tool_calls(ctx, 5) is True

    def test_max_tool_calls_fail(self):
        """max_tool_calls should fail when over limit."""
        ctx = GuardrailContext(agent="test", request={})
        ctx.tool_call_count = 6
        assert max_tool_calls(ctx, 5) is False

    def test_max_iterations_pass(self):
        """max_iterations should pass when under limit."""
        ctx = GuardrailContext(agent="test", request={})
        ctx.iteration_count = 2
        assert max_iterations(ctx, 5) is True

    def test_max_iterations_fail(self):
        """max_iterations should fail when over limit."""
        ctx = GuardrailContext(agent="test", request={})
        ctx.iteration_count = 10
        assert max_iterations(ctx, 5) is False

    def test_allowed_tools_pass(self):
        """allowed_tools should pass for allowed tools."""
        ctx = GuardrailContext(agent="test", request={})
        ctx.tool_calls = ["tool_a", "tool_b"]
        assert allowed_tools(ctx, ["tool_a", "tool_b", "tool_c"]) is True

    def test_allowed_tools_fail(self):
        """allowed_tools should fail for unknown tools."""
        ctx = GuardrailContext(agent="test", request={})
        ctx.tool_calls = ["tool_a", "unknown_tool"]
        assert allowed_tools(ctx, ["tool_a", "tool_b"]) is False

    def test_allowed_tools_empty(self):
        """allowed_tools should pass when no tools called."""
        ctx = GuardrailContext(agent="test", request={})
        ctx.tool_calls = []
        assert allowed_tools(ctx, ["tool_a"]) is True


class TestRuleParser:
    """Tests for the rule parser."""

    def test_parse_function_call(self):
        """Should parse function-style rules."""
        context = {"request": {"text": "hello"}}
        assert evaluate_rule("max_length(request.text, 10)", context) is True
        assert evaluate_rule("max_length(request.text, 3)", context) is False

    def test_parse_nested_path(self):
        """Should handle nested dot notation paths."""
        context = {"request": {"body": {"nested": {"value": "test"}}}}
        assert evaluate_rule("max_length(request.body.nested.value, 10)", context) is True

    def test_parse_list_argument(self):
        """Should parse list arguments."""
        context = {"output": {"category": "A"}}
        assert evaluate_rule("valid_enum(output.category, ['A', 'B', 'C'])", context) is True
        assert evaluate_rule("valid_enum(output.category, ['X', 'Y', 'Z'])", context) is False

    def test_parse_numeric_argument(self):
        """Should parse numeric arguments."""
        context = {"output": {"score": 5}}
        assert evaluate_rule("in_range(output.score, 0, 10)", context) is True
        assert evaluate_rule("in_range(output.score, 0.0, 10.5)", context) is True

    def test_parse_comparison(self):
        """Should parse comparison expressions."""
        context = {"output": {"count": 5}}
        assert evaluate_rule("output.count > 3", context) is True
        assert evaluate_rule("output.count < 3", context) is False
        assert evaluate_rule("output.count == 5", context) is True
        assert evaluate_rule("output.count != 5", context) is False
        assert evaluate_rule("output.count >= 5", context) is True
        assert evaluate_rule("output.count <= 5", context) is True

    def test_parse_in_operator(self):
        """Should parse 'in' and 'not in' operators."""
        context = {"output": {"status": "active"}}
        assert evaluate_rule("output.status in ['active', 'pending']", context) is True
        assert evaluate_rule("output.status in ['inactive']", context) is False
        assert evaluate_rule("output.status not in ['inactive']", context) is True

    def test_parse_string_literal(self):
        """Should parse string literals."""
        context = {"output": {"status": "active"}}
        assert evaluate_rule("output.status == 'active'", context) is True
        assert evaluate_rule('output.status == "active"', context) is True

    def test_parse_boolean_literal(self):
        """Should parse boolean literals."""
        context = {"output": {"enabled": True}}
        assert evaluate_rule("output.enabled == true", context) is True
        assert evaluate_rule("output.enabled == false", context) is False

    def test_parse_null_literal(self):
        """Should parse null/None literals."""
        context = {"output": {"value": None}}
        assert evaluate_rule("output.value == null", context) is True
        assert evaluate_rule("output.value == none", context) is True

    def test_invalid_rule_raises_error(self):
        """Should raise error for invalid rules."""
        context = {}
        with pytest.raises(RuleParseError):
            evaluate_rule("not a valid rule", context)

    def test_unknown_function_raises_error(self):
        """Should raise error for unknown functions."""
        context = {"request": {}}
        with pytest.raises(RuleParseError, match="Unknown rule function"):
            evaluate_rule("unknown_function(request.text)", context)

    def test_missing_value_returns_none(self):
        """Missing path should return None, not error."""
        context = {"request": {}}
        # max_length(None, 100) returns True
        assert evaluate_rule("max_length(request.missing_field, 100)", context) is True
        # required(None) returns False
        assert evaluate_rule("required(request.missing_field)", context) is False
