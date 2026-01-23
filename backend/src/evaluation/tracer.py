"""
Trace capture and S3 storage.

The Tracer wraps API calls to capture timing, token usage, and responses,
then stores the resulting traces to S3 for later analysis.
"""

import hashlib
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

import boto3
from botocore.exceptions import ClientError

from .models import Trace, TraceRequest, TraceResponse, TraceMetrics, ToolCall
from .evaluator import Evaluator


logger = logging.getLogger(__name__)

T = TypeVar("T")

# Maximum response size before truncation (100KB)
MAX_RESPONSE_SIZE = 100 * 1024


class Tracer:
    """
    Captures and stores traces for AI API calls.

    Usage:
        tracer = Tracer(bucket="my-traces-bucket")
        result = tracer.trace_call(
            agent="classifier",
            call_fn=lambda: client.messages.create(...),
            request_data={...}
        )
    """

    def __init__(
        self,
        bucket: str | None = None,
        evaluator: Evaluator | None = None,
        enabled: bool = True,
        async_write: bool = True,
    ):
        """
        Initialize the tracer.

        Args:
            bucket: S3 bucket name (default: TRACE_BUCKET env var)
            evaluator: Evaluator instance (default: creates new one)
            enabled: Whether tracing is enabled (default: True)
            async_write: Whether to write asynchronously (default: True)
        """
        self.bucket = bucket or os.environ.get("TRACE_BUCKET")
        self.enabled = enabled and self.bucket is not None
        self.async_write = async_write

        # Lazy-load evaluator and S3 client
        self._evaluator = evaluator
        self._s3_client = None
        self._executor = None

        if not self.bucket and enabled:
            logger.warning(
                "TRACE_BUCKET not set, tracing disabled. "
                "Set TRACE_BUCKET environment variable to enable."
            )

    @property
    def evaluator(self) -> Evaluator:
        """Lazy-load evaluator."""
        if self._evaluator is None:
            self._evaluator = Evaluator()
        return self._evaluator

    @property
    def s3(self):
        """Lazy-load S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client("s3")
        return self._s3_client

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Lazy-load thread pool executor."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=2)
        return self._executor

    def trace_call(
        self,
        agent: str,
        call_fn: Callable[[], T],
        request_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> T:
        """
        Execute a function while capturing a trace.

        Args:
            agent: Agent identifier for this call
            call_fn: Function that makes the API call
            request_data: Request parameters (for trace record)
            metadata: Optional custom metadata

        Returns:
            The result of call_fn()

        Raises:
            Whatever call_fn raises (after recording error in trace)
        """
        if not self.enabled:
            return call_fn()

        start_time = time.perf_counter()
        error = None
        response = None

        try:
            response = call_fn()
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # Build trace
            trace = self._build_trace(
                agent=agent,
                request_data=request_data,
                response=response,
                error=error,
                duration_ms=duration_ms,
                metadata=metadata or {},
            )

            # Run evaluations
            trace = self.evaluator.evaluate(trace)

            # Log evaluation failures
            self._log_evaluation_failures(trace)

            # Write to S3
            if self.async_write:
                self.executor.submit(self._write_trace, trace)
            else:
                self._write_trace(trace)

    def _build_trace(
        self,
        agent: str,
        request_data: dict[str, Any],
        response: Any,
        error: str | None,
        duration_ms: int,
        metadata: dict[str, Any],
    ) -> Trace:
        """Build a Trace object from call data."""
        # Extract request info
        messages = request_data.get("messages", [])
        input_text = messages[-1].get("content", "") if messages else ""
        if isinstance(input_text, list):
            # Handle content blocks
            input_text = " ".join(
                block.get("text", "") for block in input_text
                if isinstance(block, dict) and block.get("type") == "text"
            )

        model = request_data.get("model", "unknown")
        system = request_data.get("system", "")
        system_hash = hashlib.sha256(system.encode()).hexdigest()[:8] if system else None

        trace_request = TraceRequest(
            input=input_text[:10000],  # Limit input size
            model=model,
            system_hash=system_hash,
            parameters={
                k: v for k, v in request_data.items()
                if k not in ("messages", "system", "model")
            },
        )

        # Extract response info
        trace_response = None
        trace_metrics = None
        tool_calls = []

        if response is not None and not error:
            # Handle Anthropic Message response
            output = self._extract_output(response)
            raw_response = self._truncate_response(response)

            trace_response = TraceResponse(
                output=output,
                stop_reason=getattr(response, "stop_reason", None),
                raw_response=raw_response,
            )

            # Extract metrics
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
            trace_metrics = TraceMetrics(
                duration_ms=duration_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )

            # Extract tool calls
            tool_calls = self._extract_tool_calls(response)
        else:
            # Error case - still record duration
            trace_metrics = TraceMetrics(
                duration_ms=duration_ms,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
            )

        return Trace(
            agent=agent,
            request=trace_request,
            response=trace_response,
            metrics=trace_metrics,
            tool_calls=tool_calls,
            error=error,
            metadata=metadata,
        )

    def _extract_output(self, response: Any) -> Any:
        """Extract output text or structured data from response."""
        content = getattr(response, "content", None)
        if not content:
            return None

        # Handle content blocks
        if isinstance(content, list):
            texts = []
            for block in content:
                if hasattr(block, "text"):
                    texts.append(block.text)
                elif hasattr(block, "type") and block.type == "tool_use":
                    # Include tool use info
                    texts.append(f"[tool_use: {block.name}]")
            return "\n".join(texts) if texts else None

        return str(content)

    def _extract_tool_calls(self, response: Any) -> list[ToolCall]:
        """Extract tool calls from response."""
        content = getattr(response, "content", None)
        if not content or not isinstance(content, list):
            return []

        tool_calls = []
        for block in content:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append(ToolCall(
                    name=getattr(block, "name", "unknown"),
                    input=getattr(block, "input", {}),
                    output=None,  # Would need tool result to populate
                    duration_ms=0,
                ))

        return tool_calls

    def _truncate_response(self, response: Any) -> dict | None:
        """Truncate large responses to prevent S3 bloat."""
        try:
            # Convert to dict if possible
            if hasattr(response, "model_dump"):
                response_dict = response.model_dump()
            elif hasattr(response, "__dict__"):
                response_dict = dict(response.__dict__)
            else:
                response_dict = {"raw": str(response)}

            # Check size
            json_str = json.dumps(response_dict, default=str)
            if len(json_str) > MAX_RESPONSE_SIZE:
                return {
                    "_truncated": True,
                    "_original_size": len(json_str),
                    "stop_reason": response_dict.get("stop_reason"),
                    "usage": response_dict.get("usage"),
                }

            return response_dict

        except Exception as e:
            logger.debug(f"Could not serialize response: {e}")
            return None

    def _write_trace(self, trace: Trace) -> None:
        """Write trace to S3."""
        if not self.bucket:
            return

        # Build S3 key: traces/{agent}/{YYYY-MM-DD}/{trace_id}.json
        date = trace.timestamp[:10]  # Extract YYYY-MM-DD
        key = f"traces/{trace.agent}/{date}/{trace.trace_id}.json"

        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=trace.to_json(),
                ContentType="application/json",
            )
            logger.debug(f"Wrote trace to s3://{self.bucket}/{key}")
        except ClientError as e:
            logger.error(f"Failed to write trace to S3: {e}")

    def _log_evaluation_failures(self, trace: Trace) -> None:
        """Log Layer 1 evaluation failures for alerting."""
        for name, result in trace.evaluations.items():
            if result.layer == 1 and result.result == "fail":
                logger.warning(
                    f"Layer 1 evaluation FAILED: {name} for trace {trace.trace_id}. "
                    f"Message: {result.message}"
                )

    def get_trace(self, trace_id: str, agent: str, date: str) -> Trace | None:
        """
        Retrieve a trace from S3.

        Args:
            trace_id: The trace UUID
            agent: Agent name
            date: Date string (YYYY-MM-DD)

        Returns:
            Trace object or None if not found
        """
        if not self.bucket:
            return None

        key = f"traces/{agent}/{date}/{trace_id}.json"

        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response["Body"].read().decode("utf-8"))
            return Trace.from_dict(data)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    def list_traces(
        self,
        agent: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        """
        List traces from S3 with optional filters.

        Args:
            agent: Filter by agent name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum traces to return
            continuation_token: Token for pagination

        Returns:
            Tuple of (list of trace summaries, next continuation token)
        """
        if not self.bucket:
            return [], None

        # Build prefix
        prefix = "traces/"
        if agent:
            prefix = f"traces/{agent}/"

        # List objects
        kwargs = {
            "Bucket": self.bucket,
            "Prefix": prefix,
            "MaxKeys": limit,
        }
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        try:
            response = self.s3.list_objects_v2(**kwargs)
        except ClientError as e:
            logger.error(f"Failed to list traces: {e}")
            return [], None

        # Filter and extract summaries
        traces = []
        for obj in response.get("Contents", []):
            key = obj["Key"]
            # Parse key: traces/{agent}/{date}/{trace_id}.json
            parts = key.split("/")
            if len(parts) != 4:
                continue

            obj_agent = parts[1]
            obj_date = parts[2]
            trace_id = parts[3].replace(".json", "")

            # Apply date filters
            if start_date and obj_date < start_date:
                continue
            if end_date and obj_date > end_date:
                continue

            traces.append({
                "trace_id": trace_id,
                "agent": obj_agent,
                "date": obj_date,
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })

        next_token = response.get("NextContinuationToken")
        return traces, next_token
