"""
Signal extractors for evaluation criteria.

Signals are observable values extracted from traces that can be evaluated
against thresholds. This module provides built-in extractors and a registry
for custom signals.
"""

import json
import re
from typing import Any, Callable

from .models import Trace


# Registry of custom signal extractors
_custom_signals: dict[str, Callable[[Trace], Any]] = {}


def register_signal(name: str):
    """Decorator to register a custom signal extractor."""
    def decorator(func: Callable[[Trace], Any]):
        _custom_signals[name] = func
        return func
    return decorator


def extract_signal(trace: Trace, signal: str) -> Any:
    """
    Extract a signal value from a trace.

    Supports:
    - Dot notation for nested fields: "metrics.duration_ms"
    - Built-in signals: "duration_ms", "total_tokens", etc.
    - Custom registered signals
    - Special signals: "response.format" (JSON validation)

    Args:
        trace: The trace to extract from
        signal: Signal specification (field path or signal name)

    Returns:
        Extracted value, or None if not found
    """
    # Check custom signals first
    if signal in _custom_signals:
        try:
            return _custom_signals[signal](trace)
        except Exception:
            return None

    # Handle special built-in signals
    if signal == "response.format":
        return _check_response_format(trace)

    if signal == "error":
        return trace.error

    # Handle shorthand for common metrics
    shorthand_map = {
        "duration_ms": "metrics.duration_ms",
        "input_tokens": "metrics.input_tokens",
        "output_tokens": "metrics.output_tokens",
        "total_tokens": "metrics.total_tokens",
    }
    if signal in shorthand_map:
        signal = shorthand_map[signal]

    # Handle dot notation for nested fields
    return _extract_nested(trace, signal)


def _extract_nested(obj: Any, path: str) -> Any:
    """Extract a nested value using dot notation."""
    parts = path.split(".")
    current = obj

    for part in parts:
        if current is None:
            return None

        # Handle dataclass attributes
        if hasattr(current, part):
            current = getattr(current, part)
        # Handle dict keys
        elif isinstance(current, dict) and part in current:
            current = current[part]
        # Handle list index
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if 0 <= idx < len(current) else None
        else:
            return None

    return current


def _check_response_format(trace: Trace) -> dict[str, Any]:
    """
    Check if the response output is valid JSON.

    Returns a dict with validation results:
    - is_json: bool - whether output parses as JSON
    - has_fields: list - fields present if JSON object
    - error: str - parse error if not valid JSON
    """
    if trace.response is None:
        return {"is_json": False, "error": "No response"}

    output = trace.response.output

    # Already a dict (structured output)
    if isinstance(output, dict):
        return {
            "is_json": True,
            "has_fields": list(output.keys()),
            "error": None
        }

    # Try to parse as JSON
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
            fields = list(parsed.keys()) if isinstance(parsed, dict) else []
            return {
                "is_json": True,
                "has_fields": fields,
                "error": None
            }
        except json.JSONDecodeError as e:
            return {
                "is_json": False,
                "has_fields": [],
                "error": str(e)
            }

    return {"is_json": False, "error": f"Unexpected output type: {type(output)}"}


# Built-in custom signals

@register_signal("tool_count")
def _signal_tool_count(trace: Trace) -> int:
    """Count of tool calls in the trace."""
    return len(trace.tool_calls)


@register_signal("has_error")
def _signal_has_error(trace: Trace) -> bool:
    """Whether the trace has an error."""
    return trace.error is not None


@register_signal("response_length")
def _signal_response_length(trace: Trace) -> int:
    """Length of response output in characters."""
    if trace.response is None:
        return 0
    output = trace.response.output
    if isinstance(output, str):
        return len(output)
    elif isinstance(output, dict):
        return len(json.dumps(output))
    return 0


@register_signal("tokens_per_second")
def _signal_tokens_per_second(trace: Trace) -> float:
    """Output tokens per second (throughput)."""
    if trace.metrics is None or trace.metrics.duration_ms == 0:
        return 0.0
    return (trace.metrics.output_tokens / trace.metrics.duration_ms) * 1000
