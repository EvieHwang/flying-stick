# Specification: AI Guardrails Infrastructure

**Requirements**: [requirements.md](./requirements.md)
**Created**: 2026-01-22
**Status**: Draft
**Scope**: Phase 1 (Core Engine) and Phase 2 (Full Stage Coverage)

---

## Overview

This specification defines the AI guardrails infrastructure for the flying-stick template. The guardrails system provides runtime protections against cost overruns, quality failures, scope violations, and security risks using the GUARD (Generalized Unified Agent Risk Defense) framework.

**Relationship to Evaluation Infrastructure:**
- **Evaluation (APF)**: Measures what the agent *should* do (offline analysis)
- **Guardrails (GUARD)**: Prevents what the agent *shouldn't* do (runtime enforcement)

---

## User Stories

### US-1: Template User Configures Guardrails

**As a** developer using the flying-stick template,
**I want to** configure guardrails for my AI agents via YAML,
**So that** I have runtime protections without writing custom validation code.

**Acceptance Criteria:**
1. Guardrails defined in `guardrails.yaml` are loaded at startup
2. Each guardrail specifies stage, threat category, detection rule, and response
3. Invalid configuration raises clear validation errors
4. Missing configuration file results in no guardrails (graceful fallback)

### US-2: Input Validation Before AI Calls

**As a** developer,
**I want** input guardrails to run before any AI API call,
**So that** invalid or dangerous inputs are rejected early, saving cost and preventing issues.

**Acceptance Criteria:**
1. Input guardrails execute before TracedAnthropicClient calls
2. Block responses return 400 Bad Request with error message
3. Input length limits (min/max) are enforced
4. Format validation (JSON schema) is supported
5. Guardrail activations are logged

### US-3: Behavioral Limits During Execution

**As a** developer,
**I want** behavioral guardrails to limit agent execution,
**So that** runaway agents are stopped before exhausting resources.

**Acceptance Criteria:**
1. Tool call count limits are enforced
2. Iteration limits prevent infinite loops
3. Only allowed tools can be called (whitelist)
4. Behavioral violations return appropriate errors
5. Limits are configurable per-agent

### US-4: Output Validation Before Response

**As a** developer,
**I want** output guardrails to validate AI responses,
**So that** invalid outputs never reach downstream systems.

**Acceptance Criteria:**
1. Output schema validation is supported
2. Enum/category validation checks against allowed values
3. Truncation limits verbose outputs
4. Block responses return 500 Internal Server Error
5. Fallback responses substitute safe default values

---

## Functional Requirements

### FR-1: Guardrails Configuration Schema

**FR-1.1**: Configuration MUST be loadable from YAML file (`guardrails.yaml`)

**FR-1.2**: Each guardrail MUST specify:
- `name`: Unique identifier
- `stage`: One of `input`, `behavioral`, `output`
- `threat`: One of `cost`, `quality`, `scope`, `security`
- `detection`: `deterministic` or `custom`
- `rule`: Expression to evaluate (for deterministic)
- `response`: One of `block`, `fallback`, `truncate`, `flag`
- `enabled`: Boolean (default: true)

**FR-1.3**: Optional guardrail fields:
- `error_message`: Message to return on block
- `fallback_value`: Value to use for fallback response
- `truncate_to`: Length limit for truncate response
- `suffix`: Suffix to append after truncation (e.g., "...")

**FR-1.4**: Configuration MUST support agent-specific guardrails:
```yaml
agents:
  classifier:
    input: [...]
    behavioral: [...]
    output: [...]
```

**FR-1.5**: Configuration SHOULD support global guardrails applied to all agents:
```yaml
global:
  input: [...]
  behavioral: [...]
  output: [...]
```

### FR-2: Guardrails Engine

**FR-2.1**: Engine MUST execute guardrails in stage order: Input → Behavioral → Output

**FR-2.2**: Engine MUST short-circuit on Block responses (stop processing immediately)

**FR-2.3**: Engine MUST apply responses in order:
1. Block: Raise exception / return error
2. Truncate: Modify output to limit size
3. Fallback: Substitute default value
4. Flag: Log but continue

**FR-2.4**: Engine MUST be injectable into TracedAnthropicClient

**FR-2.5**: Engine errors MUST NOT crash the application:
- If `fail_open: true`, continue without guardrails
- If `fail_open: false` (default), return error

### FR-3: Input Stage Guardrails

**FR-3.1**: Built-in rules MUST support:
- `max_length(field, limit)`: Check string length
- `min_length(field, limit)`: Check minimum length
- `required(field)`: Check field exists and is not empty
- `valid_json(field)`: Check JSON parseability
- `matches_schema(field, schema)`: Validate against JSON schema

