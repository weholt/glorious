"""Tests for entity utility functions."""

from datetime import datetime

from issue_tracker.domain.entities.dependency import utcnow_naive as dep_utcnow
from issue_tracker.domain.entities.epic import utcnow_naive as epic_utcnow
from issue_tracker.domain.entities.label import utcnow_naive as label_utcnow


def test_label_utcnow_naive():
    """Test label utcnow_naive returns naive datetime."""
    dt = label_utcnow()
    assert isinstance(dt, datetime)
    assert dt.tzinfo is None


def test_epic_utcnow_naive():
    """Test epic utcnow_naive returns naive datetime."""
    dt = epic_utcnow()
    assert isinstance(dt, datetime)
    assert dt.tzinfo is None


def test_dep_utcnow_naive():
    """Test dependency utcnow_naive returns naive datetime."""
    dt = dep_utcnow()
    assert isinstance(dt, datetime)
    assert dt.tzinfo is None
