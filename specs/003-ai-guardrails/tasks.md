# Task Breakdown: AI Guardrails Infrastructure

**Plan**: [plan.md](./plan.md)
**Created**: 2026-01-22
**Status**: Phase 1-2 Complete
**Scope**: Phase 1 (Core Engine) and Phase 2 (Full Stage Coverage)

## Task Summary

| Phase | Tasks | Completed |
|-------|-------|-----------|
| Phase 1: Core Engine | 10 | 10 |
| Phase 2: Full Stage Coverage | 10 | 10 |
| **Total** | **20** | **20** |

---

## Phase 1: Core Engine

### T-1.1: Create Guardrails Module Structure

- **Description**: Create the `backend/src/guardrails/` directory with `__init__.py` that exports the public API
- **Dependencies**: None
- **Files**:
  - Create: `backend/src/guardrails/__init__.py`
- **Acceptance**: Module can be imported (`from src.guardrails import GuardrailEngine`)
- **Status**: [x] Complete

### T-1.2: Implement Data Models

- **Description**: Create dataclasses for GuardrailConfig, GuardrailResult, GuardrailContext, and GuardrailBlockError
- **Dependencies**: T-1.1
- **Files**:
  - Create: `backend/src/guardrails/models.py`
- **Acceptance**:
  - GuardrailConfig with name, stage, threat, detection, rule, response, enabled, etc.
  - GuardrailResult with name, stage, triggered, response, message, details
  - GuardrailContext with agent, request, output, tool_call_count, iteration_count
  - GuardrailBlockError with to_http_status() and to_response() methods
  - Stage validated as input/behavioral/output
  - Threat validated as cost/quality/scope/security
  - Response validated as block/fallback/truncate/flag
- **Status**: [x] Complete

### T-1.3: Implement Configuration Loader

- **Description**: Create config.py that loads and validates guardrails.yaml using Pydantic
- **Dependencies**: T-1.2
- **Files**:
  - Create: `backend/src/guardrails/config.py`
- **Acceptance**:
  - `load_guardrails(path)` returns dict of agent -> stage -> list of guardrails
  - Global guardrails merged with agent-specific guardrails
  - Invalid YAML raises clear error with line number
  - Invalid stage/threat/response values raise validation error
  - Missing file returns empty config (graceful fallback)
  - Disabled guardrails are included but marked
- **Status**: [x] Complete

### T-1.4: Implement Built-in Rules

- **Description**: Create rules.py with deterministic rule implementations and a rule registry
- **Dependencies**: T-1.2
- **Files**:
  - Create: `backend/src/guardrails/rules.py`
- **Acceptance**:
  - `@register_rule` decorator for adding new rules
  - Built-in rules: `max_length`, `min_length`, `required`, `valid_json`
  - Built-in rules: `valid_enum`, `in_range`, `required_fields`
  - Built-in rules: `max_tool_calls`, `max_iterations`, `allowed_tools`
  - `evaluate_rule(rule_str, context)` parses and executes rule
  - No use of `eval()` - custom safe parser
  - Unknown rules raise clear error
- **Status**: [x] Complete

### T-1.5: Implement Rule Parser

- **Description**: Create a safe rule parser that converts rule strings like `max_length(request.body.description, 2000)` into function calls
- **Dependencies**: T-1.4
- **Files**:
  - Modify: `backend/src/guardrails/rules.py`
- **Acceptance**:
  - Parses function-style rules: `function_name(arg1, arg2)`
  - Supports dot notation for nested access: `request.body.field`
  - Supports literal values: strings, numbers, lists
  - Supports comparison operators: `>`, `<`, `>=`, `<=`, `==`, `!=`
  - Returns boolean result
  - Raises clear error for malformed rules
- **Status**: [x] Complete

### T-1.6: Implement Guardrail Engine Core

- **Description**: Create engine.py with GuardrailEngine class that orchestrates guardrail execution
- **Dependencies**: T-1.3, T-1.4
- **Files**:
  - Create: `backend/src/guardrails/engine.py`
- **Acceptance**:
  - `__init__` accepts config_path, config_dict, fail_open
  - `_get_guardrails(agent, stage)` returns guardrails for agent/stage
  - `_evaluate_guardrail(config, context)` runs single guardrail
  - `get_summary()` returns all results organized by stage
  - `reset()` clears results for new request
  - Engine catches errors and respects fail_open setting
- **Status**: [x] Complete

### T-1.7: Implement Input Stage Guardrails

- **Description**: Implement input guardrail checking in the engine
- **Dependencies**: T-1.6
- **Files**:
  - Create: `backend/src/guardrails/input.py`
  - Modify: `backend/src/guardrails/engine.py`
- **Acceptance**:
  - `check_input(agent, request)` runs all input guardrails
  - Guardrails execute in defined order
  - Block response raises GuardrailBlockError immediately
  - Flag response logs but continues
  - Results accumulated for summary
  - Returns list of GuardrailResult
