"""
Output stage guardrails.

Provides utilities for output validation and modification.
"""

from __future__ import annotations

import json
from typing import Any


def truncate_string(
    value: str,
    max_length: int,
    suffix: str = "...",
) -> tuple[str, bool]:
    """
    Truncate a string to max length.

    Args:
        value: String to truncate
        max_length: Maximum length (not including suffix)
        suffix: Suffix to append if truncated

    Returns:
        Tuple of (truncated string, was_truncated)
    """
    if len(value) <= max_length:
        return value, False

    truncated = value[:max_length] + suffix
    return truncated, True


def truncate_field(
    obj: dict[str, Any],
    field_path: str,
    max_length: int,
    suffix: str = "...",
) -> tuple[dict[str, Any], int | None]:
    """
    Truncate a nested field in a dictionary.

    Args:
        obj: Dictionary to modify (will be mutated)
        field_path: Dot-notation path to field (e.g., "response.reasoning")
        max_length: Maximum length
        suffix: Suffix to append

    Returns:
        Tuple of (modified dict, original_length or None if not truncated)
    """
    parts = field_path.split(".")
    current = obj

    # Navigate to parent
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return obj, None
        current = current[part]

    # Get and truncate the final field
    final_key = parts[-1]
    if not isinstance(current, dict) or final_key not in current:
        return obj, None

    value = current[final_key]
    if not isinstance(value, str):
        return obj, None

    original_length = len(value)
    if original_length <= max_length:
        return obj, None

    current[final_key] = value[:max_length] + suffix
    return obj, original_length


def apply_fallback(
    obj: dict[str, Any],
    field_path: str,
    fallback_value: Any,
) -> tuple[dict[str, Any], Any]:
    """
    Apply a fallback value to a nested field.

    Args:
        obj: Dictionary to modify (will be mutated)
        field_path: Dot-notation path to field
        fallback_value: Value to set

    Returns:
        Tuple of (modified dict, original_value)
    """
    parts = field_path.split(".")
    current = obj

    # Navigate to parent, creating dicts as needed
    for part in parts[:-1]:
        if not isinstance(current, dict):
            return obj, None
        if part not in current:
            current[part] = {}
        current = current[part]

    # Get original and set fallback
    final_key = parts[-1]
    if not isinstance(current, dict):
        return obj, None

    original_value = current.get(final_key)
    current[final_key] = fallback_value
    return obj, original_value


def validate_json_structure(
    value: Any,
    required_fields: list[str] | None = None,
    allowed_fields: list[str] | None = None,
) -> tuple[bool, str | None]:
    """
    Validate JSON structure.

    Args:
        value: Value to validate (should be dict)
        required_fields: List of required field names
        allowed_fields: List of allowed field names (if set, no others allowed)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, dict):
        return False, "Value is not a dictionary"

    if required_fields:
        missing = [f for f in required_fields if f not in value]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

    if allowed_fields:
        extra = [f for f in value.keys() if f not in allowed_fields]
        if extra:
            return False, f"Unexpected fields: {', '.join(extra)}"

    return True, None


def format_output(
    output: Any,
    indent: int = 2,
) -> str:
    """
    Format output as JSON string for logging/debugging.

    Args:
        output: Output to format
        indent: JSON indentation level

    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(output, indent=indent, default=str)
    except (TypeError, ValueError):
        return str(output)


def extract_text_content(output: Any) -> str:
    """
    Extract text content from various output formats.

    Handles Anthropic message responses, dicts, and plain strings.

    Args:
        output: Output to extract from

    Returns:
        Extracted text content
    """
    # Handle Anthropic message response
    if hasattr(output, "content"):
        content = output.content
        if isinstance(content, list):
            texts = []
            for block in content:
                if hasattr(block, "text"):
                    texts.append(block.text)
                elif isinstance(block, dict) and "text" in block:
                    texts.append(block["text"])
            return " ".join(texts)
        return str(content)

    # Handle dict with common text fields
    if isinstance(output, dict):
        for key in ("text", "content", "message", "output", "result"):
            if key in output:
                return str(output[key])
        return json.dumps(output)

    return str(output)
