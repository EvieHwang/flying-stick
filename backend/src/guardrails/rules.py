"""
Built-in guardrail rules and rule parser.

This module provides deterministic rule implementations and a safe rule parser
that does NOT use eval().
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from .models import GuardrailContext


# Registry of built-in rules
_rules: dict[str, Callable] = {}


def register_rule(name: str):
    """Decorator to register a rule function."""
    def decorator(fn: Callable) -> Callable:
        _rules[name] = fn
        return fn
    return decorator


def get_rule(name: str) -> Callable | None:
    """Get a registered rule by name."""
    return _rules.get(name)


def list_rules() -> list[str]:
    """List all registered rule names."""
    return list(_rules.keys())


# =============================================================================
# Input/Output Rules (work on request/output data)
# =============================================================================


@register_rule("max_length")
def max_length(value: Any, limit: int) -> bool:
    """Check if string length is within limit."""
    if value is None:
        return True
    return len(str(value)) <= limit


@register_rule("min_length")
def min_length(value: Any, limit: int) -> bool:
    """Check if string has minimum length."""
    if value is None:
        return False
    return len(str(value).strip()) >= limit


@register_rule("required")
def required(value: Any) -> bool:
    """Check if value exists and is not empty."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict)) and not value:
        return False
    return True


@register_rule("valid_json")
def valid_json(value: Any) -> bool:
    """Check if value is valid JSON (or already parsed)."""
    if value is None:
        return False
    if isinstance(value, (dict, list)):
        return True
    if isinstance(value, str):
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    return False


@register_rule("valid_enum")
def valid_enum(value: Any, allowed: list[Any]) -> bool:
    """Check if value is in allowed set."""
    return value in allowed


@register_rule("in_range")
def in_range(value: Any, min_val: float, max_val: float) -> bool:
    """Check if numeric value is in range (inclusive)."""
    if value is None:
        return False
    try:
        num = float(value)
        return min_val <= num <= max_val
    except (TypeError, ValueError):
        return False


@register_rule("required_fields")
def required_fields(obj: Any, fields: list[str]) -> bool:
    """Check if all required fields are present and non-empty."""
    if not isinstance(obj, dict):
        return False
    for field_name in fields:
        value = obj.get(field_name)
        if not required(value):
            return False
    return True


@register_rule("matches_pattern")
def matches_pattern(value: Any, pattern: str) -> bool:
    """Check if value matches regex pattern."""
    if value is None:
        return False
    try:
        return bool(re.match(pattern, str(value)))
    except re.error:
        return False


# =============================================================================
# Behavioral Rules (work on GuardrailContext)
# =============================================================================


@register_rule("max_tool_calls")
def max_tool_calls(context: GuardrailContext, limit: int) -> bool:
    """Check if tool call count is within limit."""
    return context.tool_call_count <= limit


@register_rule("max_iterations")
def max_iterations(context: GuardrailContext, limit: int) -> bool:
    """Check if iteration count is within limit."""
    return context.iteration_count <= limit


@register_rule("allowed_tools")
def allowed_tools(context: GuardrailContext, allowed: list[str]) -> bool:
    """Check if all tool calls are in allowed list."""
    if not context.tool_calls:
        return True
    return all(tool in allowed for tool in context.tool_calls)


@register_rule("timeout")
def timeout(context: GuardrailContext, limit_ms: int) -> bool:
    """Check if execution time is within limit."""
    return context.elapsed_ms() <= limit_ms


# =============================================================================
# Rule Parser
# =============================================================================


class RuleParseError(Exception):
    """Raised when a rule string cannot be parsed."""
    pass


