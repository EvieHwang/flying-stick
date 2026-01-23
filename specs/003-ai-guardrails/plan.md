# Implementation Plan: AI Guardrails Infrastructure

**Specification**: [spec.md](./spec.md)
**Created**: 2026-01-22
**Status**: Planned
**Scope**: Phase 1 (Core Engine) and Phase 2 (Full Stage Coverage)

---

## Architecture Overview

### System Context

```
┌──────────────────────────────────────────────────────────────────┐
│                        Lambda Handler                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Request ──▶ INPUT GUARDRAILS ──▶ (Block? → 400)                │
│                      │                                            │
│                      ▼                                            │
│              GuardedAnthropicClient                               │
│                      │                                            │
│                      ▼                                            │
│   ┌─────────────────────────────────────┐                        │
│   │         Agentic Loop                 │                        │
│   │  ┌──────────────────────────────┐   │                        │
│   │  │  BEHAVIORAL GUARDRAILS       │   │                        │
│   │  │  - Check before each tool    │   │                        │
│   │  │  - Check each iteration      │   │                        │
│   │  │  - (Block? → 400)            │   │                        │
│   │  └──────────────────────────────┘   │                        │
│   │              │                       │                        │
│   │              ▼                       │                        │
│   │     TracedAnthropicClient           │                        │
│   │              │                       │                        │
│   │              ▼                       │                        │
│   │         Claude API                   │                        │
│   └─────────────────────────────────────┘                        │
│                      │                                            │
│                      ▼                                            │
│              OUTPUT GUARDRAILS ──▶ (Block? → 500)                │
│                      │                                            │
│                      ▼                                            │
│               Response ──▶ Client                                 │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      guardrails module                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   config    │────▶│   engine    │────▶│   models    │       │
│  │   loader    │     │             │     │             │       │
│  └─────────────┘     └──────┬──────┘     └─────────────┘       │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │    input    │     │ behavioral  │     │   output    │       │
│  │  guardrails │     │  guardrails │     │  guardrails │       │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                    │
│                             ▼                                    │
│                      ┌─────────────┐                            │
│                      │    rules    │                            │
│                      │  (built-in) │                            │
│                      └─────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Decisions

### TD-1: Rule Expression Language

**Decision**: Use a simple Python-like expression syntax parsed with a custom evaluator (not `eval`)

**Rationale**:
- Security: `eval()` is dangerous with user-provided config
- Simplicity: Full DSL is overkill for Phase 1
- Extensibility: Can add more complex expressions later

**Implementation**:
- Parse rules like `max_length(field, 2000)` into function calls
- Registry of allowed functions (whitelist approach)
- Support basic operators: `>`, `<`, `>=`, `<=`, `==`, `!=`, `in`, `not in`

### TD-2: Guardrail Execution Model

**Decision**: Guardrails run synchronously in the request path

**Rationale**:
- Runtime protection requires immediate feedback
- Guardrail overhead is minimal (< 15ms total)
- Async would complicate error handling

**Implementation**:
- `check_input()` called before AI call
- `check_behavioral()` called in agent loop (hook pattern)
- `check_output()` called before returning response

### TD-3: Integration with Evaluation

**Decision**: Guardrails attach results to existing Trace model

**Rationale**:
- Reuse existing S3 storage and API
- Single source of truth for request observability
- Consistent data model

**Implementation**:
- Add `guardrails` field to Trace model
- GuardrailEngine accepts optional Tracer
- Results attached before trace is written

### TD-4: Configuration Location

**Decision**: Separate `guardrails.yaml` file (not combined with evaluation)

**Rationale**:
- Clear separation of concerns
- Guardrails and evaluations serve different purposes
- Easier to manage independently

**Implementation**:
- Load from `backend/guardrails.yaml`
- Fallback to environment variable `GUARDRAILS_CONFIG_PATH`
- Default to empty config if not found

---

## Data Flow

### Input Stage Flow

```
Request arrives
       │
       ▼