**FR-3.2**: Input guardrails MUST have access to:
- `request`: The incoming request object
- `request.body`: Parsed request body (dict)
- `agent`: Agent name

**FR-3.3**: Block responses MUST return HTTP 400

### FR-4: Behavioral Stage Guardrails

**FR-4.1**: Built-in rules MUST support:
- `max_tool_calls(limit)`: Limit total tool invocations
- `max_iterations(limit)`: Limit agentic loop iterations
- `allowed_tools(list)`: Whitelist of permitted tools
- `timeout(seconds)`: Execution time limit

**FR-4.2**: Behavioral guardrails MUST track state across the agentic loop:
- `tool_call_count`: Running count of tool calls
- `iteration_count`: Running count of loop iterations
- `elapsed_time`: Time since execution started

**FR-4.3**: Behavioral guardrails MUST integrate with agent execution (hook pattern)

### FR-5: Output Stage Guardrails

**FR-5.1**: Built-in rules MUST support:
- `valid_enum(field, values)`: Check value in allowed set
- `required_fields(fields)`: Check all required fields present
- `max_length(field, limit)`: Check output field length
- `in_range(field, min, max)`: Check numeric bounds
- `valid_json(field)`: Check JSON parseability

**FR-5.2**: Output guardrails MUST have access to:
- `output`: The AI response (parsed)
- `request`: Original request
- `context`: Execution context (tool calls, timing, etc.)

**FR-5.3**: Truncate response MUST:
- Limit output to specified length
- Append suffix if configured
- Record original length in guardrail result

**FR-5.4**: Fallback response MUST:
- Substitute the configured fallback value
- Log that fallback was used
- Mark response as containing fallback

### FR-6: Logging and Observability

**FR-6.1**: All guardrail activations MUST be logged with:
- Guardrail name
- Stage
- Threat category
- Triggered (boolean)
- Response taken
- Details (values, thresholds)

**FR-6.2**: Guardrail results MUST be attachable to traces (integration with evaluation)

**FR-6.3**: Guardrail summary MUST be available for each request:
```json
{
  "guardrails": {
    "input": [...],
    "behavioral": [...],
    "output": [...]
  },
  "blocked": false,
  "stage_blocked": null
}
```

---

## Non-Functional Requirements

### NFR-1: Performance
- Input guardrails: < 5ms overhead
- Behavioral guardrails: < 1ms per check
- Output guardrails: < 5ms overhead
- Total guardrail overhead: < 15ms per request

### NFR-2: Reliability
- Guardrail engine failures MUST NOT crash the application
- Configurable fail-open vs fail-closed behavior
- Malformed rules MUST raise clear errors at load time

### NFR-3: Extensibility
- Custom detection functions MUST be registrable
- New built-in rules MUST be addable without breaking changes
- Per-agent configuration overrides global settings

---

## Data Models

### GuardrailConfig

```python
@dataclass
class GuardrailConfig:
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
```

### GuardrailResult

```python
@dataclass
class GuardrailResult:
    name: str
    stage: str
    threat: str
    triggered: bool
    response: str | None  # Only if triggered
    message: str | None
    details: dict[str, Any] = field(default_factory=dict)
```

### GuardrailContext

```python
@dataclass
class GuardrailContext:
    agent: str
    request: dict[str, Any]
    output: Any | None = None
    tool_call_count: int = 0
    iteration_count: int = 0
    start_time: float = 0
    tool_calls: list[str] = field(default_factory=list)
```

---

## API Design

### GuardrailEngine

```python
class GuardrailEngine:
    def __init__(
        self,
        config_path: str | None = None,
        config_dict: dict | None = None,
        fail_open: bool = False,
    ): ...

    def check_input(
        self,
        agent: str,
        request: dict,
    ) -> list[GuardrailResult]:
        """Run input stage guardrails. Raises GuardrailBlockError if blocked."""

    def check_behavioral(
        self,
        context: GuardrailContext,
        tool_name: str | None = None,
    ) -> list[GuardrailResult]:
        """Run behavioral guardrails. Call before each tool/iteration."""

    def check_output(
        self,
        agent: str,
        request: dict,
        output: Any,
    ) -> tuple[Any, list[GuardrailResult]]:
        """Run output guardrails. Returns (possibly modified output, results)."""

    def get_summary(self) -> dict:
        """Get summary of all guardrail checks for current request."""
```

### Integration with TracedAnthropicClient

```python
class GuardedAnthropicClient:
    def __init__(
        self,
        client: Anthropic,
        tracer: Tracer,
        guardrails: GuardrailEngine,
        agent: str,
    ): ...

    def messages_create(self, **kwargs) -> Message:
        """Create message with guardrails applied at all stages."""
```

---

## Error Handling

