# Technical Plan: AI Evaluation Infrastructure

**Spec**: [spec.md](./spec.md)
**Created**: 2026-01-22
**Status**: Draft
**Scope**: Phase 1 (Tracing) and Phase 2 (Evaluation Engine)

## Architecture Overview

The evaluation infrastructure adds a tracing and evaluation layer between application code and the Claude API. Traces flow to S3 for persistent storage, with optional evaluation criteria applied before storage.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Code                                 │
│                                                                          │
│     handler.py                                                           │
│         │                                                                │
│         ▼                                                                │
│   ┌─────────────────┐                                                   │
│   │ TracedAnthropic │  ◄── Wraps standard Anthropic client             │
│   │     Client      │                                                    │
│   └────────┬────────┘                                                   │
│            │                                                             │
│            ▼                                                             │
│   ┌─────────────────┐      ┌─────────────────┐                         │
│   │    Tracer       │─────►│   Evaluator     │                         │
│   │                 │      │                 │                         │
│   │ - Capture call  │      │ - Load criteria │                         │
│   │ - Time request  │      │ - Run Layer 1   │                         │
│   │ - Extract tokens│      │ - Run Layer 2   │                         │
│   └────────┬────────┘      └────────┬────────┘                         │
│            │                        │                                   │
│            └───────────┬────────────┘                                   │
│                        ▼                                                │
│                 ┌─────────────┐                                         │
│                 │    Trace    │  (with evaluations attached)            │
│                 └──────┬──────┘                                         │
│                        │                                                │
└────────────────────────┼────────────────────────────────────────────────┘
                         │ async write
                         ▼
                  ┌─────────────┐
                  │     S3      │
                  │             │
                  │ /traces/    │
                  │   {agent}/  │
                  │     {date}/ │
                  │       {id}  │
                  └─────────────┘
```

## Directory Structure

```
backend/
├── src/
│   ├── evaluation/
│   │   ├── __init__.py           # Exports public API
│   │   ├── client.py             # TracedAnthropicClient wrapper
│   │   ├── tracer.py             # Trace capture and S3 storage
│   │   ├── evaluator.py          # Run evaluations against traces
│   │   ├── criteria.py           # Load and validate criteria config
│   │   ├── signals.py            # Built-in signal extractors
│   │   └── models.py             # Dataclasses (Trace, Criterion, Result)
│   ├── handler.py                # (existing) Updated to use TracedClient
│   └── utils/
│       └── secrets.py            # (existing)
├── evaluation.yaml               # Evaluation criteria configuration
├── tests/
│   ├── test_handler.py           # (existing)
│   ├── test_tracer.py            # Tracer unit tests
│   ├── test_evaluator.py         # Evaluator unit tests
│   └── test_criteria.py          # Config loading tests
└── requirements.txt              # Add pyyaml, pydantic

template.yaml                     # Add S3 bucket, IAM permissions
```

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Trace Storage | S3 | Cost-efficient ($0.023/GB), scalable, no provisioning, queryable via Athena later |
| Trace Format | JSON | Human-readable, queryable, standard |
| Config Format | YAML | Readable, standard for config, supports comments |
| Validation | Pydantic | Type-safe, great error messages, widely used |
| Async Write | ThreadPoolExecutor | Simple, works in Lambda, avoids blocking |

## Implementation Phases

### Phase 1: Core Tracing

**Goal**: Every Claude API call is traced and stored in S3 automatically.

- [ ] Create `evaluation/` module structure
- [ ] Implement `models.py` with Trace, TraceRequest, TraceResponse, TraceMetrics dataclasses
- [ ] Implement `tracer.py` with trace capture and async S3 write
- [ ] Implement `client.py` with TracedAnthropicClient wrapper
- [ ] Update `template.yaml` with S3 bucket and IAM permissions
- [ ] Add trace retrieval API endpoints to handler
- [ ] Write tests for tracer

**Verification**: Make Claude API call, verify trace JSON appears in S3 within 5 seconds.

### Phase 2: Evaluation Engine

**Goal**: Traces are evaluated against configured criteria before storage.

- [ ] Implement `models.py` additions (EvaluationCriterion, EvaluationResult)
- [ ] Implement `criteria.py` for loading and validating evaluation.yaml
- [ ] Implement `signals.py` with built-in signal extractors
- [ ] Implement `evaluator.py` for running Layer 1 and Layer 2 evaluations
- [ ] Create example `evaluation.yaml` with common criteria
- [ ] Integrate evaluator into tracer (evaluate before S3 write)
- [ ] Write tests for evaluator and criteria

**Verification**: Configure latency criterion with 3000ms threshold, make call taking 2000ms, verify trace has "pass" evaluation.

## Module Design

### models.py

```python
from dataclasses import dataclass, field
from typing import Any, Literal
from datetime import datetime
import uuid

@dataclass
class TraceRequest:
    input: str
    model: str
    system_hash: str | None = None

@dataclass
class TraceResponse:
    output: Any  # str or dict for structured output
    raw_response: dict | None = None  # Truncated if large

@dataclass
class TraceMetrics:
    duration_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int

@dataclass
class ToolCall:
    name: str
    input: dict
    output: Any
    duration_ms: int

@dataclass
class EvaluationResult:
    criterion: str
    layer: int
    result: Literal["pass", "fail", "warning", "skipped"]
    value: Any | None = None
    message: str | None = None

@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    agent: str = "default"
    request: TraceRequest | None = None
    response: TraceResponse | None = None
    metrics: TraceMetrics | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    error: str | None = None
    evaluations: dict[str, EvaluationResult] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
```

### client.py

```python
from anthropic import Anthropic
from .tracer import Tracer

