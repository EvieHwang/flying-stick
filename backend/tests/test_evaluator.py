"""
Tests for the evaluator module.
"""

import pytest

from src.evaluation.evaluator import Evaluator
from src.evaluation.models import (
    Trace,
    TraceRequest,
    TraceResponse,
    TraceMetrics,
    EvaluationCriterion,
)


class TestEvaluator:
    """Tests for the Evaluator class."""

    def test_evaluator_with_no_criteria(self):
        """Evaluator should work with no criteria defined."""
        evaluator = Evaluator(criteria={})
        trace = Trace(agent="test")

        result = evaluator.evaluate(trace)

        assert result.evaluations == {}

    def test_evaluator_layer1_pass(self):
        """Layer 1 criterion should pass when condition met."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="no_errors",
                    pillar="effectiveness",
                    layer=1,
                    signal="error",
                    threshold="must be null",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(agent="test", error=None)
        result = evaluator.evaluate(trace)

        assert "no_errors" in result.evaluations
        assert result.evaluations["no_errors"].result == "pass"

    def test_evaluator_layer1_fail(self):
        """Layer 1 criterion should fail when condition not met."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="no_errors",
                    pillar="effectiveness",
                    layer=1,
                    signal="error",
                    threshold="must be null",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(agent="test", error="Something went wrong")
        result = evaluator.evaluate(trace)

        assert result.evaluations["no_errors"].result == "fail"

    def test_evaluator_layer2_pass(self):
        """Layer 2 criterion should pass when under threshold."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="latency",
                    pillar="efficiency",
                    layer=2,
                    signal="duration_ms",
                    threshold="< 5000",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(
            agent="test",
            metrics=TraceMetrics(
                duration_ms=3000,
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
            ),
        )
        result = evaluator.evaluate(trace)

        assert result.evaluations["latency"].result == "pass"
        assert result.evaluations["latency"].value == 3000

    def test_evaluator_layer2_fail(self):
        """Layer 2 criterion should fail when over threshold."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="latency",
                    pillar="efficiency",
                    layer=2,
                    signal="duration_ms",
                    threshold="< 3000",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(
            agent="test",
            metrics=TraceMetrics(
                duration_ms=5000,
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
            ),
        )
        result = evaluator.evaluate(trace)

        assert result.evaluations["latency"].result == "fail"

    def test_evaluator_layer2_warning(self):
        """Layer 2 criterion should warn when between thresholds."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="latency",
                    pillar="efficiency",
                    layer=2,
                    signal="duration_ms",
                    threshold="< 5000",
                    warning="< 3000",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(
            agent="test",
            metrics=TraceMetrics(
                duration_ms=4000,  # Above warning, below threshold
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
            ),
        )
        result = evaluator.evaluate(trace)

        assert result.evaluations["latency"].result == "warning"

    def test_evaluator_layer3_skipped(self):
        """Layer 3 criterion should be skipped (not implemented)."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="reasoning",
                    pillar="trustworthiness",
                    layer=3,
                    signal="response.output",
                    threshold="mean >= 4",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(agent="test")
        result = evaluator.evaluate(trace)

        assert result.evaluations["reasoning"].result == "skipped"
        assert "not implemented" in result.evaluations["reasoning"].message.lower()

    def test_evaluator_disabled_criterion_skipped(self):
        """Disabled criteria should not be evaluated."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="disabled_check",
                    pillar="effectiveness",
                    layer=1,
                    signal="error",
                    threshold="must be null",
                    enabled=False,
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(agent="test")
        result = evaluator.evaluate(trace)

        assert "disabled_check" not in result.evaluations

    def test_evaluator_default_agent_fallback(self):
        """Should use default agent criteria if specific agent not found."""
        criteria = {
            "default": [
                EvaluationCriterion(
                    name="global_check",
                    pillar="effectiveness",
                    layer=1,
                    signal="error",
                    threshold="must be null",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(agent="unknown_agent", error=None)
        result = evaluator.evaluate(trace)

        assert "global_check" in result.evaluations
        assert result.evaluations["global_check"].result == "pass"

    def test_evaluator_multiple_criteria(self):
        """Multiple criteria should all be evaluated."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="check1",
                    pillar="effectiveness",
                    layer=1,
                    signal="error",
                    threshold="must be null",
                ),
                EvaluationCriterion(
                    name="check2",
                    pillar="efficiency",
                    layer=2,
                    signal="duration_ms",
                    threshold="< 5000",
                ),
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(
            agent="test",
            error=None,
            metrics=TraceMetrics(
                duration_ms=3000,
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
            ),
        )
        result = evaluator.evaluate(trace)

        assert len(result.evaluations) == 2
        assert result.evaluations["check1"].result == "pass"
        assert result.evaluations["check2"].result == "pass"


class TestLayer1Thresholds:
    """Tests for Layer 1 threshold parsing."""

    def test_must_not_be_empty(self):
        """'must not be empty' should check for truthy value."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="has_output",
                    pillar="effectiveness",
                    layer=1,
                    signal="response.output",
                    threshold="must not be empty",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        # Empty string should fail
        trace1 = Trace(agent="test", response=TraceResponse(output=""))
        result1 = evaluator.evaluate(trace1)
        assert result1.evaluations["has_output"].result == "fail"

        # Non-empty should pass
        trace2 = Trace(agent="test", response=TraceResponse(output="hello"))
        result2 = evaluator.evaluate(trace2)
        assert result2.evaluations["has_output"].result == "pass"


class TestLayer2Thresholds:
    """Tests for Layer 2 threshold parsing."""

    def test_greater_than(self):
        """'> X' threshold should work."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="min_tokens",
                    pillar="efficiency",
                    layer=2,
                    signal="total_tokens",
                    threshold="> 100",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(
            agent="test",
            metrics=TraceMetrics(
                duration_ms=1000,
                input_tokens=80,
                output_tokens=50,
                total_tokens=130,
            ),
        )
        result = evaluator.evaluate(trace)
        assert result.evaluations["min_tokens"].result == "pass"

    def test_less_than_or_equal(self):
        """'<= X' threshold should work."""
        criteria = {
            "test": [
                EvaluationCriterion(
                    name="max_tokens",
                    pillar="efficiency",
                    layer=2,
                    signal="total_tokens",
                    threshold="<= 100",
                )
            ]
        }
        evaluator = Evaluator(criteria=criteria)

        trace = Trace(
            agent="test",
            metrics=TraceMetrics(
                duration_ms=1000,
                input_tokens=50,
                output_tokens=50,
                total_tokens=100,
            ),
        )
        result = evaluator.evaluate(trace)
        assert result.evaluations["max_tokens"].result == "pass"
