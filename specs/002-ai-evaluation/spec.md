# Feature Specification: AI Evaluation Infrastructure

**Feature Branch**: `002-ai-evaluation`
**Created**: 2026-01-22
**Status**: Ready for Implementation
**Input**: requirements.md, docs/EVALUATION_PROTOCOL.md

## Overview

This feature adds AI agent evaluation infrastructure to the flying-stick template, ensuring every app has built-in observability, tracing, and evaluation capabilities from day one. The system follows the Agent Performance Framework (APF) with four pillars and a three-layer evaluation approach.

Key insight: Evaluation infrastructure is most valuable when it's zero-config by default but fully customizable. Every Claude API call should be traced automatically; evaluation criteria should be opt-in via YAML configuration.

**Scope for this spec**: Phase 1 (Tracing) and Phase 2 (Evaluation Engine). Dashboard and advanced features deferred to future spec.

---

## User Scenarios & Testing

### User Story 1 - Automatic Trace Capture (Priority: P1)

A developer builds a feature using the Claude API. Without any additional configuration, all AI interactions are automatically traced and stored in S3 for later analysis.

**Why this priority**: Foundation for all evaluation—no traces, no evaluation.

**Independent Test**: Make a Claude API call via the wrapped client, verify trace appears in S3 within 5 seconds.

**Acceptance Scenarios**:

1. **Given** a Lambda using the template's Claude client wrapper, **When** it makes an API call, **Then** a trace is captured with all required fields (trace_id, timestamp, agent, input, output, metrics)
2. **Given** a trace is captured, **When** I check S3, **Then** the trace JSON is stored in `s3://{bucket}/traces/{agent}/{date}/{trace_id}.json`
3. **Given** an API call that fails, **When** I check the trace, **Then** error information is captured and stored
4. **Given** an API call with tool use, **When** I check the trace, **Then** tool calls are captured with name, input, output, and duration

---

### User Story 2 - Define Evaluation Criteria (Priority: P1)

A developer wants to evaluate their classification agent. They create an `evaluation.yaml` file defining what "good" looks like—output format validation, latency thresholds, and token efficiency.

**Why this priority**: Without criteria, traces are just logs. Criteria turn them into actionable evaluation.

**Independent Test**: Create evaluation.yaml with 3 criteria, verify they're loaded and validated correctly.

**Acceptance Scenarios**:

1. **Given** an evaluation.yaml with criteria definitions, **When** the evaluator starts, **Then** criteria are loaded and validated
2. **Given** a criterion with invalid pillar value, **When** config is loaded, **Then** a clear validation error is raised
3. **Given** a criterion with layer 1 (binary), **When** I inspect the loaded config, **Then** threshold is interpreted as pass/fail condition
4. **Given** a criterion with layer 2 (quantitative), **When** I inspect the loaded config, **Then** threshold and optional warning threshold are parsed

---

### User Story 3 - Automatic Evaluation on Traces (Priority: P1)

When a trace is captured, Layer 1 and Layer 2 evaluations run automatically. Results are attached to the trace before storage.

**Why this priority**: Real-time evaluation catches issues immediately rather than in batch analysis.

**Independent Test**: Configure latency criterion with threshold 3000ms, make a call taking 2000ms, verify evaluation result is "pass".

**Acceptance Scenarios**:

1. **Given** a Layer 1 criterion checking output format, **When** a trace with valid output is captured, **Then** evaluation result is "pass"
2. **Given** a Layer 1 criterion checking output format, **When** a trace with invalid output is captured, **Then** evaluation result is "fail"
3. **Given** a Layer 2 criterion with latency threshold 3000ms, **When** a trace with 2500ms latency is captured, **Then** evaluation result is "pass" with value 2500
4. **Given** a Layer 2 criterion with warning threshold 2000ms, **When** a trace with 2500ms latency is captured, **Then** evaluation result is "warning"
5. **Given** multiple criteria, **When** a trace is captured, **Then** all evaluations run and results are attached to `trace.evaluations`

