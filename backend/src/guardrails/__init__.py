"""
AI Guardrails Infrastructure.

Runtime protections for AI agents using the GUARD framework:
- Three stages: Input → Behavioral → Output
- Four threats: Cost, Quality, Scope, Security
- Four responses: Block, Fallback, Truncate, Flag

Usage:
    from src.guardrails import GuardrailEngine, GuardrailBlockError

    # Create engine from config
    engine = GuardrailEngine(config_path="guardrails.yaml")

    # Check input before AI call
    try:
        engine.check_input(agent="classifier", request=request_data)
    except GuardrailBlockError as e:
        return e.to_response()

    # Track behavioral state in agent loops
    ctx = engine.create_context(agent="classifier", request=request_data)
    for iteration in range(max_iterations):
        engine.check_behavioral(ctx, tool_name="lookup")

    # Check output before returning
    output, results = engine.check_output(agent="classifier", request=request_data, output=ai_response)

    # Get summary for logging/tracing
    summary = engine.get_summary()
"""

from .models import (
    GuardrailConfig,
    GuardrailResult,
    GuardrailContext,
    GuardrailBlockError,
    GuardrailSummary,
    VALID_STAGES,
    VALID_THREATS,
    VALID_RESPONSES,
)

from .engine import GuardrailEngine

from .config import (
    load_guardrails,
    validate_config,
    get_settings,
    ConfigValidationError,
)

from .rules import (
    register_rule,
    get_rule,
    list_rules,
    evaluate_rule,
    RuleParseError,
)

from .client import (
    GuardedAnthropicClient,
    get_guarded_client,
)

from .behavioral import (
    BehavioralGuard,
    with_behavioral_check,
)

from .input import (
    parse_request_body,
    get_content_length,
    sanitize_input,
)

from .output import (
    truncate_string,
    truncate_field,
    apply_fallback,
    validate_json_structure,
    extract_text_content,
)


__all__ = [
    # Models
    "GuardrailConfig",
    "GuardrailResult",
    "GuardrailContext",
    "GuardrailBlockError",
    "GuardrailSummary",
    "VALID_STAGES",
    "VALID_THREATS",
    "VALID_RESPONSES",
    # Engine
    "GuardrailEngine",
    # Config
    "load_guardrails",
    "validate_config",
    "get_settings",
    "ConfigValidationError",
    # Rules
    "register_rule",
    "get_rule",
    "list_rules",
    "evaluate_rule",
    "RuleParseError",
    # Client
    "GuardedAnthropicClient",
    "get_guarded_client",
    # Behavioral
    "BehavioralGuard",
    "with_behavioral_check",
    # Input
    "parse_request_body",
    "get_content_length",
    "sanitize_input",
    # Output
    "truncate_string",
    "truncate_field",
    "apply_fallback",
    "validate_json_structure",
    "extract_text_content",
]
