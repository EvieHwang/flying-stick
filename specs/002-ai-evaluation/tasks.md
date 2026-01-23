# Task Breakdown: AI Evaluation Infrastructure

**Plan**: [plan.md](./plan.md)
**Created**: 2026-01-22
**Status**: Phase 1-2 Complete
**Scope**: Phase 1 (Tracing) and Phase 2 (Evaluation Engine)

## Task Summary

| Phase | Tasks | Completed |
|-------|-------|-----------|
| Phase 1: Core Tracing | 10 | 10 |
| Phase 2: Evaluation Engine | 9 | 9 |
| **Total** | **19** | **19** |

---

## Phase 1: Core Tracing

### T-1.1: Create Evaluation Module Structure

- **Description**: Create the `backend/src/evaluation/` directory with `__init__.py` that exports the public API
- **Dependencies**: None
- **Files**:
  - Create: `backend/src/evaluation/__init__.py`
- **Acceptance**: Module can be imported (`from src.evaluation import TracedAnthropicClient`)
- **Status**: [x] Complete

### T-1.2: Implement Data Models

- **Description**: Create dataclasses for Trace, TraceRequest, TraceResponse, TraceMetrics, ToolCall using dataclasses. Include JSON serialization helpers.
- **Dependencies**: T-1.1
- **Files**:
  - Create: `backend/src/evaluation/models.py`
- **Acceptance**:
  - All dataclasses defined with type hints
  - `Trace.trace_id` defaults to UUID
  - `Trace.timestamp` defaults to current time ISO 8601
  - `asdict()` produces valid JSON-serializable dict
- **Status**: [x] Complete

### T-1.3: Implement Tracer Core

- **Description**: Create Tracer class that captures API calls, builds Trace objects, and provides async S3 write capability
- **Dependencies**: T-1.2
- **Files**:
  - Create: `backend/src/evaluation/tracer.py`
- **Acceptance**:
  - `Tracer.__init__()` accepts bucket name (from env var if not provided)
  - `Tracer.trace_call()` times execution and builds Trace
  - `Tracer._write_trace()` writes to S3 with correct path structure
  - ThreadPoolExecutor used for async writes
  - Tracing can be disabled via `enabled=False`
- **Status**: [x] Complete

### T-1.4: Implement TracedAnthropicClient

- **Description**: Create wrapper around Anthropic client that automatically traces all `messages.create()` calls
- **Dependencies**: T-1.3
- **Files**:
  - Create: `backend/src/evaluation/client.py`
- **Acceptance**:
  - Wraps standard Anthropic client
  - `messages_create()` method traces call and returns response
  - Agent name configurable per-client
  - Custom metadata can be passed per-call
  - Returns same response type as unwrapped client
- **Status**: [x] Complete

### T-1.5: Add S3 Bucket to SAM Template

- **Description**: Add TraceBucket resource to template.yaml with encryption and lifecycle policy. Add IAM permissions for Lambda to read/write.
- **Dependencies**: None (can run parallel)
- **Files**:
  - Modify: `template.yaml`
- **Acceptance**:
  - S3 bucket created with AES256 encryption
  - 30-day lifecycle policy for automatic deletion
  - Lambda has S3CrudPolicy for the bucket
  - TRACE_BUCKET environment variable passed to Lambda
- **Status**: [x] Complete

### T-1.6: Add Dependencies to requirements.txt

- **Description**: Add pyyaml and pydantic to backend requirements
- **Dependencies**: None (can run parallel)
- **Files**:
  - Modify: `backend/requirements.txt`
- **Acceptance**: `pip install -r requirements.txt` installs pyyaml and pydantic
- **Status**: [x] Complete

### T-1.7: Implement Trace Retrieval API

- **Description**: Add API endpoints to handler.py for listing and retrieving traces from S3
- **Dependencies**: T-1.3, T-1.5
- **Files**:
  - Modify: `backend/src/handler.py`
- **Acceptance**:
  - `GET /traces` lists traces with optional filters (agent, start, end)
  - `GET /traces/{trace_id}` returns full trace JSON
  - Pagination supported with limit and next_token
  - Returns 404 for non-existent trace_id
- **Status**: [x] Complete

### T-1.8: Handle Response Truncation

- **Description**: Add logic to truncate large responses (>100KB) in traces to prevent S3 bloat
- **Dependencies**: T-1.3
- **Files**:
  - Modify: `backend/src/evaluation/tracer.py`
- **Acceptance**:
  - Responses > 100KB are truncated
  - Truncated responses include `_truncated: true` field
  - Original response length recorded in metadata