---

### User Story 4 - Retrieve Traces for Analysis (Priority: P2)

A developer wants to analyze their agent's performance. They query traces by time range, agent, and evaluation result to understand patterns.

**Why this priority**: Traces are only valuable if retrievable. Analysis drives improvement.

**Independent Test**: Store 10 traces with varying results, query for failed evaluations, verify correct traces returned.

**Acceptance Scenarios**:

1. **Given** traces stored in S3, **When** I query by time range, **Then** matching traces are returned
2. **Given** traces for multiple agents, **When** I query by agent name, **Then** only that agent's traces are returned
3. **Given** traces with pass/fail evaluations, **When** I query by evaluation result, **Then** matching traces are returned
4. **Given** a specific trace_id, **When** I retrieve it, **Then** the full trace with evaluations is returned

---

### Edge Cases

- **Missing evaluation.yaml**: System should work with zero criteria (tracing only)
- **Malformed evaluation.yaml**: Clear error at startup, not runtime
- **S3 write failure**: Log error, don't crash the Lambda—tracing is observability, not critical path
- **Very large response**: Truncate response in trace if > 100KB to prevent S3 bloat
- **Concurrent traces**: Trace IDs are UUIDs, no collision risk
- **Clock skew**: Use server timestamp, not client timestamp

---

## Requirements

### Functional Requirements

**Trace Capture (FR-1)**

- **FR-1.1**: Template MUST include a `TracedAnthropicClient` wrapper for the Claude SDK
- **FR-1.2**: Traces MUST capture: trace_id (UUID), timestamp (ISO 8601), agent, input, output, duration_ms, input_tokens, output_tokens, total_tokens, model, tool_calls, error, metadata
- **FR-1.3**: Tracing MUST be enabled by default with zero configuration
- **FR-1.4**: Tracing MUST work in both Lambda and local environments
- **FR-1.5**: Agent identifier MUST be configurable per-client or per-call
- **FR-1.6**: Custom metadata MUST be attachable to traces (key-value pairs)

**Trace Storage (FR-2)**

- **FR-2.1**: Traces MUST be stored in S3 with path `s3://{bucket}/traces/{agent}/{YYYY-MM-DD}/{trace_id}.json`
- **FR-2.2**: S3 bucket name MUST be configurable via environment variable
- **FR-2.3**: Traces MUST be written asynchronously to minimize latency impact
- **FR-2.4**: Large responses (>100KB) MUST be truncated with truncation indicator
- **FR-2.5**: S3 lifecycle policy SHOULD be documented for retention (default: 30 days)

**Evaluation Criteria (FR-3)**

- **FR-3.1**: Criteria MUST be defined in `evaluation.yaml` in the backend directory
- **FR-3.2**: Criteria schema MUST support: name, description, pillar, layer, signal, threshold, warning (optional), enabled (optional)
- **FR-3.3**: Pillar values MUST be validated: effectiveness, efficiency, reliability, trustworthiness
- **FR-3.4**: Layer values MUST be validated: 1 (binary), 2 (quantitative), 3 (judgment)
- **FR-3.5**: Template MUST include example criteria for common patterns
- **FR-3.6**: Missing evaluation.yaml MUST be handled gracefully (tracing works, no evaluations)

**Evaluation Execution (FR-4)**

- **FR-4.1**: Layer 1 evaluations MUST run on every trace automatically
- **FR-4.2**: Layer 2 evaluations MUST run on every trace automatically
- **FR-4.3**: Layer 3 evaluations MUST be opt-in (not implemented in Phase 1-2)
- **FR-4.4**: Evaluation results MUST be attached to trace before storage
- **FR-4.5**: Each evaluation result MUST include: criterion name, layer, result (pass/fail/warning), value (for Layer 2)
- **FR-4.6**: Evaluation failures SHOULD be logged (CloudWatch) for alerting

**Built-in Signals (FR-5)**

