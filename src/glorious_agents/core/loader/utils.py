"""Utility functions for skill loading."""

from typing import Any


def normalize_config_schema(schema_data: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Normalize config schema by extracting properties from JSON Schema format.

    If the schema_data contains a "properties" key (JSON Schema format), extract
    and return just the properties dict. Otherwise, return the schema as-is.

    Args:
        schema_data: Raw schema data which may be in JSON Schema format

    Returns:
        Normalized schema dict with just the properties, or None if no schema

    Examples:
        >>> schema = {"properties": {"key": {"type": "string"}}}
        >>> normalize_config_schema(schema)
        {"key": {"type": "string"}}

        >>> schema = {"key": {"type": "string"}}
        >>> normalize_config_schema(schema)
        {"key": {"type": "string"}}

        >>> normalize_config_schema(None)
        None
    """
    if not schema_data or not isinstance(schema_data, dict):
        return None

    # If it's a JSON Schema with "properties", extract them
    if "properties" in schema_data:
        return dict(schema_data["properties"])

    # Otherwise return as-is
    return dict(schema_data)
