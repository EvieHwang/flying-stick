"""
Tests for behavioral stage guardrails.
"""

import pytest
import time

from src.guardrails import (
    GuardrailEngine,
    GuardrailBlockError,
    GuardrailContext,
    BehavioralGuard,
)


class TestBehavioralGuardrails:
    """Tests for behavioral stage guardrail checking."""

    def test_behavioral_guardrails_pass(self):
        """Behavioral guardrails should pass when under limits."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "max_tools",
                            "threat": "cost",
                            "rule": "max_tool_calls(context, 5)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        ctx = engine.create_context("test", {})

        # Make a few tool calls
        ctx.record_tool_call("tool_a")
        ctx.record_tool_call("tool_b")

        results = engine.check_behavioral(ctx)
        assert len(results) == 1
        assert results[0].triggered is False

    def test_behavioral_guardrails_block(self):
        """Behavioral guardrails should block when over limit."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "max_tools",
                            "threat": "cost",
                            "rule": "max_tool_calls(context, 3)",
                            "response": "block",
                            "error_message": "Too many tool calls",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        ctx = engine.create_context("test", {})

        # Exceed tool call limit
        for i in range(5):
            ctx.record_tool_call(f"tool_{i}")

        with pytest.raises(GuardrailBlockError) as exc_info:
            engine.check_behavioral(ctx)

        assert exc_info.value.guardrail_name == "max_tools"
        assert exc_info.value.stage == "behavioral"
        assert "Too many tool calls" in exc_info.value.message

    def test_max_iterations_check(self):
        """Should enforce iteration limits."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "max_iter",
                            "threat": "cost",
                            "rule": "max_iterations(context, 3)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        ctx = engine.create_context("test", {})

        # First 3 iterations should pass
        for i in range(3):
            ctx.increment_iteration()
            results = engine.check_behavioral(ctx)
            assert results[0].triggered is False

        # 4th iteration should block
        ctx.increment_iteration()
        with pytest.raises(GuardrailBlockError):
            engine.check_behavioral(ctx)

    def test_allowed_tools_check(self):
        """Should enforce tool whitelist."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "allowed_tools",
                            "threat": "scope",
                            "rule": "allowed_tools(context, ['safe_tool', 'another_tool'])",
                            "response": "block",
                            "error_message": "Unauthorized tool",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        ctx = engine.create_context("test", {})

        # Allowed tool should pass
        ctx.record_tool_call("safe_tool")
        results = engine.check_behavioral(ctx)
        assert results[0].triggered is False

        # Unknown tool should block
        ctx.record_tool_call("dangerous_tool")
        with pytest.raises(GuardrailBlockError) as exc_info:
            engine.check_behavioral(ctx)

        assert "Unauthorized tool" in exc_info.value.message

    def test_tool_call_tracking(self):
        """Should track tool calls via check_behavioral with tool_name."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "max_tools",
                            "threat": "cost",
                            "rule": "max_tool_calls(context, 2)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        ctx = engine.create_context("test", {})

        # Record tool via check_behavioral
        engine.check_behavioral(ctx, tool_name="tool_1")
        engine.check_behavioral(ctx, tool_name="tool_2")

        assert ctx.tool_call_count == 2
        assert ctx.tool_calls == ["tool_1", "tool_2"]

        # Third tool should block
        with pytest.raises(GuardrailBlockError):
            engine.check_behavioral(ctx, tool_name="tool_3")

    def test_context_elapsed_time(self):
        """Context should track elapsed time."""
        ctx = GuardrailContext(agent="test", request={})

        # Wait a bit
        time.sleep(0.1)

        elapsed = ctx.elapsed_ms()
        assert elapsed >= 100  # At least 100ms

    def test_context_to_dict(self):
        """Context should serialize to dict."""
        ctx = GuardrailContext(agent="test", request={"key": "value"})
        ctx.tool_call_count = 2
        ctx.iteration_count = 3
        ctx.tool_calls = ["tool_a", "tool_b"]

        data = ctx.to_dict()

        assert data["agent"] == "test"
        assert data["tool_call_count"] == 2
        assert data["iteration_count"] == 3
        assert data["tool_calls"] == ["tool_a", "tool_b"]
        assert "elapsed_ms" in data

    def test_behavioral_result_includes_details(self):
        """Behavioral results should include execution details."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "check",
                            "threat": "cost",
                            "rule": "max_tool_calls(context, 10)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        ctx = engine.create_context("test", {})
        ctx.tool_call_count = 5
        ctx.iteration_count = 2

        results = engine.check_behavioral(ctx)

        assert results[0].details["tool_call_count"] == 5
        assert results[0].details["iteration_count"] == 2
        assert "elapsed_ms" in results[0].details


class TestBehavioralGuard:
    """Tests for BehavioralGuard context manager."""

    def test_iteration_guard(self):
        """IterationGuard should increment iteration and check."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "max_iter",
                            "threat": "cost",
                            "rule": "max_iterations(context, 3)",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        guard = BehavioralGuard(engine, "test", {})

        # First 3 iterations should pass
        for i in range(3):
            with guard.iteration():
                pass

        # 4th should block
        with pytest.raises(GuardrailBlockError):
            with guard.iteration():
                pass

    def test_tool_call_guard(self):
        """ToolCallGuard should record tool and check."""
        config = {
            "agents": {
                "test": {
                    "behavioral": [
                        {
                            "name": "allowed",
                            "threat": "scope",
                            "rule": "allowed_tools(context, ['safe'])",
                            "response": "block",
                        }
                    ]
                }
            }
        }
        engine = GuardrailEngine(config_dict=config)
        guard = BehavioralGuard(engine, "test", {})

        # Safe tool should pass
        with guard.tool_call("safe"):
            pass

        # Unsafe tool should block
        with pytest.raises(GuardrailBlockError):
            with guard.tool_call("unsafe"):
                pass

    def test_guard_get_context(self):
        """Should be able to get context from guard."""
        config = {"agents": {"test": {"behavioral": []}}}
        engine = GuardrailEngine(config_dict=config)
        guard = BehavioralGuard(engine, "test", {"key": "value"})

        ctx = guard.get_context()
        assert ctx.agent == "test"
        assert ctx.request == {"key": "value"}
