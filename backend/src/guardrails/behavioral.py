"""
Behavioral stage guardrails.

Provides utilities for tracking execution state during agent loops.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from .models import GuardrailContext, GuardrailBlockError


T = TypeVar("T")


def with_behavioral_check(
    engine: "GuardrailEngine",  # noqa: F821
    context: GuardrailContext,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory for adding behavioral checks to functions.

    Usage:
        @with_behavioral_check(engine, context)
        def call_tool(tool_name: str, args: dict):
            ...

    Args:
        engine: GuardrailEngine instance
        context: GuardrailContext for tracking state

    Returns:
        Decorator function
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            # Increment iteration before check
            context.increment_iteration()

            # Run behavioral guardrails
            engine.check_behavioral(context)

            # Execute the function
            return fn(*args, **kwargs)
        return wrapper
    return decorator


class BehavioralGuard:
    """
    Context manager for behavioral guardrails in agent loops.

    Usage:
        guard = BehavioralGuard(engine, agent, request)

        for iteration in agent_loop():
            with guard.iteration():
                # Do iteration work
                pass

            with guard.tool_call("tool_name"):
                # Call tool
                pass
    """

    def __init__(
        self,
        engine: "GuardrailEngine",  # noqa: F821
        agent: str,
        request: dict[str, Any],
    ):
        self.engine = engine
        self.context = engine.create_context(agent, request)

    def iteration(self) -> "IterationGuard":
        """Start a new iteration check."""
        return IterationGuard(self.engine, self.context)

    def tool_call(self, tool_name: str) -> "ToolCallGuard":
        """Start a tool call check."""
        return ToolCallGuard(self.engine, self.context, tool_name)

    def get_context(self) -> GuardrailContext:
        """Get the current context."""
        return self.context


class IterationGuard:
    """Context manager for iteration checks."""

    def __init__(self, engine: "GuardrailEngine", context: GuardrailContext):  # noqa: F821
        self.engine = engine
        self.context = context

    def __enter__(self):
        self.context.increment_iteration()
        self.engine.check_behavioral(self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class ToolCallGuard:
    """Context manager for tool call checks."""

    def __init__(
        self,
        engine: "GuardrailEngine",  # noqa: F821
        context: GuardrailContext,
        tool_name: str,
    ):
        self.engine = engine
        self.context = context
        self.tool_name = tool_name

    def __enter__(self):
        self.engine.check_behavioral(self.context, self.tool_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