- **Status**: [x] Complete

### T-1.9: Write Tracer Tests

- **Description**: Create comprehensive tests for tracer functionality using moto for S3 mocking
- **Dependencies**: T-1.3, T-1.4
- **Files**:
  - Create: `backend/tests/test_tracer.py`
- **Acceptance**:
  - Test trace capture with successful call
  - Test trace capture with failed call (error recorded)
  - Test S3 write with correct path structure
  - Test response truncation
  - Test disabled tracing (no S3 write)
  - All tests pass with `pytest`
- **Status**: [x] Complete

### T-1.10: Update Module Exports

- **Description**: Update `__init__.py` to export TracedAnthropicClient, Tracer, and models
- **Dependencies**: T-1.2, T-1.3, T-1.4
- **Files**:
  - Modify: `backend/src/evaluation/__init__.py`
- **Acceptance**:
  - `from src.evaluation import TracedAnthropicClient` works
  - `from src.evaluation import Tracer, Trace` works
  - Public API is clean and documented
- **Status**: [x] Complete

---

## Phase 2: Evaluation Engine

### T-2.1: Add Evaluation Models

- **Description**: Add EvaluationCriterion and EvaluationResult dataclasses to models.py
- **Dependencies**: T-1.2
- **Files**:
  - Modify: `backend/src/evaluation/models.py`
- **Acceptance**:
  - EvaluationCriterion with name, description, pillar, layer, signal, threshold, warning, enabled
  - EvaluationResult with criterion, layer, result, value, message
  - Pillar validated as enum (effectiveness, efficiency, reliability, trustworthiness)
  - Layer validated as 1, 2, or 3
- **Status**: [x] Complete

### T-2.2: Implement Criteria Loader

- **Description**: Create criteria.py that loads and validates evaluation.yaml using Pydantic
- **Dependencies**: T-2.1, T-1.6
- **Files**:
  - Create: `backend/src/evaluation/criteria.py`
- **Acceptance**:
  - `load_criteria(path)` returns dict of agent -> list of criteria
  - Invalid YAML raises clear error with line number
  - Invalid pillar/layer values raise validation error
  - Missing file returns empty dict (graceful fallback)
  - Criteria with `enabled: false` are included but marked
- **Status**: [x] Complete

### T-2.3: Implement Built-in Signals

- **Description**: Create signals.py with extractors for common signals: duration_ms, input_tokens, output_tokens, total_tokens, error, response.format
- **Dependencies**: T-1.2
- **Files**:
  - Create: `backend/src/evaluation/signals.py`
- **Acceptance**:
  - `extract_signal(trace, "duration_ms")` returns trace.metrics.duration_ms
  - `extract_signal(trace, "response.format")` validates JSON structure
  - Dot notation supported for nested fields
  - Missing fields return None (not error)
  - Custom signals can be registered via decorator
- **Status**: [x] Complete

### T-2.4: Implement Evaluator Core

- **Description**: Create evaluator.py that runs Layer 1 and Layer 2 evaluations against traces
- **Dependencies**: T-2.1, T-2.2, T-2.3
- **Files**:
  - Create: `backend/src/evaluation/evaluator.py`
- **Acceptance**:
  - `Evaluator.__init__()` loads criteria from config
  - `Evaluator.evaluate(trace)` runs all applicable criteria
  - Layer 1: binary pass/fail based on threshold
  - Layer 2: quantitative with pass/warning/fail
  - Layer 3: skipped with result="skipped"
  - Results attached to trace.evaluations dict
  - Disabled criteria are skipped
- **Status**: [x] Complete

### T-2.5: Implement Layer 1 Evaluation Logic

- **Description**: Implement binary gate evaluation for Layer 1 criteria
- **Dependencies**: T-2.4
- **Files**:
  - Modify: `backend/src/evaluation/evaluator.py`
- **Acceptance**:
  - Threshold "must be valid JSON" checks JSON parseability
  - Threshold "must be null" checks for None
  - Threshold "must not be empty" checks for truthy value
  - Custom threshold expressions supported (basic)
  - Result is always "pass" or "fail"
- **Status**: [x] Complete

### T-2.6: Implement Layer 2 Evaluation Logic

- **Description**: Implement quantitative metric evaluation for Layer 2 criteria with thresholds and warnings
- **Dependencies**: T-2.4
- **Files**:
  - Modify: `backend/src/evaluation/evaluator.py`
