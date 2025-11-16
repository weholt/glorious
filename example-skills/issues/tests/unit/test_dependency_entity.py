"""Tests for Dependency entity."""

import pytest
from datetime import UTC, datetime

from issue_tracker.domain.entities.dependency import Dependency, DependencyType
from issue_tracker.domain.exceptions import InvariantViolationError


class TestDependencyValidation:
    """Test dependency entity validation."""

    def test_dependency_with_description_trimming(self) -> None:
        """Test that description is trimmed."""
        dep = Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
            description="  Some description with spaces  ",
        )
        assert dep.description == "Some description with spaces"

    def test_dependency_with_empty_description(self) -> None:
        """Test that empty description becomes None."""
        dep = Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.BLOCKS,
            description="   ",
        )
        assert dep.description is None

    def test_dependency_discovered_from_type(self) -> None:
        """Test DISCOVERED_FROM dependency type."""
        dep = Dependency(
            from_issue_id="ISS-A",
            to_issue_id="ISS-B",
            dependency_type=DependencyType.DISCOVERED_FROM,
        )
        assert dep.dependency_type == DependencyType.DISCOVERED_FROM
        assert dep.dependency_type.value == "discovered-from"
