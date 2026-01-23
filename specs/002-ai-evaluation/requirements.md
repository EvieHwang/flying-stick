# AI Evaluation Infrastructure: Requirements Document

## Executive Summary

This document specifies requirements for adding AI agent evaluation infrastructure to the flying-stick template. The goal is to ensure every app built from this template has built-in observability, tracing, and evaluation capabilities from day one.

The evaluation framework follows the **Agent Performance Framework (APF)** with four pillars: Effectiveness, Efficiency, Reliability, and Trustworthiness. It implements a three-layer evaluation approach: Binary Gates, Quantitative Metrics, and Human Judgment.

---

## Problem Statement

### Current State
- Apps built from the template have no standardized way to trace AI agent behavior
- Evaluation criteria are defined ad-hoc per project, if at all
- No infrastructure exists for capturing, storing, or visualizing agent performance
- Debugging AI behavior requires manual log inspection

### Target State
- Every app has evaluation infrastructure from the start
- Traces are captured automatically for all AI interactions
- Evaluation criteria can be defined per-agent using a structured protocol
- A dashboard visualizes agent performance dynamically
- The infrastructure supports later development of sophisticated evaluation features

---

## Core Concepts

### The Four Pillars (APF)

| Pillar | Focus | Key Question |
|--------|-------|--------------|
| **Effectiveness** | Outcome-oriented | Did the agent achieve its goal? |
| **Efficiency** | Effort-oriented | How much did it cost to achieve the goal? |
| **Reliability** | Consistency-oriented | Can you trust the agent to behave predictably? |
| **Trustworthiness** | Human-centered | Would a human trust this agent? |

### The Three Evaluation Layers

| Layer | Type | Characteristics |
|-------|------|-----------------|
| **Layer 1** | Binary Gate | Pass/fail, must-pass criteria |
| **Layer 2** | Quantitative Metric | Numeric score with threshold |
| **Layer 3** | Human Judgment | Subjective assessment, LLM-as-Judge |

### Key Entities

**Trace**: A record of a single AI interaction, including:
- Request (input, context, parameters)
- Response (output, metadata)
- Timing (start, end, duration)
- Token usage (input, output, total)
- Tool calls (if any)
- Evaluation results (per criterion)

**Evaluation Criterion**: A specific aspect of agent performance to measure:
- Name and description
- Pillar (Effectiveness/Efficiency/Reliability/Trustworthiness)
- Layer (1/2/3)
- Signal (what to observe)
- Threshold (pass condition)

**Evaluation Grid**: The complete set of criteria for an agent, organized by layer.

---

## Functional Requirements

### FR-1: Trace Capture

**FR-1.1**: Template MUST include a tracing module that wraps AI API calls (Claude SDK)

**FR-1.2**: Traces MUST capture:
- Unique trace ID (UUID)
- Timestamp (ISO 8601)
- Agent identifier (which agent/feature)
- Input (prompt, context, system message hash)
- Output (response text, structured output if applicable)
- Latency (ms)
- Token counts (input, output, total)
- Model used
- Tool calls (name, input, output, duration) if applicable
- Error information if request failed
- Custom metadata (extensible key-value pairs)

**FR-1.3**: Tracing MUST be low-overhead and not significantly impact latency

**FR-1.4**: Tracing MUST work in both Lambda and local environments

**FR-1.5**: Traces MUST be stored for later analysis (options: CloudWatch, S3, or DynamoDB)

### FR-2: Evaluation Criteria Definition

**FR-2.1**: Template MUST include a schema for defining evaluation criteria (YAML or JSON)

**FR-2.2**: Criteria definition MUST support:
- Name and description
- Pillar assignment (Effectiveness/Efficiency/Reliability/Trustworthiness)
- Layer assignment (1/2/3)
- Signal specification (what field/computation to evaluate)
- Threshold specification (pass condition, warning threshold if applicable)
- Enabled/disabled flag

**FR-2.3**: Template MUST include example criteria definitions for common patterns:
- Output format validation (Layer 1)
- Latency threshold (Layer 2)
- Token efficiency (Layer 2)
- Response consistency (Layer 2)

**FR-2.4**: Criteria definitions SHOULD live in a configuration file (e.g., `evaluation.yaml`)