### GuardrailBlockError

Raised when a guardrail with `response: block` triggers:

```python
class GuardrailBlockError(Exception):
    def __init__(
        self,
        guardrail_name: str,
        stage: str,
        message: str,
        details: dict,
    ): ...

    def to_http_response(self) -> dict:
        """Convert to API Gateway response format."""
```

### HTTP Status Codes

| Stage | Response | HTTP Status |
|-------|----------|-------------|
| Input | Block | 400 Bad Request |
| Behavioral | Block | 400 Bad Request |
| Output | Block | 500 Internal Server Error |

---

## Configuration Example

```yaml
# guardrails.yaml
version: "1.0"

settings:
  fail_open: false
  log_all_activations: true
  attach_to_traces: true

global:
  input:
    - name: valid_json_body
      threat: quality
      detection: deterministic
      rule: "valid_json(request.body)"
      response: block
      error_message: "Invalid JSON in request body"

agents:
  classifier:
    input:
      - name: max_description_length
        threat: cost
        detection: deterministic
        rule: "max_length(request.body.description, 2000)"
        response: block
        error_message: "Description too long (max 2000 characters)"

      - name: min_description_length
        threat: quality
        detection: deterministic
        rule: "min_length(request.body.description, 5)"
        response: block
        error_message: "Description too short (min 5 characters)"

    behavioral:
      - name: max_tool_calls
        threat: cost
        detection: deterministic
        rule: "max_tool_calls(3)"
        response: block
        error_message: "Too many tool calls (max 3)"

      - name: allowed_tools_only
        threat: scope
        detection: deterministic
        rule: "allowed_tools(['lookup_product', 'extract_dimensions'])"
        response: block
        error_message: "Unauthorized tool usage"

    output:
      - name: valid_category
        threat: quality
        detection: deterministic
        rule: "valid_enum(output.category, ['BOOKS', 'ELECTRONICS', 'UNKNOWN'])"
        response: block
        error_message: "Invalid category returned"

      - name: truncate_reasoning
        threat: scope
        detection: deterministic
        rule: "max_length(output.reasoning, 500)"
        response: truncate
        truncate_to: 500
        suffix: "..."
```

---

## Test Scenarios

### Input Stage Tests

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Valid request | Normal JSON | Pass all guardrails |
| Missing body | Empty request | Block: "Invalid JSON" |
| Too long | 5000 char description | Block: "Too long" |
| Too short | 2 char description | Block: "Too short" |
| Empty description | `""` | Block: "Too short" |

### Behavioral Stage Tests

| Scenario | Condition | Expected Result |
|----------|-----------|-----------------|
| Normal execution | 2 tool calls | Pass |
| Excessive tools | 5 tool calls | Block after 3rd |
| Unknown tool | Call `delete_all` | Block immediately |
| Iteration limit | 10 iterations | Block after limit |

### Output Stage Tests

| Scenario | Output | Expected Result |
|----------|--------|-----------------|
| Valid output | `{category: "BOOKS"}` | Pass |
| Invalid category | `{category: "FOOD"}` | Block |
| Long reasoning | 800 chars | Truncate to 500 |
| Missing field | No `category` | Block or fallback |

---

## File Structure

```
backend/
├── src/
│   ├── guardrails/
│   │   ├── __init__.py          # Module exports
│   │   ├── models.py            # GuardrailConfig, GuardrailResult, etc.
│   │   ├── engine.py            # GuardrailEngine class
│   │   ├── config.py            # YAML config loader
│   │   ├── rules.py             # Built-in rule implementations
│   │   ├── input.py             # Input stage guardrails
│   │   ├── behavioral.py        # Behavioral stage guardrails
│   │   └── output.py            # Output stage guardrails
│   └── evaluation/              # (existing)
├── guardrails.yaml              # Configuration file
└── tests/
    ├── test_guardrails_engine.py
    ├── test_guardrails_input.py
    ├── test_guardrails_behavioral.py
    ├── test_guardrails_output.py
    └── test_guardrails_config.py
```

---

## Integration Points

### With Evaluation Infrastructure

1. **Trace attachment**: Guardrail results included in trace metadata
2. **Shared client**: GuardedAnthropicClient wraps TracedAnthropicClient
3. **Common patterns**: Similar YAML configuration approach

### With Handler

1. **Input validation**: Called before processing request
2. **Error responses**: GuardrailBlockError converted to HTTP responses
3. **Logging**: Guardrail activations logged alongside request logs

---

## Out of Scope (Phase 1-2)

- ML-based detection (Phase 4)
- PII detection/redaction (Phase 4)
- Dashboard integration (Phase 3)
- Rate limiting at application level (infrastructure concern)
- Custom detection function registration (Phase 3)
