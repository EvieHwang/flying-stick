"""
Data models for the evaluation infrastructure.

This module defines the core dataclasses used for tracing and evaluation:
- Trace: Complete record of an AI interaction
- EvaluationCriterion: Definition of what to evaluate
- EvaluationResult: Result of evaluating a criterion
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Literal
import uuid
import json


# Type aliases for clarity
Pillar = Literal["effectiveness", "efficiency", "reliability", "trustworthiness"]
Layer = Literal[1, 2, 3]
EvalResult = Literal["pass", "fail", "warning", "skipped"]


@dataclass
class TraceRequest:
    """Input data for a traced API call."""
    input: str
    model: str
    system_hash: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceResponse:
    """Output data from a traced API call."""
    output: Any  # str or dict for structured output
    stop_reason: str | None = None
    raw_response: dict | None = None  # Truncated if large


@dataclass
class TraceMetrics:
    """Performance metrics for a traced API call."""
    duration_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class ToolCall:
    """Record of a tool/function call within an API interaction."""
    name: str
    input: dict[str, Any]
    output: Any
    duration_ms: int = 0


@dataclass
class EvaluationResult:
    """Result of evaluating a single criterion against a trace."""
    criterion: str
    layer: int
    result: EvalResult
    value: Any | None = None
    message: str | None = None


@dataclass
class Trace:
    """
    Complete record of an AI interaction with evaluation results.

    This is the primary data structure stored in S3 for each API call.
    """
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    agent: str = "default"
    request: TraceRequest | None = None
    response: TraceResponse | None = None
    metrics: TraceMetrics | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    error: str | None = None
    evaluations: dict[str, EvaluationResult] = field(default_factory=dict)
    guardrails: dict[str, Any] | None = None  # Guardrail results from GUARD framework
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to dictionary for JSON serialization."""
        return _asdict_recursive(self)

    def to_json(self) -> str:
        """Convert trace to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trace":
        """Create Trace from dictionary."""
        # Reconstruct nested dataclasses
        if data.get("request") and isinstance(data["request"], dict):
            data["request"] = TraceRequest(**data["request"])
        if data.get("response") and isinstance(data["response"], dict):
            data["response"] = TraceResponse(**data["response"])
        if data.get("metrics") and isinstance(data["metrics"], dict):
            data["metrics"] = TraceMetrics(**data["metrics"])
        if data.get("tool_calls"):
            data["tool_calls"] = [
                ToolCall(**tc) if isinstance(tc, dict) else tc
                for tc in data["tool_calls"]
            ]
        if data.get("evaluations"):
            data["evaluations"] = {
                k: EvaluationResult(**v) if isinstance(v, dict) else v
                for k, v in data["evaluations"].items()
            }
        return cls(**data)


@dataclass
class EvaluationCriterion:
    """
    Definition of an evaluation criterion.

    Loaded from evaluation.yaml and used by the Evaluator to assess traces.
    """
    name: str
    pillar: Pillar
    layer: Layer
    signal: str
    threshold: str
    description: str | None = None
    warning: str | None = None  # Warning threshold for Layer 2
    enabled: bool = True
    evaluation_method: str | None = None  # For Layer 3: "llm_as_judge", etc.
    prompt: str | None = None  # For Layer 3: evaluation prompt
    sample_rate: float = 1.0  # For Layer 3: fraction of traces to evaluate


def _asdict_recursive(obj: Any) -> Any:
    """Recursively convert dataclasses to dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _asdict_recursive(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [_asdict_recursive(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _asdict_recursive(v) for k, v in obj.items()}
    return obj