def _get_nested_value(obj: Any, path: str) -> Any:
    """
    Get a nested value using dot notation.

    Example: _get_nested_value({"a": {"b": 1}}, "a.b") -> 1
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current


def _parse_literal(token: str) -> Any:
    """Parse a literal value (string, number, list, bool, None)."""
    token = token.strip()

    # None/null
    if token.lower() in ("none", "null"):
        return None

    # Boolean
    if token.lower() == "true":
        return True
    if token.lower() == "false":
        return False

    # Number (int or float)
    try:
        if "." in token:
            return float(token)
        return int(token)
    except ValueError:
        pass

    # String (quoted)
    if (token.startswith("'") and token.endswith("'")) or \
       (token.startswith('"') and token.endswith('"')):
        return token[1:-1]

    # List
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        if not inner:
            return []
        # Simple list parsing (doesn't handle nested lists)
        items = []
        for item in inner.split(","):
            items.append(_parse_literal(item.strip()))
        return items

    # If nothing else, treat as a path reference
    return {"__path__": token}


def _tokenize_args(args_str: str) -> list[str]:
    """
    Tokenize function arguments, respecting brackets and quotes.

    Example: "request.body.description, 2000" -> ["request.body.description", "2000"]
    """
    args = []
    current = ""
    depth = 0
    in_string = None

    for char in args_str:
        if char in ('"', "'") and in_string is None:
            in_string = char
            current += char
        elif char == in_string:
            in_string = None
            current += char
        elif in_string:
            current += char
        elif char == "[":
            depth += 1
            current += char
        elif char == "]":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        args.append(current.strip())

    return args


def evaluate_rule(
    rule: str,
    context: dict[str, Any],
) -> bool:
    """
    Evaluate a rule string against a context.

    Supports two formats:
    1. Function call: function_name(arg1, arg2)
    2. Comparison: field > value, field == value, etc.

    Args:
        rule: The rule string to evaluate
        context: Dictionary containing 'request', 'output', 'context' (GuardrailContext)

    Returns:
        True if the rule passes, False if it fails

    Raises:
        RuleParseError: If the rule cannot be parsed
    """
    rule = rule.strip()

    # Try to parse as function call FIRST (to avoid matching "in" within function names)
    func_match = re.match(r"^(\w+)\s*\(\s*(.*)\s*\)$", rule, re.DOTALL)
    if func_match:
        func_name = func_match.group(1)
        args_str = func_match.group(2)
        return _evaluate_function(func_name, args_str, context)

    # Try to parse as comparison (only if not a function call)
    # Use word boundaries for operators to avoid matching within identifiers
    comparison_match = re.match(
        r"^(.+?)\s*(==|!=|>=|<=|>|<|\bin\b|\bnot\s+in\b)\s*(.+)$",
        rule,
        re.IGNORECASE
    )
    if comparison_match:
        return _evaluate_comparison(
            comparison_match.group(1).strip(),
            comparison_match.group(2).strip().lower().replace(" ", "_"),
            comparison_match.group(3).strip(),
            context,
        )

    raise RuleParseError(f"Cannot parse rule: {rule}")


def _resolve_value(token: Any, context: dict[str, Any]) -> Any:
    """Resolve a token to its actual value."""
    if isinstance(token, dict) and "__path__" in token:
        path = token["__path__"]
        return _get_nested_value(context, path)
    return token


def _evaluate_comparison(
    left: str,
    operator: str,
    right: str,
    context: dict[str, Any],
) -> bool:
    """Evaluate a comparison expression."""
    left_val = _resolve_value(_parse_literal(left), context)
    right_val = _resolve_value(_parse_literal(right), context)

    # Handle None values gracefully
    if operator == "==":
        return left_val == right_val
    elif operator == "!=":
        return left_val != right_val
    elif operator in (">", "<", ">=", "<="):
        # Comparison with None is always False
        if left_val is None or right_val is None:
            return False
        if operator == ">":
            return left_val > right_val
        elif operator == "<":
            return left_val < right_val
        elif operator == ">=":
            return left_val >= right_val
        elif operator == "<=":
            return left_val <= right_val
    elif operator == "in":
        # If container is None, return False
        if right_val is None:
            return False
        return left_val in right_val
    elif operator == "not_in":
        # If container is None, return True (not in nothing)
        if right_val is None:
            return True
        return left_val not in right_val
    else:
        raise RuleParseError(f"Unknown operator: {operator}")
    return False


def _evaluate_function(
    func_name: str,
    args_str: str,
    context: dict[str, Any],
) -> bool:
    """Evaluate a function call."""
    rule_fn = get_rule(func_name)
    if rule_fn is None:
        raise RuleParseError(f"Unknown rule function: {func_name}")

    # Parse arguments
    args_tokens = _tokenize_args(args_str)
    args = []
    for token in args_tokens:
        parsed = _parse_literal(token)
        resolved = _resolve_value(parsed, context)
        args.append(resolved)

    # Call the rule function
    try:
        return rule_fn(*args)
    except TypeError as e:
        raise RuleParseError(f"Error calling {func_name}: {e}")