┌──────────────────┐
│ Load guardrails  │
│ for agent        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ For each input   │◀──────────────────┐
│ guardrail:       │                   │
└────────┬─────────┘                   │
         │                             │
         ▼                             │
┌──────────────────┐                   │
│ Evaluate rule    │                   │
│ against request  │                   │
└────────┬─────────┘                   │
         │                             │
    ┌────┴────┐                        │
    │ Failed? │                        │
    └────┬────┘                        │
    Yes  │  No                         │
    │    └─────────────────────────────┘
    ▼
┌──────────────────┐
│ Response type?   │
└────────┬─────────┘
         │
    ┌────┴────┬──────────┐
    │ Block   │ Flag     │
    ▼         ▼          │
 Raise    Log and        │
 Error    continue       │
```

### Behavioral Stage Flow

```
Agent loop iteration
       │
       ▼
┌──────────────────┐
│ Update context:  │
│ - tool_call_count│
│ - iteration_count│
│ - elapsed_time   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check behavioral │
│ guardrails       │
└────────┬─────────┘
         │
    ┌────┴────┐
    │ Blocked?│
    └────┬────┘
    Yes  │  No
    │    │
    │    └──▶ Continue to tool call
    ▼
 Raise Error
 (abort loop)
```

### Output Stage Flow

```
AI response received
       │
       ▼
┌──────────────────┐
│ Parse output     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ For each output  │◀──────────────────┐
│ guardrail:       │                   │
└────────┬─────────┘                   │
         │                             │
         ▼                             │
┌──────────────────┐                   │
│ Evaluate rule    │                   │
└────────┬─────────┘                   │
         │                             │
    ┌────┴────┐                        │
    │ Failed? │                        │
    └────┬────┘                        │
    Yes  │  No                         │
    │    └─────────────────────────────┘
    ▼
┌──────────────────┐
│ Response type?   │
└────────┬─────────┘
         │
    ┌────┼────┬──────────┬──────────┐
    │    │    │          │          │
  Block  │ Truncate  Fallback    Flag
    │    │    │          │          │
    ▼    │    ▼          ▼          ▼
 Raise   │  Modify    Substitute  Log
 Error   │  output    value
```

---

## Implementation Phases

### Phase 1: Core Engine (9 tasks)

**Goal**: Working guardrails engine with input stage support

**Deliverables**:
1. `guardrails/models.py` - Data classes
2. `guardrails/config.py` - YAML loader with validation
3. `guardrails/rules.py` - Built-in rule implementations
4. `guardrails/engine.py` - Core engine class
5. `guardrails/input.py` - Input stage implementation
6. `guardrails.yaml` - Example configuration
7. Tests for all components

**Key Decisions**:
- Rule parser implementation
- Error response format
- Config validation approach

### Phase 2: Full Stage Coverage (8 tasks)

**Goal**: Complete three-stage guardrails with behavioral and output stages

**Deliverables**:
1. `guardrails/behavioral.py` - Behavioral stage
2. `guardrails/output.py` - Output stage
3. GuardrailContext for tracking execution state
4. Hook integration for agent loops
5. Trace integration for observability
6. GuardedAnthropicClient wrapper
7. Handler integration
8. Comprehensive tests

**Key Decisions**:
- Hook mechanism for behavioral checks
- Output modification strategy
- Client wrapper vs middleware approach

---

## Module Specifications

### guardrails/models.py

```python
from dataclasses import dataclass, field
from typing import Any, Literal

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

@dataclass
class GuardrailContext:
    """Execution context for behavioral guardrails."""
    agent: str
    request: dict[str, Any]
    output: Any = None
    tool_call_count: int = 0
    iteration_count: int = 0
    start_time: float = 0
    tool_calls: list[str] = field(default_factory=list)
    results: list[GuardrailResult] = field(default_factory=list)

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
        return 400 if self.stage in ("input", "behavioral") else 500

    def to_response(self) -> dict:
        return {
            "statusCode": self.to_http_status(),
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": self.message,
                "guardrail": self.guardrail_name,
                "stage": self.stage,
                "details": self.details,
            }),
        }
