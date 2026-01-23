"""
Lambda handler for {{PROJECT_NAME}}.

This module provides the main entry point for AWS Lambda invocations.
"""

import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs

from .evaluation import Tracer


# Lazy-loaded tracer instance
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """Get or create the tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def lambda_handler(event: dict, context) -> dict:
    """
    Main Lambda handler function.

    Args:
        event: API Gateway event dictionary
        context: Lambda context object

    Returns:
        API Gateway response dictionary
    """
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "/")

    # Route requests
    if path == "/health" or path == "/":
        return health_check()

    # Trace API endpoints
    if path == "/traces" and http_method == "GET":
        return list_traces(event)

    # Match /traces/{trace_id} pattern
    trace_match = re.match(r"^/traces/([a-f0-9-]+)$", path)
    if trace_match and http_method == "GET":
        trace_id = trace_match.group(1)
        return get_trace(event, trace_id)

    # Default 404 for unknown paths
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Not found", "path": path}),
    }


def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        API Gateway response with health status
    """
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "{{PROJECT_NAME}}",
            }
        ),
    }


def list_traces(event: dict) -> dict:
    """
    List traces with optional filters.

    Query parameters:
        - agent: Filter by agent name
        - start: Start date (YYYY-MM-DD)
        - end: End date (YYYY-MM-DD)
        - limit: Max traces to return (default: 100)
        - token: Continuation token for pagination

    Returns:
        API Gateway response with trace list
    """
    # Parse query parameters
    params = event.get("queryStringParameters") or {}

    agent = params.get("agent")
    start_date = params.get("start")
    end_date = params.get("end")
    limit = int(params.get("limit", "100"))
    continuation_token = params.get("token")

    # Validate limit
    if limit < 1 or limit > 1000:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "limit must be between 1 and 1000"}),
        }

    # Get traces from S3
    tracer = get_tracer()
    traces, next_token = tracer.list_traces(
        agent=agent,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        continuation_token=continuation_token,
    )

    response_body = {
        "traces": traces,
        "count": len(traces),
    }
    if next_token:
        response_body["next_token"] = next_token

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(response_body, default=str),
    }


def get_trace(event: dict, trace_id: str) -> dict:
    """
    Get a single trace by ID.

    Requires agent and date query parameters to locate the trace.

    Query parameters:
        - agent: Agent name (required)
        - date: Date of trace (YYYY-MM-DD) (required)

    Returns:
        API Gateway response with full trace
    """
    # Parse query parameters
    params = event.get("queryStringParameters") or {}

    agent = params.get("agent")
    date = params.get("date")

    if not agent or not date:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Missing required query parameters: agent, date"
            }),
        }

    # Get trace from S3
    tracer = get_tracer()
    trace = tracer.get_trace(trace_id=trace_id, agent=agent, date=date)

    if trace is None:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Trace not found",
                "trace_id": trace_id,
            }),
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": trace.to_json(),
    }
