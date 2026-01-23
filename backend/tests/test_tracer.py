"""
Tests for the tracer module.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.evaluation.tracer import Tracer
from src.evaluation.models import Trace, TraceMetrics


class TestTracer:
    """Tests for the Tracer class."""

    def test_tracer_disabled_when_no_bucket(self):
        """Tracer should be disabled if no bucket is configured."""
        with patch.dict("os.environ", {}, clear=True):
            tracer = Tracer(bucket=None)
            assert tracer.enabled is False

    def test_tracer_enabled_with_bucket(self):
        """Tracer should be enabled when bucket is provided."""
        tracer = Tracer(bucket="test-bucket")
        assert tracer.enabled is True
        assert tracer.bucket == "test-bucket"

    def test_trace_call_disabled_returns_result(self):
        """When disabled, trace_call should just return the function result."""
        tracer = Tracer(bucket=None, enabled=False)

        result = tracer.trace_call(
            agent="test",
            call_fn=lambda: "hello",
            request_data={},
        )

        assert result == "hello"

    def test_trace_call_captures_timing(self):
        """trace_call should capture execution timing."""
        tracer = Tracer(bucket="test-bucket", enabled=True, async_write=False)

        # Mock S3 client
        tracer._s3_client = MagicMock()

        # Track what gets written
        written_traces = []

        def capture_put(Bucket, Key, Body, ContentType):
            written_traces.append(json.loads(Body))

        tracer._s3_client.put_object = capture_put

        # Make a call that takes some time
        import time

        def slow_fn():
            time.sleep(0.1)
            return "done"

        result = tracer.trace_call(
            agent="test-agent",
            call_fn=slow_fn,
            request_data={"model": "test-model", "messages": []},
        )

        assert result == "done"
        assert len(written_traces) == 1

        trace = written_traces[0]
        assert trace["agent"] == "test-agent"
        assert trace["metrics"]["duration_ms"] >= 100
        assert trace["error"] is None

    def test_trace_call_captures_errors(self):
        """trace_call should capture errors and re-raise them."""
        tracer = Tracer(bucket="test-bucket", enabled=True, async_write=False)
        tracer._s3_client = MagicMock()

        written_traces = []

        def capture_put(Bucket, Key, Body, ContentType):
            written_traces.append(json.loads(Body))

        tracer._s3_client.put_object = capture_put

        def failing_fn():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            tracer.trace_call(
                agent="test",
                call_fn=failing_fn,
                request_data={},
            )

        # Error should be captured in trace
        assert len(written_traces) == 1
        assert written_traces[0]["error"] == "Test error"

    def test_trace_s3_path_structure(self):
        """Traces should be written to correct S3 path."""
        tracer = Tracer(bucket="my-bucket", enabled=True, async_write=False)
        tracer._s3_client = MagicMock()

        written_keys = []

        def capture_put(Bucket, Key, Body, ContentType):
            written_keys.append(Key)

        tracer._s3_client.put_object = capture_put

        tracer.trace_call(
            agent="classifier",
            call_fn=lambda: None,
            request_data={},
        )

        assert len(written_keys) == 1
        key = written_keys[0]

        # Path should be: traces/{agent}/{date}/{trace_id}.json
        assert key.startswith("traces/classifier/")
        assert key.endswith(".json")
        parts = key.split("/")
        assert len(parts) == 4
        assert parts[0] == "traces"
        assert parts[1] == "classifier"
        # Date format: YYYY-MM-DD
        assert len(parts[2]) == 10
        assert parts[2][4] == "-"

    def test_trace_metadata_included(self):
        """Custom metadata should be included in trace."""
        tracer = Tracer(bucket="test-bucket", enabled=True, async_write=False)
        tracer._s3_client = MagicMock()

        written_traces = []

        def capture_put(Bucket, Key, Body, ContentType):
            written_traces.append(json.loads(Body))

        tracer._s3_client.put_object = capture_put

        tracer.trace_call(
            agent="test",
            call_fn=lambda: None,
            request_data={},
            metadata={"user_id": "123", "request_id": "abc"},
        )

        trace = written_traces[0]
        assert trace["metadata"]["user_id"] == "123"
        assert trace["metadata"]["request_id"] == "abc"


class TestTraceModel:
    """Tests for the Trace model."""

    def test_trace_default_values(self):
        """Trace should have sensible defaults."""
        trace = Trace()

        assert trace.trace_id is not None
        assert len(trace.trace_id) == 36  # UUID format
        assert trace.timestamp is not None
        assert trace.agent == "default"
        assert trace.evaluations == {}
        assert trace.metadata == {}

    def test_trace_to_json(self):
        """Trace should serialize to valid JSON."""
        trace = Trace(
            agent="test",
            metrics=TraceMetrics(
                duration_ms=1000,
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
            ),
        )

        json_str = trace.to_json()
        data = json.loads(json_str)

        assert data["agent"] == "test"
        assert data["metrics"]["duration_ms"] == 1000

    def test_trace_from_dict(self):
        """Trace should deserialize from dict."""
        data = {
            "trace_id": "test-123",
            "timestamp": "2026-01-22T00:00:00Z",
            "agent": "classifier",
            "metrics": {
                "duration_ms": 500,
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            },
        }

        trace = Trace.from_dict(data)

        assert trace.trace_id == "test-123"
        assert trace.agent == "classifier"
        assert trace.metrics.duration_ms == 500