```

### guardrails/rules.py

```python
from typing import Any, Callable

# Registry of built-in rules
_rules: dict[str, Callable] = {}

def register_rule(name: str):
    """Decorator to register a rule function."""
    def decorator(fn: Callable) -> Callable:
        _rules[name] = fn
        return fn
    return decorator

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
    return True

@register_rule("valid_json")
def valid_json(value: Any) -> bool:
    """Check if value is valid JSON (or already parsed)."""
    if isinstance(value, (dict, list)):
        return True
    if isinstance(value, str):
        try:
            json.loads(value)
            return True
        except json.JSONDecodeError:
            return False
    return False

@register_rule("valid_enum")
def valid_enum(value: Any, allowed: list[Any]) -> bool:
    """Check if value is in allowed set."""
    return value in allowed

@register_rule("in_range")
def in_range(value: Any, min_val: float, max_val: float) -> bool:
    """Check if numeric value is in range."""
    try:
        num = float(value)
        return min_val <= num <= max_val
    except (TypeError, ValueError):
        return False

@register_rule("max_tool_calls")
def max_tool_calls(context: 'GuardrailContext', limit: int) -> bool:
    """Check if tool call count is within limit."""
    return context.tool_call_count <= limit

@register_rule("max_iterations")
def max_iterations(context: 'GuardrailContext', limit: int) -> bool:
    """Check if iteration count is within limit."""
    return context.iteration_count <= limit

@register_rule("allowed_tools")
def allowed_tools(context: 'GuardrailContext', allowed: list[str]) -> bool:
    """Check if all tool calls are in allowed list."""
    return all(tool in allowed for tool in context.tool_calls)

def evaluate_rule(rule: str, context: dict[str, Any]) -> bool:
    """Evaluate a rule string against context."""
    # Parse rule and evaluate
    # Implementation in rules.py
    ...
```

### guardrails/engine.py

```python
class GuardrailEngine:
    """Main guardrails execution engine."""

    def __init__(
        self,
        config_path: str | None = None,
        config_dict: dict | None = None,
        fail_open: bool = False,
    ):
        self.config = load_config(config_path, config_dict)
        self.fail_open = fail_open
        self._results: list[GuardrailResult] = []

    def check_input(
        self,
        agent: str,
        request: dict[str, Any],
    ) -> list[GuardrailResult]:
        """Run input stage guardrails."""
        guardrails = self._get_guardrails(agent, "input")
        results = []

        for g in guardrails:
            if not g.enabled:
                continue

            result = self._evaluate_guardrail(g, {"request": request})
            results.append(result)

            if result.triggered and result.response == "block":
                raise GuardrailBlockError(
                    guardrail_name=g.name,
                    stage="input",
                    message=g.error_message or f"Blocked by {g.name}",
                    details=result.details,
                )

        self._results.extend(results)
        return results

    def check_behavioral(
        self,
        context: GuardrailContext,
        tool_name: str | None = None,
    ) -> list[GuardrailResult]:
        """Run behavioral stage guardrails."""
        # Implementation in Phase 2
        ...

    def check_output(
        self,
        agent: str,
        request: dict[str, Any],
        output: Any,
    ) -> tuple[Any, list[GuardrailResult]]:
        """Run output guardrails, returning possibly modified output."""
        # Implementation in Phase 2
        ...

    def get_summary(self) -> dict:
        """Get summary of all guardrail results."""
        return {
            "guardrails": {
                "input": [r for r in self._results if r.stage == "input"],
                "behavioral": [r for r in self._results if r.stage == "behavioral"],
                "output": [r for r in self._results if r.stage == "output"],
            },
            "blocked": any(
                r.triggered and r.response == "block" for r in self._results
            ),
            "stage_blocked": next(
                (r.stage for r in self._results if r.triggered and r.response == "block"),
                None,
            ),
        }

    def reset(self):
        """Reset results for new request."""
        self._results = []