- **Status**: [x] Complete

### T-1.8: Create Example guardrails.yaml

- **Description**: Create guardrails.yaml with example configuration demonstrating all patterns
- **Dependencies**: T-1.3
- **Files**:
  - Create: `backend/guardrails.yaml`
- **Acceptance**:
  - Includes global guardrails (valid_json_body)
  - Includes agent-specific guardrails for "default" agent
  - Demonstrates input guardrails: max_length, min_length
  - Demonstrates behavioral guardrails: max_tool_calls, allowed_tools
  - Demonstrates output guardrails: valid_enum, truncate
  - Comments explain each guardrail
  - Passes validation
- **Status**: [x] Complete

### T-1.9: Write Configuration Tests

- **Description**: Create tests for configuration loading and validation
- **Dependencies**: T-1.3, T-1.8
- **Files**:
  - Create: `backend/tests/test_guardrails_config.py`
- **Acceptance**:
  - Test loading valid YAML config
  - Test loading from dict
  - Test missing file returns empty config
  - Test invalid stage raises error
  - Test invalid threat raises error
  - Test invalid response raises error
  - Test global guardrails merged with agent-specific
  - All tests pass with `pytest`
- **Status**: [x] Complete

### T-1.10: Write Input Stage Tests

- **Description**: Create tests for input stage guardrails and rule evaluation
- **Dependencies**: T-1.7, T-1.4
- **Files**:
  - Create: `backend/tests/test_guardrails_input.py`
  - Create: `backend/tests/test_guardrails_rules.py`
- **Acceptance**:
  - Test max_length rule passes and fails correctly
  - Test min_length rule passes and fails correctly
  - Test required rule passes and fails correctly
  - Test valid_json rule passes and fails correctly
  - Test block response raises GuardrailBlockError
  - Test flag response logs but continues
  - Test engine.get_summary() returns correct structure
  - Test rule parser handles various formats
  - All tests pass with `pytest`
- **Status**: [x] Complete

---

## Phase 2: Full Stage Coverage

### T-2.1: Implement Behavioral Stage Guardrails

- **Description**: Implement behavioral guardrail checking with execution context tracking
- **Dependencies**: T-1.6
- **Files**:
  - Create: `backend/src/guardrails/behavioral.py`
  - Modify: `backend/src/guardrails/engine.py`
- **Acceptance**:
  - `check_behavioral(context, tool_name)` runs behavioral guardrails
  - Context tracks tool_call_count, iteration_count, start_time
  - max_tool_calls rule works with context
  - max_iterations rule works with context
  - allowed_tools rule checks tool_name against whitelist
  - Block response raises GuardrailBlockError
  - Results added to summary
- **Status**: [x] Complete

### T-2.2: Implement Output Stage Guardrails

- **Description**: Implement output guardrail checking with modification support
- **Dependencies**: T-1.6
- **Files**:
  - Create: `backend/src/guardrails/output.py`
  - Modify: `backend/src/guardrails/engine.py`
- **Acceptance**:
  - `check_output(agent, request, output)` runs output guardrails
  - Returns tuple of (modified_output, results)
  - Block response raises GuardrailBlockError
  - Truncate response modifies output field
  - Fallback response substitutes default value
  - Flag response logs but continues
  - Original output not mutated (deep copy)
- **Status**: [x] Complete

### T-2.3: Implement Truncate Response

- **Description**: Implement output truncation logic for long fields
- **Dependencies**: T-2.2
- **Files**:
  - Modify: `backend/src/guardrails/output.py`
- **Acceptance**:
  - Truncates string field to truncate_to length
  - Appends suffix (default "...")
  - Records original_length in result details
  - Handles nested field paths (output.reasoning)
  - Returns modified output copy
- **Status**: [x] Complete

### T-2.4: Implement Fallback Response

- **Description**: Implement fallback value substitution for output guardrails
- **Dependencies**: T-2.2
- **Files**:
  - Modify: `backend/src/guardrails/output.py`
- **Acceptance**:
  - Substitutes fallback_value for failed field
  - Records original_value in result details
  - Marks result as using fallback
  - Handles nested field paths
  - Works with any value type (string, dict, list, null)
- **Status**: [x] Complete

### T-2.5: Implement GuardrailContext Management

- **Description**: Create context management for tracking execution state across behavioral guardrails
- **Dependencies**: T-2.1
- **Files**:
  - Modify: `backend/src/guardrails/models.py`
  - Modify: `backend/src/guardrails/engine.py`
- **Acceptance**:
  - `create_context(agent, request)` returns new GuardrailContext
  - `update_context(context, tool_name)` increments counters
  - Context tracks elapsed time from start_time
  - Context accumulates tool_calls list
  - Engine can reuse context across multiple checks
- **Status**: [x] Complete

### T-2.6: Integrate with Tracer

