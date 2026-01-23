"""
Evaluation engine for running criteria against traces.

The Evaluator loads criteria from configuration and applies them to traces,
producing EvaluationResults that are attached to the trace before storage.
"""

import logging
import operator
import re
from typing import Any, Callable

from .models import Trace, EvaluationCriterion, EvaluationResult
from .criteria import load_criteria
from .signals import extract_signal


logger = logging.getLogger(__name__)


# Comparison operators for threshold evaluation
OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
}


class Evaluator:
    """
    Runs evaluations against traces based on configured criteria.

    Usage:
        evaluator = Evaluator()  # Loads from evaluation.yaml
        trace = evaluator.evaluate(trace)  # Attaches evaluations
    """

    def __init__(
        self,
        config_path: str | None = None,
        criteria: dict[str, list[EvaluationCriterion]] | None = None
    ):
        """
        Initialize the evaluator.

        Args:
            config_path: Path to evaluation.yaml (optional)
            criteria: Pre-loaded criteria dict (optional, for testing)
        """
        if criteria is not None:
            self.criteria = criteria
        else:
            self.criteria = load_criteria(config_path)

    def evaluate(self, trace: Trace) -> Trace:
        """
        Run all applicable evaluations and attach results to trace.

        Args:
            trace: The trace to evaluate

        Returns:
            The same trace with evaluations dict populated
        """
        # Get criteria for this agent, fall back to default
        agent_criteria = self.criteria.get(trace.agent, [])
        if not agent_criteria:
            agent_criteria = self.criteria.get("default", [])

        for criterion in agent_criteria:
            if not criterion.enabled:
                continue

            # Skip Layer 3 (not implemented in Phase 1-2)
            if criterion.layer == 3:
                trace.evaluations[criterion.name] = EvaluationResult(
                    criterion=criterion.name,
                    layer=3,
                    result="skipped",
                    message="Layer 3 evaluation not implemented"
                )
                continue

            try:
                result = self._evaluate_criterion(trace, criterion)
                trace.evaluations[criterion.name] = result
            except Exception as e:
                logger.warning(
                    f"Error evaluating criterion '{criterion.name}': {e}",
                    exc_info=True
                )
                trace.evaluations[criterion.name] = EvaluationResult(
                    criterion=criterion.name,
                    layer=criterion.layer,
                    result="skipped",
                    message=f"Evaluation error: {e}"
                )

        return trace

    def _evaluate_criterion(
        self, trace: Trace, criterion: EvaluationCriterion
    ) -> EvaluationResult:
        """Evaluate a single criterion against a trace."""
        # Extract the signal value
        value = extract_signal(trace, criterion.signal)

        if criterion.layer == 1:
            return self._evaluate_layer1(criterion, value)
        else:  # Layer 2
            return self._evaluate_layer2(criterion, value)

    def _evaluate_layer1(
        self, criterion: EvaluationCriterion, value: Any
    ) -> EvaluationResult:
        """
        Evaluate a Layer 1 (binary gate) criterion.

        Layer 1 thresholds are pass/fail conditions expressed as:
        - "must be valid JSON"
        - "must be null"
        - "must not be empty"
        - "must have field X"
        """
        threshold = criterion.threshold.lower().strip()
        passed = False
        message = None

        # Handle common Layer 1 patterns
        if "must be valid json" in threshold:
            if isinstance(value, dict):
                # Check response.format signal
                passed = value.get("is_json", False)
                if not passed:
                    message = value.get("error", "Not valid JSON")
            else:
                passed = False
                message = "Signal did not return format validation"

        elif "must be null" in threshold or "must be none" in threshold:
            passed = value is None
            if not passed:
                message = f"Expected null, got: {type(value).__name__}"

        elif "must not be null" in threshold or "must not be none" in threshold:
            passed = value is not None
            if not passed:
                message = "Value is null"

        elif "must not be empty" in threshold:
            passed = bool(value)
            if not passed:
                message = "Value is empty"

        elif "must have field" in threshold:
            # Extract field name: "must have field 'category'"
            match = re.search(r"must have field ['\"]?(\w+)['\"]?", threshold)
            if match and isinstance(value, dict):
                field_name = match.group(1)
                if isinstance(value.get("has_fields"), list):
                    passed = field_name in value["has_fields"]
                else:
                    passed = field_name in value
                if not passed:
                    message = f"Missing field: {field_name}"
            else:
                passed = False
                message = "Cannot check field on non-dict value"

        elif "must be true" in threshold:
            passed = value is True
            if not passed:
                message = f"Expected true, got: {value}"

        elif "must be false" in threshold:
            passed = value is False
            if not passed:
                message = f"Expected false, got: {value}"

        else:
            # Try to evaluate as a simple boolean expression
            passed = bool(value)
            message = f"Evaluated as boolean: {passed}"

        return EvaluationResult(
            criterion=criterion.name,
            layer=1,
            result="pass" if passed else "fail",
            value=value,
            message=message
        )

    def _evaluate_layer2(
        self, criterion: EvaluationCriterion, value: Any
    ) -> EvaluationResult:
        """
        Evaluate a Layer 2 (quantitative) criterion.

        Layer 2 thresholds are numeric comparisons:
        - "< 3000"
        - ">= 0.85"
        - "p95 < 5000" (treated as single value comparison for now)
        """
        threshold = criterion.threshold.strip()
        warning_threshold = criterion.warning.strip() if criterion.warning else None

        # Handle non-numeric values
        if value is None:
            return EvaluationResult(
                criterion=criterion.name,
                layer=2,
                result="skipped",
                value=None,
                message="Signal value is None"
            )

        # Try to convert value to number
        try:
            if isinstance(value, (int, float)):
                numeric_value = float(value)
            else:
                numeric_value = float(value)
        except (TypeError, ValueError):
            return EvaluationResult(
                criterion=criterion.name,
                layer=2,
                result="skipped",
                value=value,
                message=f"Cannot convert to number: {type(value).__name__}"
            )

        # Parse and evaluate threshold
        passed, threshold_msg = self._check_threshold(numeric_value, threshold)

        # Check warning threshold if main threshold passes
        warning = False
        if passed and warning_threshold:
            warning_passed, _ = self._check_threshold(numeric_value, warning_threshold)
            warning = not warning_passed

        if not passed:
            result = "fail"
        elif warning:
            result = "warning"
        else:
            result = "pass"

        return EvaluationResult(
            criterion=criterion.name,
            layer=2,
            result=result,
            value=numeric_value,
            message=threshold_msg if not passed else None
        )

    def _check_threshold(self, value: float, threshold: str) -> tuple[bool, str]:
        """
        Check if a value meets a threshold.

        Returns (passed, message) tuple.
        """
        # Remove p95/p99/mean prefix if present (treat as single value for now)
        threshold = re.sub(r"^(p\d+|mean|avg|max|min)\s+", "", threshold)

        # Parse comparison: "< 3000", ">= 0.85", etc.
        match = re.match(r"([<>=!]+)\s*([\d.]+)", threshold)
        if not match:
            return True, f"Could not parse threshold: {threshold}"

        op_str = match.group(1)
        target = float(match.group(2))

        if op_str not in OPERATORS:
            return True, f"Unknown operator: {op_str}"

        op_func = OPERATORS[op_str]
        passed = op_func(value, target)

        message = f"{value} {op_str} {target} = {passed}"
        return passed, message