- **Acceptance**:
  - Threshold "< 3000" compares numeric value
  - Threshold "p95 < 3000" noted for future (evaluates as single value for now)
  - Warning threshold triggers "warning" result
  - Actual value included in EvaluationResult
  - Non-numeric signals handled gracefully
- **Status**: [x] Complete

### T-2.7: Create Example evaluation.yaml

- **Description**: Create evaluation.yaml with example criteria for a generic agent demonstrating all patterns
- **Dependencies**: T-2.2
- **Files**:
  - Create: `backend/evaluation.yaml`
- **Acceptance**:
  - Includes Layer 1: valid_output, no_errors
  - Includes Layer 2: latency, token_efficiency
  - Includes Layer 3 example (disabled by default)
  - Comments explain each criterion
  - Passes validation
- **Status**: [x] Complete

### T-2.8: Integrate Evaluator into Tracer

- **Description**: Update Tracer to run evaluations before S3 write
- **Dependencies**: T-2.4, T-1.3
- **Files**:
  - Modify: `backend/src/evaluation/tracer.py`
- **Acceptance**:
  - Tracer accepts optional Evaluator in constructor
  - Evaluator.evaluate() called before _write_trace()
  - If no Evaluator, traces stored without evaluations
  - Evaluation errors logged but don't prevent trace storage
- **Status**: [x] Complete

### T-2.9: Write Evaluator Tests

- **Description**: Create comprehensive tests for evaluator, criteria loader, and signals
- **Dependencies**: T-2.4, T-2.5, T-2.6
- **Files**:
  - Create: `backend/tests/test_evaluator.py`
  - Create: `backend/tests/test_criteria.py`
- **Acceptance**:
  - Test Layer 1 pass/fail scenarios
  - Test Layer 2 pass/warning/fail scenarios
  - Test criteria loading from valid YAML
  - Test criteria loading with invalid YAML (error handling)
  - Test signal extraction for all built-in signals
  - Test missing signal handling
  - All tests pass with `pytest`
- **Status**: [x] Complete

---

## Critical Path

Tasks that block other work and should be prioritized:

1. **T-1.1** → T-1.2 → T-1.3 → T-1.4 (core tracing chain)
2. **T-1.5** (can run parallel with T-1.1-T-1.4, needed for integration)
3. **T-2.1** → T-2.2 → T-2.4 (evaluation chain depends on T-1.2)
4. **T-2.8** (integration point between Phase 1 and 2)

## Parallelization Opportunities

Tasks that can be worked on simultaneously:

**Parallel Group 1** (start immediately):
- T-1.5 (SAM template)
- T-1.6 (requirements.txt)
- T-1.1 (module structure)

**Parallel Group 2** (after T-1.2):
- T-1.3 (tracer)
- T-2.1 (evaluation models)
- T-2.3 (signals)

**Parallel Group 3** (after core implementation):
- T-1.9 (tracer tests)
- T-2.9 (evaluator tests)

---

## File Checklist

All files that will be created or modified:

**New Files (11)**:
- [x] `backend/src/evaluation/__init__.py`
- [x] `backend/src/evaluation/models.py`
- [x] `backend/src/evaluation/tracer.py`
- [x] `backend/src/evaluation/client.py`
- [x] `backend/src/evaluation/criteria.py`
- [x] `backend/src/evaluation/signals.py`
- [x] `backend/src/evaluation/evaluator.py`
- [x] `backend/evaluation.yaml`
- [x] `backend/tests/test_tracer.py`
- [x] `backend/tests/test_evaluator.py`
- [x] `backend/tests/test_criteria.py`

**Modified Files (3)**:
- [x] `template.yaml`
- [x] `backend/requirements.txt`
- [x] `backend/src/handler.py`

---

## Definition of Done (Phase 1)

- [x] TracedAnthropicClient wraps Claude SDK calls
- [x] Traces captured with all required fields
- [x] Traces stored in S3 with correct path structure
- [x] Trace retrieval API returns traces by ID and with filters
- [x] All tracer tests pass
- [x] Overhead < 50ms (async write doesn't block)

## Definition of Done (Phase 2)

- [x] evaluation.yaml schema defined and validated
- [x] Layer 1 evaluations run on every trace
- [x] Layer 2 evaluations run on every trace
- [x] Evaluation results attached to traces before storage
- [x] Example evaluation.yaml demonstrates all patterns
- [x] All evaluator tests pass
- [x] New criteria addable without code changes

---

## Progress Log

| Date | Tasks Completed | Notes |
|------|-----------------|-------|
| 2026-01-22 | T-1.1 through T-2.9 | All Phase 1-2 tasks completed. 41 tests passing. |