### FR-3: Evaluation Execution

**FR-3.1**: Layer 1 (Binary) evaluations MUST run automatically on every trace

**FR-3.2**: Layer 2 (Quantitative) evaluations MUST run automatically on every trace

**FR-3.3**: Layer 3 (Judgment) evaluations SHOULD be triggerable on-demand or via sampling

**FR-3.4**: Evaluation results MUST be attached to traces

**FR-3.5**: Evaluation failures (Layer 1) SHOULD be loggable as alerts

### FR-4: Evaluation Grid Protocol

**FR-4.1**: Template MUST include the Agent Evaluation Design Protocol document

**FR-4.2**: Template SHOULD include a questionnaire/prompt template for generating evaluation criteria for a new agent

**FR-4.3**: The questionnaire SHOULD walk through each pillar and layer systematically

**FR-4.4**: Output of the questionnaire SHOULD be a valid criteria configuration file

### FR-5: Visualization Dashboard

**FR-5.1**: Template MUST include a dashboard component for visualizing evaluation results

**FR-5.2**: Dashboard MUST display:
- Summary metrics (pass rates by layer, by pillar)
- Time-series charts (metrics over time)
- Individual trace inspection
- Evaluation grid status (which criteria passing/failing)

**FR-5.3**: Dashboard MUST support filtering by:
- Time range
- Agent/feature
- Evaluation result (pass/fail/warning)
- Pillar
- Layer

**FR-5.4**: Dashboard SHOULD update dynamically (polling or websocket)

**FR-5.5**: Dashboard SHOULD use the existing design system (information-dense, dark mode support)

### FR-6: Storage and Retrieval

**FR-6.1**: Traces MUST be queryable by:
- Time range
- Agent identifier
- Evaluation result
- Trace ID

**FR-6.2**: Storage SHOULD support retention policies (e.g., delete traces older than 30 days)

**FR-6.3**: Storage SHOULD be cost-efficient for high-volume tracing

**FR-6.4**: Consider options: CloudWatch Logs (simple), S3 + Athena (scalable), DynamoDB (queryable)

---

## Non-Functional Requirements

### NFR-1: Performance
- Tracing overhead MUST be < 50ms per request
- Dashboard SHOULD load in < 2 seconds

### NFR-2: Extensibility
- New evaluation criteria MUST be addable without code changes (config only)
- Custom signals SHOULD be definable via simple functions

### NFR-3: Cost Consciousness
- Default storage SHOULD use pay-per-use services
- Layer 3 (LLM-as-Judge) SHOULD be opt-in to control costs

### NFR-4: Privacy
- Traces MAY contain sensitive data; storage SHOULD be encrypted
- PII handling SHOULD be configurable (redact, hash, or store)

---

## Proposed File Structure

```
backend/
├── src/
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── tracer.py           # Trace capture and storage
│   │   ├── evaluator.py        # Run evaluations against traces
│   │   ├── criteria.py         # Load and validate criteria config
│   │   └── signals.py          # Built-in signal extractors
│   └── utils/
│       └── secrets.py          # (existing)
├── evaluation.yaml             # Evaluation criteria configuration
└── tests/
    └── test_evaluation.py

frontend/
├── src/
│   ├── components/
│   │   ├── evaluation/
│   │   │   ├── Dashboard.tsx       # Main evaluation dashboard
│   │   │   ├── MetricsSummary.tsx  # Summary cards
│   │   │   ├── TimeSeriesChart.tsx # Metrics over time
│   │   │   ├── TraceInspector.tsx  # Individual trace view
│   │   │   └── EvalGrid.tsx        # Criteria status grid
│   │   └── ui/                 # (existing shadcn components)
│   └── lib/
│       └── evaluation.ts       # API client for evaluation data

docs/
├── EVALUATION.md               # How to use evaluation infrastructure
└── EVALUATION_PROTOCOL.md      # Agent Evaluation Design Protocol
```

---

## Example: Evaluation Configuration

