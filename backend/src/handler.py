"""
Lambda handler for {{PROJECT_NAME}}.

This module provides the main entry point for AWS Lambda invocations.
"""

import json
from datetime import datetime, timezone


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