class TracedAnthropicClient:
    """Wrapper around Anthropic client that traces all calls."""

    def __init__(
        self,
        agent: str = "default",
        tracer: Tracer | None = None,
        **anthropic_kwargs
    ):
        self.client = Anthropic(**anthropic_kwargs)
        self.agent = agent
        self.tracer = tracer or Tracer()

    def messages_create(self, **kwargs) -> Message:
        """Traced version of messages.create()"""
        return self.tracer.trace_call(
            agent=self.agent,
            call_fn=lambda: self.client.messages.create(**kwargs),
            request_data=kwargs
        )
```

### tracer.py

```python
import boto3
import json
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from .models import Trace, TraceRequest, TraceResponse, TraceMetrics
from .evaluator import Evaluator

class Tracer:
    """Captures and stores traces for Claude API calls."""

    def __init__(
        self,
        bucket: str | None = None,
        evaluator: Evaluator | None = None,
        enabled: bool = True
    ):
        self.bucket = bucket or os.environ.get("TRACE_BUCKET")
        self.evaluator = evaluator or Evaluator()
        self.enabled = enabled
        self.s3 = boto3.client("s3")
        self.executor = ThreadPoolExecutor(max_workers=2)

    def trace_call(self, agent: str, call_fn, request_data: dict) -> Any:
        """Execute call_fn while capturing trace."""
        if not self.enabled:
            return call_fn()

        start = time.perf_counter()
        error = None
        response = None

        try:
            response = call_fn()
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            trace = self._build_trace(agent, request_data, response, error, duration_ms)

            # Run evaluations
            trace = self.evaluator.evaluate(trace)

            # Async write to S3
            self.executor.submit(self._write_trace, trace)

    def _write_trace(self, trace: Trace):
        """Write trace to S3 (runs async)."""
        date = trace.timestamp[:10]  # YYYY-MM-DD
        key = f"traces/{trace.agent}/{date}/{trace.trace_id}.json"

        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(asdict(trace), default=str),
            ContentType="application/json"
        )
```

### evaluator.py

```python
from .models import Trace, EvaluationResult
from .criteria import load_criteria
from .signals import extract_signal

class Evaluator:
    """Runs evaluations against traces."""

    def __init__(self, config_path: str = "evaluation.yaml"):
        self.criteria = load_criteria(config_path)

    def evaluate(self, trace: Trace) -> Trace:
        """Run all applicable evaluations and attach results."""
        agent_criteria = self.criteria.get(trace.agent, [])

        for criterion in agent_criteria:
            if not criterion.enabled:
                continue
            if criterion.layer == 3:
                continue  # Layer 3 not implemented

            result = self._evaluate_criterion(trace, criterion)
            trace.evaluations[criterion.name] = result

        return trace

    def _evaluate_criterion(self, trace: Trace, criterion) -> EvaluationResult:
        """Evaluate a single criterion against a trace."""
        value = extract_signal(trace, criterion.signal)

        if criterion.layer == 1:
            return self._evaluate_binary(criterion, value)
        else:
            return self._evaluate_quantitative(criterion, value)
```

## API Endpoints

### List Traces

```
GET /traces?agent={agent}&start={iso}&end={iso}&result={pass|fail|warning}
```

Response:
```json
{
  "traces": [
    {
      "trace_id": "...",
      "timestamp": "...",
      "agent": "classifier",
      "summary": {
        "duration_ms": 1250,
        "evaluations_passed": 3,
        "evaluations_failed": 0
      }
    }
  ],
  "next_token": "..."
}
```

### Get Trace

```
GET /traces/{trace_id}
```

Response: Full trace JSON as stored in S3.

## SAM Template Updates

```yaml
# Add to template.yaml

Resources:
  # ... existing resources ...

  TraceBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "{{PROJECT_NAME}}-traces-${Environment}"
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldTraces
            Status: Enabled
            ExpirationInDays: 30

  ApiFunction:
    # ... existing properties ...
    Policies:
      # ... existing policies ...
      - S3CrudPolicy:
          BucketName: !Ref TraceBucket
    Environment:
      Variables:
        TRACE_BUCKET: !Ref TraceBucket
```

## Data Flow

### Trace Capture Flow

1. Application calls `traced_client.messages_create()`
2. TracedAnthropicClient captures request data
3. Underlying Anthropic client makes API call
4. Response received, timing captured
5. Tracer builds Trace object
6. Evaluator runs Layer 1 and Layer 2 criteria
7. Evaluation results attached to trace
8. Trace written to S3 asynchronously
9. Response returned to application (blocking path complete)

### Trace Retrieval Flow

1. Client requests `GET /traces?agent=classifier&start=2026-01-20`
2. Lambda lists S3 objects matching prefix `traces/classifier/2026-01-2*`
3. For each object, fetch summary metadata (or first N bytes)
4. Return list with pagination token

## Rollback Points

Safe stopping points where the system remains functional:

1. **After Phase 1 tracing only**: Traces captured but no evaluation—still valuable for debugging
2. **After Phase 2 with empty config**: Evaluation infrastructure exists but no criteria defined—graceful no-op

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| S3 write latency impacts API response | Medium | Medium | Async write via ThreadPoolExecutor |
| Large responses bloat S3 costs | Low | Low | Truncate responses > 100KB |
| evaluation.yaml syntax errors | Medium | Low | Validate at startup, fail fast with clear error |
| Missing IAM permissions for S3 | Medium | High | Document in README, verify in CI |
| Thread pool exhaustion under load | Low | Medium | Max 2 workers, non-critical path |

## Open Questions

- [x] Storage backend? → **S3** (per user request)
- [ ] Should traces be stored per-environment? → Recommend single bucket with `environment` field in trace
- [x] Default retention period? → **30 days** via S3 lifecycle
- [ ] Should Layer 1 failures trigger CloudWatch Alarms? → Defer to Phase 4
