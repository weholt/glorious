"""Unit tests for input validation framework."""

import pytest
from pydantic import Field, ValidationError

from glorious_agents.core.validation import (
    SkillInput,
    ValidationException,
    validate_dict,
    validate_input,
)


class SimpleInput(SkillInput):
    """Test input model."""

    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=0, le=150)
    tags: str = Field("", max_length=200)


class NestedInput(SkillInput):
    """Test nested input model."""

    title: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


def test_skill_input_valid() -> None:
    """Test valid input creation."""
    input_data = SimpleInput(name="test", age=25, tags="tag1,tag2")
    assert input_data.name == "test"
    assert input_data.age == 25
    assert input_data.tags == "tag1,tag2"


def test_skill_input_strip_whitespace() -> None:
    """Test automatic whitespace stripping."""
    input_data = SimpleInput(name="  test  ", age=25)
    assert input_data.name == "test"


def test_skill_input_validation_min_length() -> None:
    """Test min_length validation."""
    with pytest.raises(ValidationError, match="String should have at least 1 character"):
        SimpleInput(name="", age=25)


def test_skill_input_validation_max_length() -> None:
    """Test max_length validation."""
    with pytest.raises(ValidationError, match="String should have at most 50 characters"):
        SimpleInput(name="a" * 51, age=25)


def test_skill_input_validation_range() -> None:
    """Test numeric range validation."""
    with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
        SimpleInput(name="test", age=-1)

    with pytest.raises(ValidationError, match="Input should be less than or equal to 150"):
        SimpleInput(name="test", age=151)


def test_skill_input_extra_fields_forbidden() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SimpleInput(name="test", age=25, extra_field="invalid")  # type: ignore[call-arg]


def test_validate_dict_valid() -> None:
    """Test validate_dict with valid data."""
    data = {"name": "test", "age": 25}
    validated = validate_dict(data, SimpleInput)
    assert validated.name == "test"
    assert validated.age == 25


def test_validate_dict_invalid() -> None:
    """Test validate_dict with invalid data."""
    data = {"name": "", "age": 25}
    with pytest.raises(ValidationException) as exc_info:
        validate_dict(data, SimpleInput)

    assert "validation failed" in str(exc_info.value).lower()


def test_validate_input_decorator_simple() -> None:
    """Test validate_input decorator with simple types."""

    @validate_input
    def add_note(content: str, tags: str = "") -> str:
        return f"{content}:{tags}"

    result = add_note("test content", tags="tag1")
    assert result == "test content:tag1"


def test_validate_input_decorator_model() -> None:
    """Test validate_input decorator with Pydantic model."""

    @validate_input
    def process_input(data: SimpleInput) -> str:
        return f"{data.name}-{data.age}"

    # Pass as dict
    result = process_input(data={"name": "Alice", "age": 30})
    assert result == "Alice-30"

    # Pass as model instance
    input_model = SimpleInput(name="Bob", age=25)
    result = process_input(data=input_model)
    assert result == "Bob-25"


def test_validate_input_decorator_validation_error() -> None:
    """Test validate_input decorator raises ValidationException."""

    @validate_input
    def process_input(data: SimpleInput) -> str:
        return data.name

    with pytest.raises(ValidationException) as exc_info:
        process_input(data={"name": "", "age": 25})

    assert "validation failed" in str(exc_info.value).lower()
    assert len(exc_info.value.errors) > 0


def test_validate_input_decorator_missing_required() -> None:
    """Test validation with missing required field."""

    @validate_input
    def process_input(data: SimpleInput) -> str:
        return data.name

    with pytest.raises(ValidationException):
        process_input(data={"name": "test"})  # Missing required 'age'


def test_validation_exception_formatting() -> None:
    """Test ValidationException message formatting."""
    try:
        SimpleInput(name="", age=-1)
    except Exception as e:
        errors = e.errors() if hasattr(e, "errors") else []  # type: ignore[attr-defined]
        if errors:
            exc = ValidationException(errors)
            message = str(exc)
            assert "validation failed" in message.lower()
            assert "name" in message.lower() or "age" in message.lower()


def test_nested_input_validation() -> None:
    """Test nested model validation."""
    valid_data = NestedInput(title="test", metadata={"key": "value"})
    assert valid_data.title == "test"
    assert valid_data.metadata == {"key": "value"}

    with pytest.raises(ValidationError, match="String should have at least 1 character"):
        NestedInput(title="", metadata={})
