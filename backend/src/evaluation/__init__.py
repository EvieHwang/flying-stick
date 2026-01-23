"""
AI Evaluation Infrastructure for {{PROJECT_NAME}}.

This module provides tracing and evaluation capabilities for AI agent interactions.

Quick Start:
    from src.evaluation import TracedAnthropicClient, get_traced_client

    # Create a traced client
    client = get_traced_client(agent="classifier")

    # Make API calls - traces are captured automatically
    response = client.messages_create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Classify this..."}]
    )

Configuration:
    - Set TRACE_BUCKET environment variable for S3 storage
    - Create evaluation.yaml to define evaluation criteria
    - See docs/EVALUATION.md for full documentation

Components:
    - TracedAnthropicClient: Drop-in replacement for Anthropic client
    - Tracer: Low-level trace capture and S3 storage
    - Evaluator: Runs criteria against traces
    - Models: Trace, EvaluationCriterion, EvaluationResult dataclasses
"""

from .client import TracedAnthropicClient, get_traced_client
from .tracer import Tracer
from .evaluator import Evaluator
from .criteria import load_criteria, validate_config
from .signals import extract_signal, register_signal
from .models import (
    Trace,
    TraceRequest,
    TraceResponse,
    TraceMetrics,
    ToolCall,
    EvaluationCriterion,
    EvaluationResult,
)


__all__ = [
    # Client
    "TracedAnthropicClient",
    "get_traced_client",
    # Core components
    "Tracer",
    "Evaluator",
    # Configuration
    "load_criteria",
    "validate_config",
    # Signals
    "extract_signal",
    "register_signal",
    # Models
    "Trace",
    "TraceRequest",
    "TraceResponse",
    "TraceMetrics",
    "ToolCall",
    "EvaluationCriterion",
    "EvaluationResult",
]
