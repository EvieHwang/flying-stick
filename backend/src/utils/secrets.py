"""
AWS Secrets Manager helper module.

This module provides functions for fetching and caching secrets from
AWS Secrets Manager. Secrets are cached at the module level to optimize
Lambda warm starts.

Usage:
    from utils.secrets import get_secret, get_secret_value

    # Get entire secret as dict
    secret = get_secret("{{PROJECT_NAME}}/prod")

    # Get specific key from JSON secret
    api_key = get_secret_value("{{PROJECT_NAME}}/prod", "ANTHROPIC_API_KEY")
"""

import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Module-level cache for secrets (persists across Lambda warm starts)
_secrets_cache: dict[str, dict[str, Any]] = {}


def get_secret(secret_name: str, region_name: str = "{{AWS_REGION}}") -> dict[str, Any]:
    """
    Fetch a secret from AWS Secrets Manager.

    Secrets are cached at the module level to avoid redundant API calls
    during Lambda warm starts.

    Args:
        secret_name: Name or ARN of the secret in Secrets Manager
        region_name: AWS region where the secret is stored

    Returns:
        Dictionary containing the secret key-value pairs

    Raises:
        SecretNotFoundError: If the secret does not exist
        SecretAccessError: If access to the secret is denied
        SecretParseError: If the secret value is not valid JSON
    """
    # Check cache first
    if secret_name in _secrets_cache:
        logger.debug(f"Returning cached secret: {secret_name}")
        return _secrets_cache[secret_name]

    # Fetch from Secrets Manager
    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")

        if error_code == "ResourceNotFoundException":
            raise SecretNotFoundError(
                f"Secret '{secret_name}' not found in Secrets Manager. "
                f"Create it with: aws secretsmanager create-secret --name {secret_name} --secret-string '{{}}'"
            ) from e
        elif error_code == "AccessDeniedException":
            raise SecretAccessError(
                f"Access denied to secret '{secret_name}'. "
                "Ensure the Lambda IAM role has secretsmanager:GetSecretValue permission."
            ) from e
        else:
            raise SecretAccessError(
                f"Failed to retrieve secret '{secret_name}': {error_code}"
            ) from e

    # Parse the secret value
    secret_string = response.get("SecretString")
    if not secret_string:
        raise SecretParseError(
            f"Secret '{secret_name}' has no string value. Binary secrets are not supported."
        )

    try:
        secret_dict = json.loads(secret_string)
    except json.JSONDecodeError as e:
        raise SecretParseError(
            f"Secret '{secret_name}' is not valid JSON: {e}"
        ) from e

    # Cache and return
    _secrets_cache[secret_name] = secret_dict
    logger.info(f"Cached secret: {secret_name}")
    return secret_dict


def get_secret_value(
    secret_name: str, key: str, region_name: str = "{{AWS_REGION}}"
) -> str:
    """
    Get a specific value from a JSON secret.

    Args:
        secret_name: Name or ARN of the secret in Secrets Manager
        key: Key to retrieve from the JSON secret
        region_name: AWS region where the secret is stored

    Returns:
        The string value for the specified key

    Raises:
        SecretKeyError: If the key does not exist in the secret
        SecretNotFoundError: If the secret does not exist
        SecretAccessError: If access to the secret is denied
    """
    secret = get_secret(secret_name, region_name)

    if key not in secret:
        available_keys = ", ".join(secret.keys()) if secret else "(empty)"
        raise SecretKeyError(
            f"Key '{key}' not found in secret '{secret_name}'. "
            f"Available keys: {available_keys}"
        )

    return str(secret[key])


def clear_cache() -> None:
    """
    Clear the secrets cache.

    Useful for testing or when secrets have been rotated and need to be
    re-fetched before the Lambda instance is recycled.
    """
    global _secrets_cache
    _secrets_cache = {}
    logger.info("Secrets cache cleared")


# Custom exceptions for clear error handling


class SecretNotFoundError(Exception):
    """Raised when a secret does not exist in Secrets Manager."""

    pass


class SecretAccessError(Exception):
    """Raised when access to a secret is denied."""

    pass


class SecretParseError(Exception):
    """Raised when a secret value cannot be parsed."""

    pass


class SecretKeyError(Exception):
    """Raised when a key does not exist in a secret."""

    pass
