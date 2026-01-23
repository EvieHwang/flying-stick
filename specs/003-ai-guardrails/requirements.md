# AI Guardrails Infrastructure: Requirements Document

## Executive Summary

This document specifies requirements for adding AI agent guardrails infrastructure to the flying-stick template. The goal is to ensure every app built from this template has built-in runtime protections against cost overruns, quality failures, scope violations, and security risks.

The guardrails framework follows **GUARD (Generalized Unified Agent Risk Defense)** with three stages (Input, Behavioral, Output) and four threat categories (Cost, Quality, Scope, Security).

This document complements the AI Evaluation Infrastructure requirements. Together they form a complete observability and safety layer:
- **Evaluation (APF)**: Measure what the agent *should* do (offline)
- **Guardrails (GUARD)**: Prevent what the agent *shouldn't* do (runtime)

---

## Problem Statement

### Current State
- Apps have no standardized runtime protections for AI agent behavior
- Cost controls are implemented ad-hoc (if at all)
- Invalid outputs can propagate to downstream systems
- No systematic way to prevent scope violations or resource abuse

### Target State
- Every app has guardrails infrastructure from the start
- Three-stage defense: Input → Behavioral → Output
- Configurable guardrails per agent via YAML
- Clear separation between guardrails (runtime block) and evaluation (offline measure)
- Infrastructure supports adding new guardrails without code changes

---

## Core Concepts

### The GUARD Framework

**GUARD** = Generalized Unified Agent Risk Defense

Three analysis stages:
1. **Input Stage**: What can go wrong before the AI sees the request?
2. **Behavioral Stage**: What can go wrong during AI execution?
3. **Output Stage**: What can go wrong with the AI's response?

Four threat categories:
| Threat | Description | Example |
|--------|-------------|---------|
| **Cost** | Resource/money waste | Token explosion, excessive API calls |
| **Quality** | Unusable or incorrect output | Invalid format, missing fields |
| **Scope** | Agent exceeds intended boundaries | Unauthorized tool use, off-topic response |
| **Security** | Data leakage or harmful actions | PII exposure, prompt injection |

### Guardrail Responses

| Response | Behavior | When to Use |
|----------|----------|-------------|
| **Block** | Reject request, return error | Hard failures, security risks |
| **Fallback** | Use default/safe value | Recoverable quality issues |
| **Truncate** | Limit output size | Verbose responses |
| **Flag** | Allow but log for review | Suspicious but not blocking |

### Detection Methods

| Method | Characteristics | Preference |
|--------|-----------------|------------|
| **Deterministic** | Rule-based, predictable, fast | Preferred |
| **ML-based** | Learned patterns, flexible, slower | Use sparingly |

---

## Functional Requirements

### FR-1: Input Stage Guardrails

**FR-1.1**: Template MUST include configurable input validation:
- Minimum input length (prevent empty/trivial requests)
- Maximum input length (prevent token cost explosion)
- Required fields validation
- JSON/format validation

**FR-1.2**: Template MUST include rate limiting pattern:
- API Gateway throttling configuration in template.yaml
- Documentation for per-IP rate limiting (WAF or application-level)

**FR-1.3**: Input guardrails MUST run before any AI API call

**FR-1.4**: Input guardrail failures MUST return appropriate HTTP status codes:
- 400 Bad Request (validation failures)
- 429 Too Many Requests (rate limiting)

### FR-2: Behavioral Stage Guardrails

**FR-2.1**: Template MUST include execution limits:
- Maximum tool calls per request (prevent runaway agents)
- Maximum iterations for agentic loops
- Request timeout (before Lambda timeout)

**FR-2.2**: Template MUST enforce tool restrictions:
- Fixed tool set (only allow defined tools)
- Unknown tool requests MUST be blocked

**FR-2.3**: Template SHOULD include cost tracking:
- Token counting per request
- Cumulative cost tracking (optional)

**FR-2.4**: Behavioral guardrails MUST operate within the agent execution loop

### FR-3: Output Stage Guardrails

**FR-3.1**: Template MUST include output validation:
- Schema validation (required fields, types)
- Enum validation (output must be from allowed set)
- Confidence/score bounds checking

**FR-3.2**: Template MUST include output sanitization:
- Reasoning/text truncation (configurable max length)
- PII detection/redaction (optional, configurable)

**FR-3.3**: Invalid outputs MUST trigger appropriate response:
- Block: Return error to client
- Fallback: Use safe default value
- Flag: Return output but log for review

**FR-3.4**: Output guardrails MUST run before response is sent to client

### FR-4: Guardrails Configuration

**FR-4.1**: Template MUST include a schema for defining guardrails (YAML)