- **Description**: Attach guardrail results to traces for observability
- **Dependencies**: T-2.1, T-2.2, evaluation module
- **Files**:
  - Modify: `backend/src/guardrails/engine.py`
  - Modify: `backend/src/evaluation/models.py`
- **Acceptance**:
  - GuardrailEngine accepts optional Tracer
  - Guardrail summary attached to Trace.guardrails field
  - Trace model updated to include guardrails field
  - Results serializable to JSON
  - Works without Tracer (standalone mode)
- **Status**: [x] Complete

### T-2.7: Create GuardedAnthropicClient

- **Description**: Create client wrapper that applies guardrails at input and output stages
- **Dependencies**: T-2.1, T-2.2, T-2.5
- **Files**:
  - Create: `backend/src/guardrails/client.py`
- **Acceptance**:
  - Wraps TracedAnthropicClient
  - Input guardrails run before API call
  - Behavioral guardrails can be called via hook
  - Output guardrails run after API response
  - GuardrailBlockError propagates correctly
  - Context managed across agentic loop calls
- **Status**: [x] Complete

### T-2.8: Update Module Exports

- **Description**: Update `__init__.py` to export all public APIs
- **Dependencies**: T-2.1 through T-2.7
- **Files**:
  - Modify: `backend/src/guardrails/__init__.py`
- **Acceptance**:
  - `from src.guardrails import GuardrailEngine` works
  - `from src.guardrails import GuardedAnthropicClient` works
  - `from src.guardrails import GuardrailBlockError` works
  - `from src.guardrails import GuardrailContext` works
  - `from src.guardrails import load_guardrails` works
- **Status**: [x] Complete

### T-2.9: Write Behavioral Stage Tests

- **Description**: Create tests for behavioral stage guardrails
- **Dependencies**: T-2.1, T-2.5
- **Files**:
  - Create: `backend/tests/test_guardrails_behavioral.py`
- **Acceptance**:
  - Test max_tool_calls passes when under limit
  - Test max_tool_calls blocks when over limit
  - Test max_iterations passes when under limit
  - Test max_iterations blocks when over limit
  - Test allowed_tools passes for allowed tool
  - Test allowed_tools blocks for unknown tool
  - Test context updates correctly across calls
  - All tests pass with `pytest`
- **Status**: [x] Complete

### T-2.10: Write Output Stage Tests

- **Description**: Create tests for output stage guardrails
- **Dependencies**: T-2.2, T-2.3, T-2.4
- **Files**:
  - Create: `backend/tests/test_guardrails_output.py`
- **Acceptance**:
  - Test valid_enum passes for valid value
  - Test valid_enum blocks for invalid value
  - Test truncate shortens long output
  - Test truncate appends suffix
  - Test fallback substitutes default value
  - Test output not mutated (returns copy)
  - Test nested field access works
  - All tests pass with `pytest`
- **Status**: [x] Complete

---

## File Checklist

All files that will be created or modified:

**New Files (14)**:
- [x] `backend/src/guardrails/__init__.py`
- [x] `backend/src/guardrails/models.py`
- [x] `backend/src/guardrails/config.py`
- [x] `backend/src/guardrails/rules.py`
- [x] `backend/src/guardrails/engine.py`
- [x] `backend/src/guardrails/input.py`
- [x] `backend/src/guardrails/behavioral.py`
- [x] `backend/src/guardrails/output.py`
- [x] `backend/src/guardrails/client.py`
- [x] `backend/guardrails.yaml`
- [x] `backend/tests/test_guardrails_config.py`
- [x] `backend/tests/test_guardrails_input.py`
- [x] `backend/tests/test_guardrails_rules.py`
- [x] `backend/tests/test_guardrails_behavioral.py`
- [x] `backend/tests/test_guardrails_output.py`

**Modified Files (1)**:
- [x] `backend/src/evaluation/models.py` (add guardrails field to Trace)

---

## Definition of Done (Phase 1)

- [x] Guardrails module created with public API
- [x] Configuration loads from YAML with validation
- [x] Built-in rules implemented (max_length, min_length, required, valid_json)
- [x] Rule parser safely evaluates rule strings
- [x] Input guardrails block invalid requests
- [x] Example guardrails.yaml demonstrates all patterns
- [x] All Phase 1 tests pass
- [x] < 5ms overhead for input checks

## Definition of Done (Phase 2)

- [x] Behavioral guardrails enforce tool/iteration limits
- [x] Output guardrails validate and modify responses
- [x] Truncate response shortens long outputs
- [x] Fallback response substitutes default values
- [x] Context tracks execution state across calls
- [x] Guardrail results attached to traces
- [x] GuardedAnthropicClient wraps full pipeline
- [x] All Phase 2 tests pass
- [x] < 15ms total guardrail overhead

---

## Progress Log

| Date | Tasks Completed | Notes |
|------|-----------------|-------|
| 2026-01-22 | T-1.1 through T-2.10 | All Phase 1-2 tasks completed. 125 total tests passing (84 guardrails + 41 evaluation). |