- **FR-5.1**: Template MUST include built-in signals: duration_ms, input_tokens, output_tokens, total_tokens, error, response.format (JSON validation)
- **FR-5.2**: Custom signals SHOULD be definable via simple Python functions
- **FR-5.3**: Signal extraction MUST handle missing fields gracefully (return None)

**Trace Retrieval (FR-6)**

- **FR-6.1**: Template MUST include API endpoint for listing traces with filters
- **FR-6.2**: Filters MUST support: time_range (start/end), agent, evaluation_result
- **FR-6.3**: Template MUST include API endpoint for getting single trace by ID
- **FR-6.4**: List endpoint SHOULD support pagination (default: 100 traces)

---

### Non-Functional Requirements

- **NFR-1**: Tracing overhead MUST be < 50ms per request (async S3 write)
- **NFR-2**: Trace storage SHOULD cost < $1/month for 10,000 traces (S3 is ~$0.023/GB)
- **NFR-3**: New criteria MUST be addable without code changes (YAML only)
- **NFR-4**: S3 storage MUST use server-side encryption (SSE-S3)
- **NFR-5**: Traces containing PII SHOULD be documented; redaction is out of scope for Phase 1-2

---

### Key Entities

**Trace**
```python
@dataclass
class Trace:
    trace_id: str          # UUID
    timestamp: str         # ISO 8601
    agent: str             # Agent identifier
    request: TraceRequest  # Input details
    response: TraceResponse # Output details
    metrics: TraceMetrics  # Timing and tokens
    tool_calls: list[ToolCall]  # Optional
    error: str | None      # Error if failed
    evaluations: dict[str, EvaluationResult]  # Results by criterion
    metadata: dict[str, Any]  # Custom key-value
```

**EvaluationCriterion**
```python
@dataclass
class EvaluationCriterion:
    name: str
    description: str | None
    pillar: Literal["effectiveness", "efficiency", "reliability", "trustworthiness"]
    layer: Literal[1, 2, 3]
    signal: str            # Field path or function name
    threshold: str         # Pass condition
    warning: str | None    # Warning threshold (Layer 2)
    enabled: bool = True
```

**EvaluationResult**
```python
@dataclass
class EvaluationResult:
    criterion: str
    layer: int
    result: Literal["pass", "fail", "warning", "skipped"]
    value: Any | None      # Actual value for Layer 2
    message: str | None    # Additional context
```

---

## Success Criteria

### Measurable Outcomes

- **SC-1**: 100% of Claude API calls through wrapped client produce traces in S3
- **SC-2**: Tracing overhead < 50ms (measured as time delta between wrapped and unwrapped calls)
- **SC-3**: All Layer 1 and Layer 2 criteria defined in evaluation.yaml are evaluated
- **SC-4**: Trace retrieval API returns results in < 500ms for queries up to 100 traces
- **SC-5**: Zero code changes required to add new evaluation criteria

---

## Assumptions

- S3 bucket will be created as part of infrastructure (via SAM template or manually)
- Claude SDK is already a dependency (anthropic package)
- Lambda has IAM permissions for S3 read/write
- evaluation.yaml is optional—system works without it
- Layer 3 (LLM-as-Judge) is explicitly out of scope for Phase 1-2

---

## Out of Scope (Future Phases)

- **Phase 3**: Dashboard for visualization (MetricsSummary, TimeSeriesChart, TraceInspector)
- **Phase 4**: Layer 3 LLM-as-Judge evaluations
- **Phase 4**: Alerting on Layer 1 failures (CloudWatch Alarms)
- **Phase 4**: Evaluation protocol questionnaire generator
- PII redaction/hashing
- Multi-environment trace separation (all traces go to same bucket)

---

## Dependencies

- **AWS Services**: S3 (storage), IAM (permissions), CloudWatch (logging)
- **Python Packages**: anthropic (Claude SDK), boto3 (S3), pyyaml (config), pydantic (validation)
- **Template Infrastructure**: Existing Lambda handler, SAM template
