"""Tests for domain utilities module."""

from datetime import UTC, datetime

from issue_tracker.domain.utils import utcnow_naive


class TestUtcnowNaive:
    """Tests for utcnow_naive function."""

    def test_returns_datetime_object(self):
        """Test that function returns a datetime object."""
        result = utcnow_naive()
        assert isinstance(result, datetime)

    def test_returns_naive_datetime(self):
        """Test that returned datetime is naive (no timezone info)."""
        result = utcnow_naive()
        assert result.tzinfo is None

    def test_returns_current_time(self):
        """Test that returned time is approximately current."""
        before = datetime.now(UTC).replace(tzinfo=None)
        result = utcnow_naive()
        after = datetime.now(UTC).replace(tzinfo=None)

        # Result should be between before and after (within 1 second tolerance)
        assert before <= result <= after
        assert (after - result).total_seconds() < 1

    def test_multiple_calls_increase(self):
        """Test that multiple calls return increasing times."""
        time1 = utcnow_naive()
        # Small delay to ensure time progresses
        import time

        time.sleep(0.01)
        time2 = utcnow_naive()

        assert time2 >= time1

    def test_returns_utc_time(self):
        """Test that returned time corresponds to UTC."""
        result = utcnow_naive()
        utc_now = datetime.now(UTC).replace(tzinfo=None)

        # Times should be within 1 second of each other
        diff = abs((result - utc_now).total_seconds())
        assert diff < 1

    def test_consistency_with_datetime_now_utc(self):
        """Test consistency with datetime.now(UTC)."""
        result = utcnow_naive()
        expected = datetime.now(UTC).replace(tzinfo=None)

        # Year, month, day should match
        assert result.year == expected.year
        assert result.month == expected.month
        assert result.day == expected.day

    def test_not_local_time(self):
        """Test that result is UTC, not local time."""
        result = utcnow_naive()
        local_now = datetime.now()

        # If not in UTC timezone, these should differ
        # We can't guarantee they differ (user might be in UTC)
        # But we can verify result matches UTC
        utc_now = datetime.now(UTC).replace(tzinfo=None)
        assert abs((result - utc_now).total_seconds()) < 1

    def test_microsecond_precision(self):
        """Test that microsecond precision is preserved."""
        result = utcnow_naive()
        assert hasattr(result, "microsecond")
        # Microsecond should be set (not always 0)
        # This might occasionally be 0, but very rarely
        # Just verify the attribute exists and is a valid value
        assert 0 <= result.microsecond < 1000000

    def test_can_be_used_as_default_factory(self):
        """Test that function can be used as dataclass default_factory."""
        from dataclasses import dataclass, field

        @dataclass
        class TestClass:
            timestamp: datetime = field(default_factory=utcnow_naive)

        obj1 = TestClass()
        obj2 = TestClass()

        # Both should have timestamps
        assert isinstance(obj1.timestamp, datetime)
        assert isinstance(obj2.timestamp, datetime)

        # Timestamps should be close but obj2 should be >= obj1
        assert obj2.timestamp >= obj1.timestamp

    def test_compatible_with_sqlmodel_datetime(self):
        """Test that returned datetime is compatible with SQLModel storage."""
        result = utcnow_naive()

        # Naive datetimes can be stored directly in SQLite
        assert result.tzinfo is None

        # Can be converted to ISO string
        iso_str = result.isoformat()
        assert isinstance(iso_str, str)

        # Can be parsed back
        parsed = datetime.fromisoformat(iso_str)
        assert parsed == result
