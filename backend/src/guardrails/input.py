"""
Input stage guardrails.

Provides helper functions and utilities for input validation.
"""

from __future__ import annotations

import json
from typing import Any


def parse_request_body(event: dict[str, Any]) -> dict[str, Any]:
    """
    Parse request body from API Gateway event.

    Handles both string and dict body formats.

    Args:
        event: API Gateway event dictionary

    Returns:
        Parsed request body as dictionary
    """
    body = event.get("body")

    if body is None:
        return {}

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"_raw": body, "_parse_error": True}

    return {}


def get_content_length(event: dict[str, Any]) -> int:
    """
    Get the content length of the request.

    Args:
        event: API Gateway event dictionary

    Returns:
        Content length in bytes
    """
    # Try Content-Length header
    headers = event.get("headers", {}) or {}
    content_length = headers.get("Content-Length") or headers.get("content-length")
    if content_length:
        try:
            return int(content_length)
        except (ValueError, TypeError):
            pass

    # Fall back to body length
    body = event.get("body", "")
    if body:
        return len(body.encode("utf-8") if isinstance(body, str) else str(body).encode("utf-8"))

    return 0


def sanitize_input(value: str) -> str:
    """
    Basic input sanitization.

    Removes potentially dangerous characters while preserving valid content.

    Args:
        value: Input string to sanitize

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    # Remove null bytes
    value = value.replace("\x00", "")

    # Normalize whitespace
    value = " ".join(value.split())

    return value