**FR-4.2**: Guardrails configuration MUST support:
- Stage assignment (input/behavioral/output)
- Threat category (cost/quality/scope/security)
- Detection method (deterministic rule or custom function)
- Response type (block/fallback/truncate/flag)
- Threshold specification
- Enabled/disabled flag

**FR-4.3**: Configuration SHOULD live alongside evaluation config (e.g., `guardrails.yaml` or combined `agent-config.yaml`)

**FR-4.4**: Template MUST include example guardrails for common patterns

### FR-5: Guardrails Execution Engine

**FR-5.1**: Engine MUST execute guardrails in stage order: Input → Behavioral → Output

**FR-5.2**: Engine MUST short-circuit on Block responses (don't continue processing)

**FR-5.3**: Engine MUST log all guardrail activations (for debugging and audit)

**FR-5.4**: Engine MUST attach guardrail results to traces (integration with evaluation infrastructure)

### FR-6: Structural Guardrails Documentation

**FR-6.1**: Template MUST document architectural guardrails that are inherent to the design:
- Fixed tool set (agents can only use defined tools)
- Lambda isolation (no arbitrary network access)
- Single model constraint (no model escalation)

**FR-6.2**: CLAUDE.md MUST include guardrails awareness:
- Cost guardrails already documented (no provisioned concurrency)
- Add awareness of runtime guardrails

---

## Non-Functional Requirements

### NFR-1: Performance
- Guardrail checks MUST add < 10ms latency per stage
- Deterministic checks preferred over ML-based

### NFR-2: Reliability
- Guardrail failures MUST NOT crash the application
- Fallback behavior MUST be defined for guardrail engine errors

### NFR-3: Observability
- All guardrail activations MUST be logged
- Guardrail metrics SHOULD be visible in evaluation dashboard

### NFR-4: Extensibility
- New guardrails MUST be addable via configuration
- Custom detection functions SHOULD be supportable

---

## Proposed File Structure

```
backend/
├── src/
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── engine.py           # Guardrails execution engine
│   │   ├── input.py            # Input stage guardrails
│   │   ├── behavioral.py       # Behavioral stage guardrails
│   │   ├── output.py           # Output stage guardrails
│   │   └── config.py           # Load guardrails configuration
│   ├── evaluation/             # (from evaluation infrastructure)
│   └── utils/
│       └── secrets.py          # (existing)
├── guardrails.yaml             # Guardrails configuration
└── tests/
    ├── test_input_guardrails.py
    ├── test_behavioral_guardrails.py
    └── test_output_guardrails.py

docs/
├── GUARDRAILS.md               # How to use guardrails infrastructure
└── GUARD_FRAMEWORK.md          # GUARD framework reference
```

---

## Example: Guardrails Configuration

```yaml
# guardrails.yaml
version: "1.0"

agents:
  classifier:
    description: "Product classification agent"
    
    input:
      # Cost: Prevent token explosion
      - name: max_input_length
        threat: cost
        detection: deterministic
        rule: "len(input.description) <= 2000"
        response: block
        error_message: "Description too long (max 2000 characters)"
        
      # Quality: Prevent trivial requests
      - name: min_input_length
        threat: quality
        detection: deterministic
        rule: "len(input.description.strip()) >= 5"
        response: block
        error_message: "Description too short (min 5 characters)"
        
      # Quality: Validate format
      - name: valid_json
        threat: quality
        detection: deterministic
        rule: "is_valid_json(request.body)"
        response: block
        error_message: "Invalid JSON in request body"

    behavioral:
      # Cost: Limit tool calls
      - name: max_tool_calls
        threat: cost
        detection: deterministic
        rule: "tool_call_count <= 3"
        response: block
        error_message: "Too many tool calls (max 3)"
        
      # Cost: Limit iterations
      - name: max_iterations
        threat: cost
        detection: deterministic
        rule: "iteration_count <= 5"
        response: block
        error_message: "Too many iterations (max 5)"
        
      # Scope: Only allowed tools
      - name: allowed_tools
        threat: scope
        detection: deterministic
        rule: "tool_name in ['lookup_known_product', 'extract_dimensions']"
        response: block
        error_message: "Unknown tool requested"

    output:
      # Quality: Valid category
      - name: valid_category
        threat: quality
        detection: deterministic
        rule: "output.category in VALID_CATEGORIES"
        response: block  # Don't fallback - invalid category is a failure
        error_message: "Invalid category returned"
        
      # Quality: Valid confidence
      - name: valid_confidence
        threat: quality
        detection: deterministic
        rule: "output.confidence in ['HIGH', 'MEDIUM_HIGH', 'MEDIUM', 'MEDIUM_LOW', 'LOW']"
        response: block
        error_message: "Invalid confidence tier"
        
      # Scope: Reasoning length
      - name: reasoning_length
        threat: scope
        detection: deterministic
        rule: "len(output.reasoning) <= 500"
        response: truncate
        truncate_to: 500
        suffix: "..."

# Global settings
settings:
  log_all_activations: true
  attach_to_traces: true
  fail_open: false  # If guardrail engine fails, block request
```

---

## Example: Guardrail Activation Log

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-23T04:30:00Z",
  "agent": "classifier",
  "guardrails": {
    "input": [
      {"name": "max_input_length", "triggered": false},
      {"name": "min_input_length", "triggered": false},
      {"name": "valid_json", "triggered": false}
    ],
    "behavioral": [
      {"name": "max_tool_calls", "triggered": false, "value": 2},
      {"name": "max_iterations", "triggered": false, "value": 1},
      {"name": "allowed_tools", "triggered": false}
    ],
    "output": [
      {"name": "valid_category", "triggered": false},
      {"name": "valid_confidence", "triggered": false},
      {"name": "reasoning_length", "triggered": true, "response": "truncate", "original_length": 650}
    ]
  },
  "blocked": false,
  "stage_blocked": null
}
```

---

## Stage × Threat Coverage Matrix

Template for documenting guardrail coverage:

|  | Input | Behavioral | Output |
|--|-------|------------|--------|
| **Cost** | Max input length, Rate limiting | Tool call limit, Iteration limit, Timeout | — |
| **Quality** | Min input length, Format validation | — | Output validation, Schema check |
| **Scope** | — | Allowed tools, Fixed tool set | Reasoning truncation |
| **Security** | (Optional: injection detection) | Lambda isolation | (Optional: PII redaction) |

---

## Implementation Phases

### Phase 1: Core Engine
- Implement guardrails engine (`engine.py`)
- Implement input stage guardrails
- Implement configuration loading
- Basic logging

### Phase 2: Full Stage Coverage
- Implement behavioral stage guardrails
- Implement output stage guardrails
- Integration with agent execution loop

### Phase 3: Integration
- Attach guardrail results to traces (evaluation integration)
- Add guardrail metrics to dashboard
- Document structural guardrails

### Phase 4: Advanced Features
- Custom detection functions
- ML-based detection (optional)
- PII detection/redaction

---

## Relationship to Evaluation Infrastructure

Guardrails and evaluations are complementary:

| Concern | Guardrail (Runtime) | Evaluation (Offline) |
|---------|---------------------|----------------------|
| Invalid output format | Block immediately | Gate: `valid_format` |
| Slow response | Timeout at threshold | Metric: `latency_p95` |
| Wrong classification | — | Metric: `accuracy` |
| Excessive confidence | — | Metric: `overconfident_failure` |
| Cost overrun | Tool/iteration limits | Metric: `tokens_per_request` |

**Key insight**: Guardrails catch **catastrophic failures** at runtime. Evaluations measure **quality degradation** over time.

Some concerns are guardrails-only (block invalid format), some are evaluation-only (measure accuracy), and some are both (latency has a hard timeout guardrail AND a quality metric).

---

## Success Criteria

1. **Every AI call is protected**: Apps using the template have guardrails by default
2. **Three-stage coverage**: Input, behavioral, and output stages all have guardrail hooks
3. **Configurable**: New guardrails addable via YAML without code changes
4. **Integrated**: Guardrail activations visible in traces and dashboard
5. **Documented**: GUARDRAILS.md explains how to use and extend

---

## Open Questions

- [ ] Should guardrails and evaluation config be in one file or separate?
- [ ] Should the engine fail-open or fail-closed by default?
- [ ] Should PII detection be included in the template or left to per-project?
- [ ] How should custom detection functions be registered?

---

## References

- WM2 Guardrails Specification (attached) - Reference implementation
- GUARD Framework - Generalized Unified Agent Risk Defense
- AI Evaluation Infrastructure Requirements - Complementary system

---

## Instructions for Claude Code CLI

**Prompt to use:**

> "Here's a requirements document for AI guardrails infrastructure in `specs/003-ai-guardrails/requirements.md`. The GUARD framework reference is in `docs/GUARD_FRAMEWORK.md`. Please:
> 1. Review the requirements
> 2. Create spec.md, plan.md, and tasks.md
> 3. Note that this complements the evaluation infrastructure (specs/002-ai-evaluation/)
>
> Focus on Phase 1 and 2 first - core engine and full stage coverage. The guardrails should integrate with the tracer from the evaluation infrastructure."