```

---

## Integration Strategy

### With Handler (handler.py)

```python
def lambda_handler(event: dict, context) -> dict:
    # Initialize guardrails engine
    engine = get_guardrails_engine()

    try:
        # Input guardrails
        agent = determine_agent(event)
        request = parse_request(event)
        engine.check_input(agent, request)

        # Process request with behavioral guardrails
        response = process_with_guardrails(engine, agent, request)

        # Output guardrails
        output, _ = engine.check_output(agent, request, response)

        return format_response(output)

    except GuardrailBlockError as e:
        return e.to_response()
```

### With TracedAnthropicClient

```python
class GuardedAnthropicClient:
    """Client wrapper that applies guardrails at all stages."""

    def __init__(
        self,
        client: Anthropic,
        tracer: Tracer,
        guardrails: GuardrailEngine,
        agent: str,
    ):
        self.client = client
        self.tracer = tracer
        self.guardrails = guardrails
        self.agent = agent
        self.context = GuardrailContext(agent=agent, request={})

    def messages_create(self, **kwargs) -> Message:
        # Track context for behavioral guardrails
        self.context.iteration_count += 1

        # Trace the call
        response = self.tracer.trace_call(
            agent=self.agent,
            call_fn=lambda: self.client.messages.create(**kwargs),
            request_data=kwargs,
        )

        # Track tool usage for behavioral guardrails
        self._track_tool_calls(response)

        return response
```

---

## Testing Strategy

### Unit Tests

| Component | Test Focus |
|-----------|------------|
| models.py | Serialization, validation |
| config.py | YAML parsing, error handling |
| rules.py | Each built-in rule |
| engine.py | Orchestration, short-circuit |
| input.py | Input validation scenarios |
| behavioral.py | State tracking, limits |
| output.py | Modification, fallback |

### Integration Tests

| Scenario | Components |
|----------|------------|
| Full request flow | Handler + Engine + Client |
| Trace attachment | Engine + Tracer |
| Error propagation | Engine + Handler |

### Test Data

```python
VALID_REQUEST = {
    "body": json.dumps({"description": "Valid product description"}),
}

INVALID_REQUESTS = [
    ({"body": ""}, "Invalid JSON"),
    ({"body": json.dumps({"description": "ab"})}, "Too short"),
    ({"body": json.dumps({"description": "x" * 5000})}, "Too long"),
]
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Rule parser bugs | Extensive test coverage, no `eval()` |
| Performance regression | Benchmark tests, < 15ms total |
| Config errors block all requests | Validation at load time, fail_open option |
| Behavioral guardrails miss violations | Explicit hook calls, not implicit |
| Output modification corrupts data | Immutable approach, deep copy before modify |

---

## Success Metrics

### Phase 1 Complete When:
- [ ] Input guardrails block invalid requests
- [ ] Config loads and validates correctly
- [ ] Error responses are well-formed
- [ ] All input tests pass
- [ ] < 5ms overhead for input checks

### Phase 2 Complete When:
- [ ] All three stages operational
- [ ] Behavioral limits enforced in agent loops
- [ ] Output validation and modification working
- [ ] Integration with tracer complete
- [ ] All tests pass
- [ ] < 15ms total overhead

---

## Dependencies

### Required (already in project):
- Python 3.12+
- pyyaml (for config loading)
- pydantic (for validation)

### New Dependencies:
- None required for Phase 1-2

### Integration Dependencies:
- `src.evaluation.Tracer` - For trace attachment
- `src.evaluation.TracedAnthropicClient` - For client wrapper base
