"""
Data models for the guardrails module.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal


# Valid values for guardrail configuration
VALID_STAGES = ("input", "behavioral", "output")
VALID_THREATS = ("cost", "quality", "scope", "security")
VALID_RESPONSES = ("block", "fallback", "truncate", "flag")
VALID_DETECTION = ("deterministic", "custom")


@dataclass
class GuardrailConfig:
    """Configuration for a single guardrail."""

    name: str
    stage: Literal["input", "behavioral", "output"]
    threat: Literal["cost", "quality", "scope", "security"]
    detection: Literal["deterministic", "custom"]
    rule: str
    response: Literal["block", "fallback", "truncate", "flag"]
    enabled: bool = True
    error_message: str | None = None
    fallback_value: Any = None
    truncate_to: int | None = None
    suffix: str = "..."

    def __post_init__(self):
        """Validate configuration values."""
        if self.stage not in VALID_STAGES:
            raise ValueError(
                f"Invalid stage '{self.stage}'. Must be one of: {VALID_STAGES}"
            )
        if self.threat not in VALID_THREATS:
            raise ValueError(
                f"Invalid threat '{self.threat}'. Must be one of: {VALID_THREATS}"
            )
        if self.response not in VALID_RESPONSES:
            raise ValueError(
                f"Invalid response '{self.response}'. Must be one of: {VALID_RESPONSES}"
            )
        if self.detection not in VALID_DETECTION:
            raise ValueError(
                f"Invalid detection '{self.detection}'. Must be one of: {VALID_DETECTION}"
            )
        if self.response == "truncate" and self.truncate_to is None:
            raise ValueError("truncate_to is required when response is 'truncate'")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "stage": self.stage,
            "threat": self.threat,
            "detection": self.detection,
            "rule": self.rule,
            "response": self.response,
            "enabled": self.enabled,
            "error_message": self.error_message,
            "fallback_value": self.fallback_value,
            "truncate_to": self.truncate_to,
            "suffix": self.suffix,
        }


@dataclass
class GuardrailResult:
    """Result of evaluating a guardrail."""

    name: str
    stage: str
    threat: str
    triggered: bool
    response: str | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "stage": self.stage,
            "threat": self.threat,
            "triggered": self.triggered,
        }
        if self.triggered:
            result["response"] = self.response
            if self.message:
                result["message"] = self.message
            if self.details:
                result["details"] = self.details
        return result


@dataclass
class GuardrailContext:
    """Execution context for tracking state across guardrail checks."""

    agent: str
    request: dict[str, Any]
    output: Any = None
    tool_call_count: int = 0
    iteration_count: int = 0
    start_time: float = field(default_factory=time.time)
    tool_calls: list[str] = field(default_factory=list)
    results: list[GuardrailResult] = field(default_factory=list)

    def record_tool_call(self, tool_name: str) -> None:
        """Record a tool call."""
        self.tool_call_count += 1
        self.tool_calls.append(tool_name)

    def increment_iteration(self) -> None:
        """Increment the iteration counter."""
        self.iteration_count += 1

    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds."""
        return int((time.time() - self.start_time) * 1000)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent": self.agent,
            "tool_call_count": self.tool_call_count,
            "iteration_count": self.iteration_count,
            "elapsed_ms": self.elapsed_ms(),
            "tool_calls": self.tool_calls,
        }


class GuardrailBlockError(Exception):
    """Raised when a guardrail blocks a request."""

    def __init__(
        self,
        guardrail_name: str,
        stage: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.guardrail_name = guardrail_name
        self.stage = stage
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_http_status(self) -> int:
        """Get appropriate HTTP status code."""
        # Input and behavioral blocks are client errors (400)
        # Output blocks are server errors (500) - we produced bad output
        return 400 if self.stage in ("input", "behavioral") else 500

    def to_response(self) -> dict[str, Any]:
        """Convert to API Gateway response format."""
        return {
            "statusCode": self.to_http_status(),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "error": self.message,
                "guardrail": self.guardrail_name,
                "stage": self.stage,
                "details": self.details,
            }),
        }


@dataclass
class GuardrailSummary:
    """Summary of all guardrail checks for a request."""

    input: list[GuardrailResult] = field(default_factory=list)
    behavioral: list[GuardrailResult] = field(default_factory=list)
    output: list[GuardrailResult] = field(default_factory=list)
    blocked: bool = False
    stage_blocked: str | None = None

    def add_result(self, result: GuardrailResult) -> None:
        """Add a result to the appropriate stage."""
        if result.stage == "input":
            self.input.append(result)
        elif result.stage == "behavioral":
            self.behavioral.append(result)
        elif result.stage == "output":
            self.output.append(result)

        # Track if we got blocked
        if result.triggered and result.response == "block":
            self.blocked = True
            self.stage_blocked = result.stage

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input": [r.to_dict() for r in self.input],
            "behavioral": [r.to_dict() for r in self.behavioral],
            "output": [r.to_dict() for r in self.output],
            "blocked": self.blocked,
            "stage_blocked": self.stage_blocked,
        }
