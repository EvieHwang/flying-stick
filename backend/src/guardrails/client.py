"""
Guarded Anthropic client wrapper.

Wraps the TracedAnthropicClient to apply guardrails at all stages.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TYPE_CHECKING

from .engine import GuardrailEngine
from .models import GuardrailContext, GuardrailBlockError


if TYPE_CHECKING:
    from anthropic import Anthropic
    from ..evaluation import Tracer, TracedAnthropicClient


logger = logging.getLogger(__name__)


class GuardedAnthropicClient:
    """
    Anthropic client wrapper with guardrails at all stages.

    Wraps TracedAnthropicClient (or plain Anthropic client) to apply:
    - Input guardrails before API call
    - Behavioral guardrails during agent loops
    - Output guardrails after API response
    """

    def __init__(
        self,
        client: "Anthropic | TracedAnthropicClient",
        guardrails: GuardrailEngine,
        agent: str,
        tracer: "Tracer | None" = None,
    ):
        """
        Initialize the guarded client.

        Args:
            client: Anthropic client or TracedAnthropicClient
            guardrails: GuardrailEngine instance
            agent: Agent name for guardrail lookup
            tracer: Optional Tracer for trace attachment
        """
        self.client = client
        self.guardrails = guardrails
        self.agent = agent
        self.tracer = tracer
        self._context: GuardrailContext | None = None

    def messages_create(
        self,
        check_input: bool = True,
        check_output: bool = True,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:
        """
        Create a message with guardrails applied.

        Args:
            check_input: Whether to run input guardrails
            check_output: Whether to run output guardrails
            metadata: Additional metadata for tracing
            **kwargs: Arguments passed to messages.create()

        Returns:
            Anthropic message response (possibly modified by output guardrails)

        Raises:
            GuardrailBlockError: If any guardrail blocks the request
        """
        # Prepare request data for guardrails
        request_data = self._prepare_request_data(kwargs)

        # Initialize context if not already done
        if self._context is None:
            self._context = self.guardrails.create_context(
                self.agent, request_data
            )
        else:
            # Update request in existing context
            self._context.request = request_data
            self._context.increment_iteration()

        # Input guardrails
        if check_input:
            self.guardrails.check_input(self.agent, request_data)

        # Behavioral guardrails (check iteration/tool counts)
        self.guardrails.check_behavioral(self._context)

        # Make the API call
        response = self._call_api(**kwargs)

        # Output guardrails
        if check_output:
            # Extract output content for guardrail checking
            output_data = self._extract_output_data(response)
            modified_output, _ = self.guardrails.check_output(
                self.agent, request_data, output_data
            )

            # If output was modified, we need to update the response
            # For now, we return the original response but log modifications
            if modified_output != output_data:
                logger.info(f"Output modified by guardrails for agent {self.agent}")

        return response

    def _prepare_request_data(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Prepare request data for guardrail checking."""
        # Extract relevant fields for guardrail checking
        messages = kwargs.get("messages", [])
        last_message = messages[-1] if messages else {}

        return {
            "model": kwargs.get("model"),
            "messages": messages,
            "system": kwargs.get("system"),
            "max_tokens": kwargs.get("max_tokens"),
            "temperature": kwargs.get("temperature"),
            "tools": kwargs.get("tools"),
            # Extract user input for easier rule writing
            "user_input": last_message.get("content") if isinstance(last_message, dict) else None,
        }

    def _call_api(self, **kwargs) -> Any:
        """Make the actual API call."""
        # Check if client is TracedAnthropicClient
        if hasattr(self.client, "messages_create"):
            return self.client.messages_create(**kwargs)

        # Plain Anthropic client
        return self.client.messages.create(**kwargs)

    def _extract_output_data(self, response: Any) -> dict[str, Any]:
        """Extract output data from response for guardrail checking."""
        output = {
            "stop_reason": getattr(response, "stop_reason", None),
        }

        # Extract text content
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, list) and len(content) > 0:
                first_block = content[0]
                if hasattr(first_block, "text"):
                    output["text"] = first_block.text
                elif isinstance(first_block, dict):
                    output["text"] = first_block.get("text")

            # Try to parse as JSON
            if "text" in output and output["text"]:
                try:
                    parsed = json.loads(output["text"])
                    output["parsed"] = parsed
                    # Merge parsed fields into output for easier rule access
                    if isinstance(parsed, dict):
                        output.update(parsed)
                except (json.JSONDecodeError, TypeError):
                    pass

        return output

    def check_tool_call(self, tool_name: str) -> None:
        """
        Check behavioral guardrails before a tool call.

        Call this before each tool execution in an agent loop.

        Args:
            tool_name: Name of the tool being called

        Raises:
            GuardrailBlockError: If tool call is blocked
        """
        if self._context is None:
            raise RuntimeError(
                "Context not initialized. Call messages_create first."
            )

        self.guardrails.check_behavioral(self._context, tool_name)

    def get_context(self) -> GuardrailContext | None:
        """Get the current guardrail context."""
        return self._context

    def reset(self) -> None:
        """Reset for a new request."""
        self._context = None
        self.guardrails.reset()

    def get_summary(self) -> dict[str, Any]:
        """Get guardrail summary for current request."""
        return self.guardrails.get_summary()


def get_guarded_client(
    api_key: str | None = None,
    agent: str = "default",
    guardrails_config: str | None = None,
    enable_tracing: bool = True,
    trace_bucket: str | None = None,
) -> GuardedAnthropicClient:
    """
    Convenience function to create a fully configured guarded client.

    Args:
        api_key: Anthropic API key (uses env var if not provided)
        agent: Agent name for guardrail lookup
        guardrails_config: Path to guardrails.yaml
        enable_tracing: Whether to enable tracing
        trace_bucket: S3 bucket for traces

    Returns:
        Configured GuardedAnthropicClient
    """
    from anthropic import Anthropic

    # Create base client
    client = Anthropic(api_key=api_key)

    # Create tracer if enabled
    tracer = None
    if enable_tracing:
        from ..evaluation import Tracer
        tracer = Tracer(bucket=trace_bucket)

    # Wrap with tracing if enabled
    if tracer and tracer.enabled:
        from ..evaluation import TracedAnthropicClient
        traced_client = TracedAnthropicClient(
            client=client,
            tracer=tracer,
            agent=agent,
        )
        base_client = traced_client
    else:
        base_client = client

    # Create guardrails engine
    guardrails = GuardrailEngine(config_path=guardrails_config, tracer=tracer)

    return GuardedAnthropicClient(
        client=base_client,
        guardrails=guardrails,
        agent=agent,
        tracer=tracer,
    )
