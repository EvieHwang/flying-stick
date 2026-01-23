"""
Traced Anthropic client wrapper.

Provides a drop-in replacement for the Anthropic client that automatically
traces all API calls.
"""

import os
from typing import Any

from anthropic import Anthropic
from anthropic.types import Message

from .tracer import Tracer


class TracedAnthropicClient:
    """
    Wrapper around Anthropic client that traces all calls.

    Usage:
        client = TracedAnthropicClient(agent="classifier")
        response = client.messages_create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello!"}]
        )

    The trace is automatically captured and stored in S3.
    """

    def __init__(
        self,
        agent: str = "default",
        tracer: Tracer | None = None,
        api_key: str | None = None,
        **anthropic_kwargs: Any,
    ):
        """
        Initialize the traced client.

        Args:
            agent: Agent identifier for traces (default: "default")
            tracer: Tracer instance (default: creates new one)
            api_key: Anthropic API key (default: from environment)
            **anthropic_kwargs: Additional kwargs for Anthropic client
        """
        self.agent = agent
        self.tracer = tracer or Tracer()

        # Initialize Anthropic client
        if api_key:
            anthropic_kwargs["api_key"] = api_key
        self._client = Anthropic(**anthropic_kwargs)

    @property
    def client(self) -> Anthropic:
        """Access the underlying Anthropic client."""
        return self._client

    def messages_create(
        self,
        metadata: dict[str, Any] | None = None,
        trace_metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Message:
        """
        Create a message with automatic tracing.

        Args:
            metadata: Metadata to pass to Anthropic API
            trace_metadata: Custom metadata to attach to trace
            **kwargs: Arguments for messages.create()

        Returns:
            Anthropic Message response
        """
        # Merge metadata
        if metadata:
            kwargs["metadata"] = metadata

        # Capture request data for trace
        request_data = dict(kwargs)

        # Execute with tracing
        return self.tracer.trace_call(
            agent=self.agent,
            call_fn=lambda: self._client.messages.create(**kwargs),
            request_data=request_data,
            metadata=trace_metadata,
        )

    def with_agent(self, agent: str) -> "TracedAnthropicClient":
        """
        Create a new client instance with a different agent identifier.

        Useful for making calls with different agent names without
        creating entirely new clients.

        Args:
            agent: New agent identifier

        Returns:
            New TracedAnthropicClient with same tracer and Anthropic client
        """
        new_client = TracedAnthropicClient.__new__(TracedAnthropicClient)
        new_client.agent = agent
        new_client.tracer = self.tracer
        new_client._client = self._client
        return new_client


def get_traced_client(
    agent: str = "default",
    api_key: str | None = None,
) -> TracedAnthropicClient:
    """
    Convenience function to create a traced client.

    Fetches API key from environment or AWS Secrets Manager if not provided.

    Args:
        agent: Agent identifier
        api_key: Optional API key (default: from env or secrets)

    Returns:
        TracedAnthropicClient instance
    """
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if api_key is None:
        # Try to get from Secrets Manager
        try:
            from ..utils.secrets import get_secret_value
            secret_name = os.environ.get("SECRET_NAME", "{{PROJECT_NAME}}/prod")
            api_key = get_secret_value(secret_name, "ANTHROPIC_API_KEY")
        except Exception:
            pass  # Let Anthropic client handle missing key

    return TracedAnthropicClient(agent=agent, api_key=api_key)
