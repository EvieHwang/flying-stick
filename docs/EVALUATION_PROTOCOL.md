# Agent Evaluation Design: A Structured Conversation Protocol

This document provides a systematic process for defining what to evaluate in an AI agent. It's designed to help a product manager move quickly from "I need to evaluate this agent" to "here's my evaluation plan" through a structured conversation—either with themselves, a collaborator, or an LLM assistant.

---

## Overview

The process has five steps:

1. **Walk through each pillar** — Generate candidate criteria
2. **Assign evaluation types** — Binary, quantitative, or judgment-based
3. **Identify signals** — What's observable?
4. **Compile the grid** — One table with everything
5. **Sort by layer** — Group for implementation

The output is a prioritized list of evaluation criteria, organized by how they'll be measured.

---

## Step 1: Walk Through Each Pillar

For each of the four APF pillars, ask: **"What matters for this agent?"**

Don't try to be comprehensive—focus on what's most important for your specific use case.

### Effectiveness (Outcome-Oriented)
*Did the agent achieve its goal?*

Questions to consider:
- What does "correct" mean? Is it binary or graded?
- Are some errors worse than others? (asymmetric costs)
- Does the agent need to be complete, or is partial success okay?
- Are there constraints it must follow?

Common criteria: Accuracy, completeness, constraint adherence, goal achievement rate

### Efficiency (Effort-Oriented)
*How much did it cost to achieve the goal?*

Questions to consider:
- What's the latency budget? When does it feel slow?
- Does cost per request matter at your scale?
- Should the agent use tools sparingly or liberally?
- How many steps/iterations are acceptable?

Common criteria: Latency, token cost, tool efficiency, steps to completion

### Reliability (Consistency-Oriented)
*Can you trust the agent to behave predictably?*

Questions to consider:
- Should the same input always produce the same output?
- Does the agent's confidence score mean anything?
- How much variance across runs is acceptable?
- Does performance need to be stable across versions?

Common criteria: Consistency, confidence calibration, variance, regression resistance

### Trustworthiness (Human-Centered)
*Would a human trust this agent?*

Questions to consider:
- Does the agent explain its reasoning? Should it?
- Could the agent hallucinate or make things up?
- Are there safety concerns or harmful outputs to avoid?
- Would a user feel comfortable acting on this output?

Common criteria: Transparency, groundedness, safety, user confidence

---

## Step 2: Assign Evaluation Types

For each criterion you identified, decide how it should be evaluated:

### Layer 1: Binary Gate
- Yes/no, pass/fail
- Must-pass criteria—if any fail, the system is broken
- No partial credit

*Examples: Valid output format, no errors, response within timeout*

### Layer 2: Quantitative Metric
- Numeric score with a threshold
- Allows comparison across runs and versions
- Can track trends over time

*Examples: Accuracy ≥ 85%, latency p95 < 5s, consistency ≥ 90%*

### Layer 3: Human Judgment
- Subjective quality assessment
- Requires human review or calibrated LLM-as-Judge
- Often uses Likert scales (1-5) or comparative ranking

*Examples: Reasoning quality, "would you ship this?", overall satisfaction*

**Guideline:** Start with Layer 1 and 2 where possible. Layer 3 is expensive—reserve it for criteria that genuinely require judgment.

---

## Step 3: Identify Signals

For each criterion, ask: **"What observable output tells me about this?"**

A signal is something the agent produces that you can capture and measure. If no signal exists, you have three options:

1. **Instrument it** — Modify the agent to output the signal
2. **Infer it** — Derive the signal from other outputs
3. **Defer it** — Accept you can't measure this criterion yet

**Common signal sources:**
- Agent response fields (classification, confidence, reasoning, etc.)
- Metadata (latency, token count, tool calls)
- Comparison to ground truth (test dataset with known answers)
- Human feedback (thumbs up/down, corrections)

**Watch for gaps:** If you care about a criterion but can't observe it, that's a problem to solve before implementation.

---

## Step 4: Compile the Grid

Now assemble everything into a single table:

| Criterion | Pillar | Layer | Signal | Threshold |
|-----------|--------|-------|--------|-----------|
| *name* | *E/Ef/R/T* | *1/2/3* | *what you observe* | *pass condition* |

**Example:**

| Criterion | Pillar | Layer | Signal | Threshold |
|-----------|--------|-------|--------|-----------|
| Valid output | Effectiveness | 1 | response format | Must be valid |
| Accuracy | Effectiveness | 2 | output vs ground truth | ≥ 85% |
| Latency | Efficiency | 2 | response time | p95 < 5s |
| Consistency | Reliability | 2 | N runs same input | ≥ 90% agreement |
| Reasoning quality | Trustworthiness | 3 | reasoning text | LLM-as-Judge pass |

This grid is your evaluation specification.

---

## Step 5: Sort by Layer

Reorganize the grid by evaluation type. This tells you what to build:

### Binary Gates (Layer 1)
These run first. If any fail, stop—the system isn't working.

| Criterion | Signal | Pass Condition |
|-----------|--------|----------------|
| ... | ... | ... |

### Quantitative Metrics (Layer 2)
These produce scores. Set thresholds for pass/warning/fail.

| Criterion | Signal | Threshold | Pillar |
|-----------|--------|-----------|--------|
| ... | ... | ... | ... |

### Human Judgment (Layer 3)
These require LLM-as-Judge or human review. Define the evaluation prompt or rubric.

| Criterion | Signal | Evaluation Method |
|-----------|--------|-------------------|
| ... | ... | ... |

---

## Tips for Moving Quickly

**Start narrow:** You don't need to evaluate everything. Pick 3-5 criteria that matter most for your current stage.

**Use placeholder thresholds:** Don't get stuck deciding if accuracy should be 85% or 87%. Pick something reasonable, run a baseline, then refine.

**Defer Layer 3:** Human judgment is expensive. Start with binary gates and quantitative metrics. Add LLM-as-Judge later for criteria that truly need it.

**Track diagnostics:** Some metrics are worth tracking even without a threshold. You'll use the data to set thresholds later.

**Accept gaps:** If you can't observe something, note it and move on. Perfect observability isn't required to start evaluating.

---

## The Conversation Protocol

If you're working with a collaborator or LLM assistant, here's how to structure the conversation:

1. **"Let's walk through Effectiveness. What matters for this agent?"**
   - Discuss, identify 1-3 criteria

2. **"Now Efficiency..."** (repeat for each pillar)

3. **"For each of these criteria, is it binary, quantitative, or judgment-based?"**
   - Assign layers

4. **"What signal do we have for each one?"**
   - Identify observables, flag gaps

5. **"Let me compile the grid and sort by layer."**
   - Produce the evaluation specification

6. **"What's our starting threshold for each?"**
   - Set initial targets, note which are estimates

This protocol ensures you don't skip important dimensions while keeping the conversation focused and efficient.