```yaml
# evaluation.yaml
version: "1.0"

agents:
  classifier:
    description: "Product classification agent"
    criteria:
      # Layer 1: Binary Gates
      - name: valid_output
        pillar: effectiveness
        layer: 1
        signal: response.format
        threshold: "must be valid JSON with 'category' field"
        
      - name: no_errors
        pillar: effectiveness
        layer: 1
        signal: error
        threshold: "must be null"

      # Layer 2: Quantitative Metrics
      - name: latency
        pillar: efficiency
        layer: 2
        signal: duration_ms
        threshold: "p95 < 3000"
        warning: "p95 < 5000"
        
      - name: token_efficiency
        pillar: efficiency
        layer: 2
        signal: total_tokens
        threshold: "< 2000"
        
      - name: confidence_accuracy
        pillar: reliability
        layer: 2
        signal: "correlation(response.confidence, is_correct)"
        threshold: "> 0.7"

      # Layer 3: Human Judgment
      - name: reasoning_quality
        pillar: trustworthiness
        layer: 3
        signal: response.reasoning
        evaluation_method: llm_as_judge
        prompt: "Rate the quality of this reasoning on a scale of 1-5..."
        threshold: "mean >= 4"
        sample_rate: 0.1  # Only evaluate 10% of traces
```

---

## Example: Trace Structure

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-23T04:30:00Z",
  "agent": "classifier",
  "request": {
    "input": "Classify this product: ...",
    "model": "claude-sonnet-4-20250514",
    "system_hash": "a1b2c3d4"
  },
  "response": {
    "output": {"category": "Electronics", "confidence": 0.92},
    "reasoning": "The product description mentions..."
  },
  "metrics": {
    "duration_ms": 1250,
    "input_tokens": 450,
    "output_tokens": 120,
    "total_tokens": 570
  },
  "tool_calls": [],
  "evaluations": {
    "valid_output": {"layer": 1, "result": "pass"},
    "no_errors": {"layer": 1, "result": "pass"},
    "latency": {"layer": 2, "value": 1250, "result": "pass"},
    "token_efficiency": {"layer": 2, "value": 570, "result": "pass"}
  },
  "metadata": {
    "request_id": "req_123",
    "user_id": "user_456"
  }
}
```

---

## Implementation Phases

### Phase 1: Core Tracing
- Implement `tracer.py` with trace capture
- Wrap Claude SDK calls
- Store traces to CloudWatch or S3
- Basic retrieval API

### Phase 2: Evaluation Engine
- Implement `criteria.py` for config loading
- Implement `evaluator.py` for Layer 1 and 2 evaluations
- Attach evaluations to traces
- Create `evaluation.yaml` with examples

### Phase 3: Dashboard MVP
- Summary metrics component
- Time-series chart (basic)
- Trace list with filtering
- Individual trace inspection

### Phase 4: Advanced Features
- Layer 3 (LLM-as-Judge) support
- Evaluation grid visualization
- Alerting on Layer 1 failures
- Protocol questionnaire generator

---

## Success Criteria

1. **Every AI call is traced**: Apps using the template automatically capture traces
2. **Evaluation is configurable**: New criteria can be added via YAML without code changes
3. **Dashboard provides visibility**: Users can see agent performance at a glance
4. **Infrastructure is extensible**: Later development can add sophisticated features
5. **Documentation is complete**: EVALUATION.md explains how to use the system

---

## Open Questions

- [ ] Storage backend preference? (CloudWatch Logs vs S3 + Athena vs DynamoDB)
- [ ] Should traces be stored per-environment (dev/staging/prod) or combined?
- [ ] What's the default retention period?
- [ ] Should Layer 3 (LLM-as-Judge) use Claude Haiku for cost efficiency?
- [ ] Should the dashboard be a separate route or embedded in the main app?

---

## References

- Agent Evaluation Design Protocol (attached)
- APF (Agent Performance Framework) - Four pillars model
- Anthropic SDK documentation for tracing hooks

---

## Instructions for Claude Code CLI

**Prompt to use:**

> "Here's a requirements document for adding AI evaluation infrastructure to the flying-stick template. Please:
> 1. Review the requirements
> 2. Create `specs/002-ai-evaluation/` with spec.md, plan.md, and tasks.md
> 3. Include the Agent Evaluation Design Protocol document as `docs/EVALUATION_PROTOCOL.md`
> 
> Focus on Phase 1 and 2 first (tracing and evaluation engine). Dashboard can come later. Storage should use S3 for cost efficiency."
