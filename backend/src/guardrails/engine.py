"""
Guardrails execution engine.

The main orchestration class that runs guardrails at each stage.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, TYPE_CHECKING

from .config import load_guardrails, get_settings
from .models import (
    GuardrailConfig,
    GuardrailResult,
    GuardrailContext,
    GuardrailBlockError,
    GuardrailSummary,
)
from .rules import evaluate_rule, RuleParseError


if TYPE_CHECKING:
    from ..evaluation import Tracer


logger = logging.getLogger(__name__)


class GuardrailEngine:
    """
    Main guardrails execution engine.

    Orchestrates guardrail checks at input, behavioral, and output stages.
    """

    def __init__(
        self,
        config_path: str | None = None,
        config_dict: dict | None = None,
        fail_open: bool | None = None,
        tracer: "Tracer | None" = None,
    ):
        """
        Initialize the guardrails engine.

        Args:
            config_path: Path to guardrails.yaml
            config_dict: Configuration dictionary (takes precedence)
            fail_open: If True, continue on guardrail engine errors.
                      If None, uses value from config settings.
            tracer: Optional Tracer for attaching results to traces
        """
        self.config = load_guardrails(config_path, config_dict)
        self.settings = get_settings(config_path)
        self.fail_open = fail_open if fail_open is not None else self.settings.get("fail_open", False)
        self.tracer = tracer
        self._summary = GuardrailSummary()

    def _get_guardrails(
        self,
        agent: str,
        stage: str,
    ) -> list[GuardrailConfig]:
        """Get guardrails for an agent and stage."""
        # Try agent-specific first
        if agent in self.config:
            return self.config[agent].get(stage, [])

        # Fall back to "default" agent
        if "default" in self.config:
            return self.config["default"].get(stage, [])

        return []

    def _evaluate_guardrail(
        self,
        guardrail: GuardrailConfig,
        context: dict[str, Any],
    ) -> GuardrailResult:
        """
        Evaluate a single guardrail.

        Returns a GuardrailResult indicating whether the guardrail triggered.
        """
        try:
            passed = evaluate_rule(guardrail.rule, context)
            triggered = not passed

            result = GuardrailResult(
                name=guardrail.name,
                stage=guardrail.stage,
                threat=guardrail.threat,
                triggered=triggered,
                response=guardrail.response if triggered else None,
                message=guardrail.error_message if triggered else None,
            )

            if self.settings.get("log_all_activations", True):
                if triggered:
                    logger.warning(
                        f"Guardrail triggered: {guardrail.name} "
                        f"(stage={guardrail.stage}, threat={guardrail.threat}, "
                        f"response={guardrail.response})"
                    )
                else:
                    logger.debug(f"Guardrail passed: {guardrail.name}")

            return result

        except RuleParseError as e:
            logger.error(f"Rule parse error in {guardrail.name}: {e}")
            if self.fail_open:
                return GuardrailResult(
                    name=guardrail.name,
                    stage=guardrail.stage,
                    threat=guardrail.threat,
                    triggered=False,
                    message=f"Rule parse error: {e}",
                )
            raise
        except Exception as e:
            logger.error(f"Error evaluating guardrail {guardrail.name}: {e}")
            if self.fail_open:
                return GuardrailResult(
                    name=guardrail.name,
                    stage=guardrail.stage,
                    threat=guardrail.threat,
                    triggered=False,
                    message=f"Evaluation error: {e}",
                )
            raise

    def check_input(
        self,
        agent: str,
        request: dict[str, Any],
    ) -> list[GuardrailResult]:
        """
        Run input stage guardrails.

        Args:
            agent: Agent name
            request: Request data (typically the parsed request body)

        Returns:
            List of GuardrailResult objects

        Raises:
            GuardrailBlockError: If any guardrail blocks the request
        """
        guardrails = self._get_guardrails(agent, "input")
        results = []

        for g in guardrails:
            if not g.enabled:
                continue

            context = {"request": request}
            result = self._evaluate_guardrail(g, context)
            results.append(result)
            self._summary.add_result(result)

            if result.triggered and result.response == "block":
                raise GuardrailBlockError(
                    guardrail_name=g.name,
                    stage="input",
                    message=g.error_message or f"Blocked by guardrail: {g.name}",
                    details=result.details,
                )

        return results

    def check_behavioral(
        self,
        ctx: GuardrailContext,
        tool_name: str | None = None,
    ) -> list[GuardrailResult]:
        """
        Run behavioral stage guardrails.

        Should be called before each tool call and/or iteration in an agent loop.

        Args:
            ctx: Guardrail context with execution state
            tool_name: Name of the tool about to be called (optional)

        Returns:
            List of GuardrailResult objects

        Raises:
            GuardrailBlockError: If any guardrail blocks execution
        """
        # Record the tool call if provided
        if tool_name:
            ctx.record_tool_call(tool_name)

        guardrails = self._get_guardrails(ctx.agent, "behavioral")
        results = []

        for g in guardrails:
            if not g.enabled:
                continue

            # For behavioral guardrails, pass the context directly
            rule_context = {
                "context": ctx,
                "request": ctx.request,
            }
            result = self._evaluate_guardrail(g, rule_context)

            # Add execution details
            result.details = {
                "tool_call_count": ctx.tool_call_count,
                "iteration_count": ctx.iteration_count,
                "elapsed_ms": ctx.elapsed_ms(),
            }

            results.append(result)
            self._summary.add_result(result)

            if result.triggered and result.response == "block":
                raise GuardrailBlockError(
                    guardrail_name=g.name,
                    stage="behavioral",
                    message=g.error_message or f"Blocked by guardrail: {g.name}",
                    details=result.details,
                )

        return results

    def check_output(
        self,
        agent: str,
        request: dict[str, Any],
        output: Any,
    ) -> tuple[Any, list[GuardrailResult]]:
        """
        Run output stage guardrails.

        May modify the output (truncate, fallback).

        Args:
            agent: Agent name
            request: Original request
            output: AI response output (will not be mutated)

        Returns:
            Tuple of (possibly modified output, list of results)

        Raises:
            GuardrailBlockError: If any guardrail blocks the output
        """
        guardrails = self._get_guardrails(agent, "output")
        results = []

        # Deep copy output to avoid mutating the original
        modified_output = copy.deepcopy(output)

        for g in guardrails:
            if not g.enabled:
                continue

            context = {
                "request": request,
                "output": modified_output,
            }
            result = self._evaluate_guardrail(g, context)
            results.append(result)
            self._summary.add_result(result)

            if result.triggered:
                if result.response == "block":
                    raise GuardrailBlockError(
                        guardrail_name=g.name,
                        stage="output",
                        message=g.error_message or f"Blocked by guardrail: {g.name}",
                        details=result.details,
                    )

                elif result.response == "truncate":
                    modified_output = self._apply_truncate(
                        modified_output, g, result
                    )

                elif result.response == "fallback":
                    modified_output = self._apply_fallback(
                        modified_output, g, result
                    )

                # "flag" response just logs (already done)

        return modified_output, results

    def _apply_truncate(
        self,
        output: Any,
        guardrail: GuardrailConfig,
        result: GuardrailResult,
    ) -> Any:
        """Apply truncation to output."""
        if guardrail.truncate_to is None:
            return output

        # Parse the rule to find the field to truncate
        # Rule format: max_length(output.field, limit)
        field_path = self._extract_field_from_rule(guardrail.rule, "output.")

        if field_path and isinstance(output, dict):
            original_value = self._get_nested(output, field_path)
            if isinstance(original_value, str):
                result.details["original_length"] = len(original_value)
                truncated = original_value[:guardrail.truncate_to] + guardrail.suffix
                self._set_nested(output, field_path, truncated)
                result.details["truncated_to"] = guardrail.truncate_to
        elif isinstance(output, str):
            result.details["original_length"] = len(output)
            output = output[:guardrail.truncate_to] + guardrail.suffix
            result.details["truncated_to"] = guardrail.truncate_to

        return output

    def _apply_fallback(
        self,
        output: Any,
        guardrail: GuardrailConfig,
        result: GuardrailResult,
    ) -> Any:
        """Apply fallback value to output."""
        # Parse the rule to find the field to replace
        field_path = self._extract_field_from_rule(guardrail.rule, "output.")

        if field_path and isinstance(output, dict):
            original_value = self._get_nested(output, field_path)
            result.details["original_value"] = original_value
            result.details["fallback_value"] = guardrail.fallback_value
            self._set_nested(output, field_path, guardrail.fallback_value)
        else:
            result.details["original_value"] = output
            result.details["fallback_value"] = guardrail.fallback_value
            output = guardrail.fallback_value

        return output

    def _extract_field_from_rule(self, rule: str, prefix: str) -> str | None:
        """Extract field path from a rule string."""
        import re
        # Look for patterns like output.field or output.nested.field
        match = re.search(rf"{re.escape(prefix)}([\w.]+)", rule)
        if match:
            return match.group(1)
        return None

    def _get_nested(self, obj: dict, path: str) -> Any:
        """Get nested value using dot notation."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _set_nested(self, obj: dict, path: str, value: Any) -> None:
        """Set nested value using dot notation."""
        parts = path.split(".")
        current = obj
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all guardrail checks."""
        return self._summary.to_dict()

    def reset(self) -> None:
        """Reset results for a new request."""
        self._summary = GuardrailSummary()

    def create_context(
        self,
        agent: str,
        request: dict[str, Any],
    ) -> GuardrailContext:
        """Create a new guardrail context for tracking execution state."""
        return GuardrailContext(agent=agent, request=request)
