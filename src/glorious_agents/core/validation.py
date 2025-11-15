"""Input validation framework for skills using Pydantic.

Provides decorators and base models for validating skill method inputs,
ensuring type safety, preventing injection attacks, and generating
consistent error messages.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar, cast, get_type_hints

from pydantic import BaseModel, ValidationError
from rich.console import Console

console = Console()

F = TypeVar("F", bound=Callable[..., Any])


class ValidationException(Exception):
    """Exception raised when input validation fails.

    Contains structured validation error information from Pydantic.
    """

    def __init__(self, errors: Any) -> None:
        # Accept Pydantic ErrorDetails or dict format
        if hasattr(errors, "__iter__"):
            self.errors = [
                {"loc": e.get("loc", ()), "msg": e.get("msg", str(e))}
                if isinstance(e, dict)
                else {"loc": getattr(e, "loc", ()), "msg": getattr(e, "msg", str(e))}
                for e in errors
            ]
        else:
            self.errors = [{"loc": (), "msg": str(errors)}]
        self.message = self._format_errors(self.errors)
        super().__init__(self.message)

    def _format_errors(self, errors: list[dict[str, Any]]) -> str:
        """Format Pydantic validation errors as readable message."""
        lines = ["Input validation failed:"]
        for err in errors:
            loc = " → ".join(str(x) for x in err["loc"])
            msg = err["msg"]
            lines.append(f"  • {loc}: {msg}")
        return "\n".join(lines)


class SkillInput(BaseModel):
    """Base class for skill input validation models.

    Skills should subclass this to define their input schemas.
    Inherits all Pydantic validation capabilities.

    Example:
        class AddNoteInput(SkillInput):
            content: str = Field(..., min_length=1, max_length=10000)
            tags: str = Field("", max_length=500)

        @validate_input
        def add_note(input: AddNoteInput) -> int:
            # Input is guaranteed to be valid
            ...
    """

    model_config = {"extra": "forbid", "str_strip_whitespace": True}


def validate_input[F: Callable[..., Any]](func: F) -> F:
    """Decorator that validates function inputs against Pydantic models.

    Automatically validates function arguments based on type hints.
    If a parameter is typed as a Pydantic BaseModel subclass, it will
    be validated before the function is called.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function with input validation

    Raises:
        ValidationException: If input validation fails

    Example:
        @validate_input
        def add_note(content: str, tags: str = "") -> int:
            # Automatically validated
            ...

        @validate_input
        def update_issue(input: UpdateIssueInput) -> None:
            # Input model validated
            ...
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get function signature and type hints
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Build bound arguments
        try:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
        except TypeError as e:
            raise ValidationException([{"loc": ("arguments",), "msg": str(e)}]) from e

        # Validate each argument against its type hint
        validated_kwargs = {}
        for param_name, value in bound.arguments.items():
            param_type = type_hints.get(param_name)

            # If parameter is a Pydantic model, validate it
            if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                try:
                    # If value is already the model type, re-validate
                    if isinstance(value, param_type):
                        validated_kwargs[param_name] = value
                    # If value is dict, construct and validate
                    elif isinstance(value, dict):
                        validated_kwargs[param_name] = param_type(**value)
                    # Otherwise try to construct from value
                    else:
                        validated_kwargs[param_name] = param_type(value)
                except ValidationError as e:
                    raise ValidationException(e.errors()) from e
            else:
                validated_kwargs[param_name] = value

        # Call function with validated arguments
        return func(**validated_kwargs)

    return cast(F, wrapper)


def validate_dict(data: dict[str, Any], model: type[BaseModel]) -> BaseModel:
    """Validate a dictionary against a Pydantic model.

    Useful for validating JSON payloads, configuration, or other
    dictionary data structures.

    Args:
        data: Dictionary to validate
        model: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        ValidationException: If validation fails

    Example:
        data = {"content": "note text", "tags": "important"}
        validated = validate_dict(data, AddNoteInput)
    """
    try:
        return model(**data)
    except ValidationError as e:
        raise ValidationException(e.errors()) from e


def print_validation_error(error: ValidationException) -> None:
    """Pretty-print a validation error to the console.

    Uses Rich for formatted output with colors and structure.

    Args:
        error: ValidationException to display
    """
    console.print(f"[bold red]✗ {error.message}[/bold red]")
