# GUARD Framework

**Generalized Unified Agent Risk Defense**

A systematic approach to implementing runtime protections for AI agents.

---

## Overview

GUARD is a framework for analyzing and implementing runtime guardrails in AI agent systems. It provides:

1. **Stage-based analysis** — Where can things go wrong?
2. **Threat categorization** — What type of risk is it?
3. **Response patterns** — How should the system react?
4. **Coverage mapping** — Are all risks addressed?

GUARD complements evaluation frameworks (like APF) by focusing on **prevention** rather than **measurement**:

| Framework | Focus | When | Question |
|-----------|-------|------|----------|
| **Evaluation (APF)** | Measure quality | Offline | "How well did it perform?" |
| **Guardrails (GUARD)** | Prevent harm | Runtime | "Should this be allowed?" |

---

## The Three Stages

GUARD analyzes risk at three points in the request lifecycle:

```
┌─────────┐     ┌────────────┐     ┌────────┐
│  INPUT  │ ──▶ │ BEHAVIORAL │ ──▶ │ OUTPUT │
└─────────┘     └────────────┘     └────────┘
   Before           During           After
   AI call        AI execution      AI response
```

### Stage 1: Input

**Question:** What can go wrong before the AI sees the request?

**Timing:** After receiving the request, before calling the AI API

**Common risks:**
- Excessively long input (token cost explosion)
- Empty or trivial input (wasted API call)
- Malformed request format (parsing errors)
- Request flooding (resource exhaustion)
- Prompt injection attempts (security)

**Typical guardrails:**
- Input length limits (min and max)
- Required field validation
- Format/schema validation
- Rate limiting
- Input sanitization

### Stage 2: Behavioral

**Question:** What can go wrong during AI execution?

**Timing:** During the agentic loop, while the AI is processing

**Common risks:**
- Excessive tool calls (cost, latency)
- Infinite loops (hung requests)
- Unauthorized tool usage (scope violation)
- Timeout exceeded (resource waste)
- Model escalation (cost)

**Typical guardrails:**
- Tool call limits
- Iteration limits
- Execution timeout
- Allowed tool whitelist
- Model restrictions

### Stage 3: Output

**Question:** What can go wrong with the AI's response?

**Timing:** After AI completes, before returning to client

**Common risks:**
- Invalid output format (downstream failures)
- Missing required fields (incomplete response)
- Out-of-bounds values (nonsensical output)
- Excessive verbosity (token waste, UX)
- Sensitive data exposure (security)

**Typical guardrails:**
- Schema validation
- Enum/category validation
- Bounds checking
- Output truncation
- PII detection/redaction

---

## The Four Threat Categories

Every guardrail addresses one or more threat categories:

### Cost

**Definition:** Risks that waste money or computational resources

**Examples:**
- Token explosion from long inputs
- Excessive API calls from tool loops
- Unnecessary model upgrades
- Timeout-induced retries

**Mitigation patterns:**
- Length limits
- Call count limits
- Timeout enforcement
- Model restrictions

### Quality

**Definition:** Risks that produce unusable or incorrect outputs

**Examples:**
- Invalid output format
- Missing required fields
- Out-of-range values
- Parsing failures

**Mitigation patterns:**
- Schema validation
- Required field checks
- Bounds validation
- Format enforcement

### Scope

**Definition:** Risks that exceed the agent's intended boundaries

**Examples:**
- Using unauthorized tools
- Off-topic responses
- Excessive output verbosity
- Capability escalation

**Mitigation patterns:**
- Tool whitelisting
- Output truncation
- Fixed capability set
- Response filtering

### Security

**Definition:** Risks that compromise data or system integrity

**Examples:**
- Prompt injection attacks
- PII exposure in outputs
- Credential leakage
- Unauthorized data access

**Mitigation patterns:**
- Input sanitization
- Output redaction
- Isolation boundaries
- Access controls

---

## Response Types

When a guardrail triggers, it must respond. GUARD defines four response types:

### Block

**Behavior:** Reject the request entirely, return an error

**When to use:**
- Hard failures that cannot be recovered
- Security violations
- Invalid input that cannot be processed

**Example:** Invalid JSON in request body → 400 Bad Request

### Fallback

**Behavior:** Use a safe default value instead of the problematic one

**When to use:**
- Recoverable quality issues
- Non-critical field failures
- Graceful degradation is acceptable

**Example:** Missing confidence score → Use "UNKNOWN" default

### Truncate

**Behavior:** Limit the size of the output

**When to use:**
- Verbose responses exceeding limits
- Cost control on output tokens
- UX concerns with long text

**Example:** Reasoning > 500 chars → Truncate with "..."

### Flag

**Behavior:** Allow the request but log for review

**When to use:**
- Suspicious but not definitively harmful
- Monitoring for emerging patterns
- Soft limits that shouldn't block

**Example:** Unusual input pattern → Log and continue

---

## Detection Methods

Guardrails need to detect when conditions are violated:

### Deterministic

**Characteristics:**
- Rule-based logic
- Predictable outcomes
- Fast execution
- Easy to test

**Examples:**
- `len(input) > 2000`
- `category not in VALID_CATEGORIES`
- `tool_call_count > 3`

**Preference:** Use deterministic detection whenever possible

### ML-Based

**Characteristics:**
- Learned patterns
- Probabilistic outcomes
- Higher latency
- Requires training data

**Examples:**
- Prompt injection classifier
- PII detection model
- Toxicity scoring

**Preference:** Use sparingly, only when rules are insufficient

---

## Coverage Matrix

Use this matrix to ensure comprehensive protection:

|  | Input | Behavioral | Output |
|--|-------|------------|--------|
| **Cost** | | | |
| **Quality** | | | |
| **Scope** | | | |
| **Security** | | | |

For each cell, identify:
- What risks exist at this intersection?
- What guardrails address them?
- Are there acceptable gaps?

Not every cell needs a guardrail. Some intersections have no meaningful risk, or the risk is acceptable for the use case.

---

## Structural vs Runtime Guardrails

Some guardrails are implemented at runtime (code checks). Others are structural (architectural constraints that make violations impossible).

### Structural Guardrails

**Definition:** Architectural decisions that eliminate risk categories entirely

**Characteristics:**
- Cannot be bypassed at runtime
- No code required to enforce
- Often invisible to the application

**Examples:**
- **Fixed tool set:** Agent literally cannot call undefined tools
- **Lambda isolation:** No network egress except allowed endpoints
- **Single model:** No code path to upgrade models
- **No database access:** Agent cannot leak data it can't reach

**Preference:** Structural guardrails are stronger than runtime checks. Prefer them when possible.

### Runtime Guardrails

**Definition:** Code that checks conditions and responds

**Characteristics:**
- Flexible and configurable
- Must be correctly implemented
- Can be logged and monitored

**Examples:**
- Input length validation
- Output schema checking
- Tool call counting

---

## Implementation Guidance

### Execution Order

Guardrails should execute in stage order, with early termination:

```
1. Run INPUT guardrails
   └─ If any BLOCK → Return error, stop
   
2. Execute AI (with BEHAVIORAL guardrails active)
   └─ If any BLOCK → Return error, stop
   
3. Run OUTPUT guardrails
   └─ If any BLOCK → Return error
   └─ Apply TRUNCATE/FALLBACK as needed
   
4. Return response
```

### Logging

All guardrail activations should be logged:

```json
{
  "guardrail": "max_input_length",
  "stage": "input",
  "threat": "cost",
  "triggered": true,
  "response": "block",
  "details": {"input_length": 5200, "max_allowed": 2000}
}
```

### Configuration

Guardrails should be configurable without code changes:

```yaml
guardrails:
  - name: max_input_length
    stage: input
    threat: cost
    enabled: true
    threshold: 2000
    response: block
```

### Testing

Each guardrail should have explicit tests:

- Test that it triggers when conditions are met
- Test that it doesn't trigger when conditions aren't met
- Test the response behavior (block returns error, truncate shortens, etc.)

---

## Guardrails vs Evaluations

Understanding when to use each:

| Concern | Use Guardrail | Use Evaluation | Use Both |
|---------|---------------|----------------|----------|
| Invalid format | ✓ Block it | | |
| Slow response | ✓ Timeout | ✓ Measure p95 | ✓ |
| Wrong answer | | ✓ Measure accuracy | |
| High cost | ✓ Limit tokens | ✓ Track spend | ✓ |
| Verbose output | ✓ Truncate | | |
| Poor reasoning | | ✓ LLM-as-Judge | |
| PII in output | ✓ Redact | | |

**Rule of thumb:**
- If it's a **catastrophic failure** → Guardrail (runtime)
- If it's a **quality gradient** → Evaluation (offline)
- If it's **both** → Implement guardrail AND track metric

---

## Anti-Patterns

### Over-Blocking

**Problem:** Too aggressive guardrails that reject valid requests

**Symptoms:**
- High false positive rate
- User complaints about rejected inputs
- Overly restrictive thresholds

**Solution:** Start permissive, tighten based on data

### Silent Fallbacks

**Problem:** Using fallback values without logging

**Symptoms:**
- Quality issues go unnoticed
- Can't distinguish real values from defaults
- No signal for improvement

**Solution:** Always log when fallbacks are used

### Guardrail Gaps

**Problem:** Missing coverage at critical intersections

**Symptoms:**
- Costs spike unexpectedly
- Invalid outputs reach production
- Security incidents

**Solution:** Use the coverage matrix systematically

### Runtime-Only Thinking

**Problem:** Implementing runtime checks when structural guardrails would be stronger

**Symptoms:**
- Complex validation code
- Edge cases that slip through
- Ongoing maintenance burden

**Solution:** Ask "Can I make this impossible instead of just detected?"

---

## Checklist: Designing Guardrails for a New Agent

1. **List the agent's capabilities**
   - What tools can it use?
   - What outputs can it produce?
   - What data can it access?

2. **Walk through each stage**
   - Input: What bad inputs could arrive?
   - Behavioral: What could go wrong during execution?
   - Output: What bad outputs could be produced?

3. **Categorize by threat**
   - Cost: What wastes money?
   - Quality: What produces bad output?
   - Scope: What exceeds boundaries?
   - Security: What leaks or harms?

4. **Choose responses**
   - What should block?
   - What should fallback?
   - What should truncate?
   - What should flag?

5. **Identify structural guardrails**
   - What's already impossible by design?
   - What could be made impossible?

6. **Fill the coverage matrix**
   - Are all critical intersections covered?
   - Are gaps acceptable?

7. **Set thresholds**
   - Start with reasonable estimates
   - Plan to refine based on production data

8. **Write tests**
   - Each guardrail should have explicit test coverage

---

## Summary

GUARD provides a systematic approach to AI agent safety:

- **Three stages:** Input → Behavioral → Output
- **Four threats:** Cost, Quality, Scope, Security
- **Four responses:** Block, Fallback, Truncate, Flag
- **Two detection methods:** Deterministic (preferred), ML-based
- **Two guardrail types:** Structural (strongest), Runtime (flexible)

The goal is comprehensive, proportionate protection—catching catastrophic failures at runtime while leaving quality measurement to offline evaluation.
