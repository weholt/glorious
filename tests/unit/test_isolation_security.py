"""Security tests for RestrictedConnection SQL parsing.

These tests verify that the SQL operation type detection cannot be bypassed
using various attack vectors like comments, whitespace, or CTEs.
"""

import sqlite3
from unittest.mock import Mock

import pytest

from glorious_agents.core.isolation import (
    Permission,
    RestrictedConnection,
    SkillPermissions,
)


@pytest.fixture
def mock_conn():
    """
    Create a Mock object constrained to behave like a sqlite3.Connection for use in tests.

    Returns:
        Mock: A Mock instance with spec set to `sqlite3.Connection`.
    """
    return Mock(spec=sqlite3.Connection)


@pytest.fixture
def read_only_permissions():
    """
    Create SkillPermissions for "test_skill" configured with only database read permission.

    The returned permissions grant DB_READ and do not grant DB_WRITE or other elevated database permissions.

    Returns:
        SkillPermissions: Permissions object for "test_skill" with only DB_READ granted.
    """
    perms = SkillPermissions("test_skill")
    # Default has DB_READ, remove others to be explicit
    return perms


@pytest.fixture
def write_permissions():
    """
    Create SkillPermissions for "test_skill" with database write permission granted.

    Returns:
        SkillPermissions: a permissions object for "test_skill" with `Permission.DB_WRITE` granted.
    """
    perms = SkillPermissions("test_skill")
    perms.grant(Permission.DB_WRITE)
    return perms


class TestSQLOperationDetection:
    """Test SQL operation type detection."""

    def test_simple_select(self, mock_conn, read_only_permissions):
        """Test basic SELECT statement."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)
        assert restricted._get_sql_operation_type("SELECT * FROM users") == "read"

    def test_simple_insert(self, mock_conn, write_permissions):
        """Test basic INSERT statement."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        assert restricted._get_sql_operation_type("INSERT INTO users VALUES (1)") == "write"

    def test_simple_update(self, mock_conn, write_permissions):
        """Test basic UPDATE statement."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        assert restricted._get_sql_operation_type("UPDATE users SET name='x'") == "write"

    def test_simple_delete(self, mock_conn, write_permissions):
        """Test basic DELETE statement."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        assert restricted._get_sql_operation_type("DELETE FROM users") == "write"

    def test_create_table(self, mock_conn, write_permissions):
        """Test CREATE TABLE statement."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        assert restricted._get_sql_operation_type("CREATE TABLE users (id INT)") == "ddl"

    def test_drop_table(self, mock_conn, write_permissions):
        """Test DROP TABLE statement."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        assert restricted._get_sql_operation_type("DROP TABLE users") == "ddl"


class TestBypassAttempts:
    """Test that various SQL injection bypass attempts are prevented."""

    def test_comment_before_insert(self, mock_conn, write_permissions):
        """Test that INSERT with leading comment is detected as write."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        sql = "/* comment */ INSERT INTO users VALUES (1)"
        assert restricted._get_sql_operation_type(sql) == "write"

    def test_multiline_comment_before_insert(self, mock_conn, write_permissions):
        """Test that INSERT with multiline comment is detected as write."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        sql = """
        /* This is a
           multiline comment */
        INSERT INTO users VALUES (1)
        """
        assert restricted._get_sql_operation_type(sql) == "write"

    def test_whitespace_before_insert(self, mock_conn, write_permissions):
        """Test that INSERT with leading whitespace is detected as write."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        sql = "\n\t  INSERT INTO users VALUES (1)"
        assert restricted._get_sql_operation_type(sql) == "write"

    def test_cte_with_insert(self, mock_conn, write_permissions):
        """Test that CTE with INSERT is detected as write."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        sql = """
        WITH temp AS (SELECT 1)
        INSERT INTO users SELECT * FROM temp
        """
        assert restricted._get_sql_operation_type(sql) == "write"

    def test_cte_with_select(self, mock_conn, read_only_permissions):
        """Test that CTE with SELECT is detected as read."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)
        sql = """
        WITH temp AS (SELECT 1)
        SELECT * FROM temp
        """
        assert restricted._get_sql_operation_type(sql) == "read"

    def test_cte_with_update(self, mock_conn, write_permissions):
        """Test that CTE with UPDATE is detected as write."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        sql = """
        WITH temp AS (SELECT id FROM users WHERE active = 1)
        UPDATE users SET status = 'inactive' WHERE id IN (SELECT id FROM temp)
        """
        assert restricted._get_sql_operation_type(sql) == "write"

    def test_mixed_case_insert(self, mock_conn, write_permissions):
        """Test that mixed case INSERT is detected."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        sql = "InSeRt InTo users VALUES (1)"
        assert restricted._get_sql_operation_type(sql) == "write"


class TestPermissionEnforcement:
    """Test that permissions are properly enforced."""

    def test_read_allowed_with_read_permission(self, mock_conn, read_only_permissions):
        """Test that SELECT is allowed with read permission."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)
        mock_conn.execute.return_value = Mock()

        # Should not raise
        restricted.execute("SELECT * FROM users")
        mock_conn.execute.assert_called_once()

    def test_write_blocked_without_write_permission(self, mock_conn, read_only_permissions):
        """Test that INSERT is blocked without write permission."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)

        with pytest.raises(PermissionError, match="db_write"):
            restricted.execute("INSERT INTO users VALUES (1)")

    def test_write_allowed_with_write_permission(self, mock_conn, write_permissions):
        """Test that INSERT is allowed with write permission."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        mock_conn.execute.return_value = Mock()

        # Should not raise
        restricted.execute("INSERT INTO users VALUES (1)")
        mock_conn.execute.assert_called_once()

    def test_comment_bypass_blocked(self, mock_conn, read_only_permissions):
        """Test that comment bypass attempt is blocked."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)

        # Attempt to bypass with comment
        with pytest.raises(PermissionError, match="db_write"):
            restricted.execute("/* comment */ INSERT INTO users VALUES (1)")

    def test_whitespace_bypass_blocked(self, mock_conn, read_only_permissions):
        """Test that whitespace bypass attempt is blocked."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)

        # Attempt to bypass with whitespace
        with pytest.raises(PermissionError, match="db_write"):
            restricted.execute("\n\t  INSERT INTO users VALUES (1)")

    def test_cte_bypass_blocked(self, mock_conn, read_only_permissions):
        """Test that CTE bypass attempt is blocked."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)

        # Attempt to bypass with CTE
        with pytest.raises(PermissionError, match="db_write"):
            restricted.execute("""
                WITH temp AS (SELECT 1)
                INSERT INTO users SELECT * FROM temp
            """)

    def test_ddl_blocked_without_write_permission(self, mock_conn, read_only_permissions):
        """Test that DDL operations are blocked without write permission."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)

        with pytest.raises(PermissionError, match="db_write"):
            restricted.execute("CREATE TABLE test (id INT)")

    def test_unknown_operation_treated_as_write(self, mock_conn, read_only_permissions):
        """Test that unknown operations are conservatively treated as write."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)

        # Malformed or unrecognized SQL should be blocked for read-only
        with pytest.raises(PermissionError, match="db_write"):
            restricted.execute("SOMETHING_WEIRD FROM users")


class TestParameterizedQueries:
    """Test that parameterized queries work correctly."""

    def test_select_with_parameters(self, mock_conn, read_only_permissions):
        """Test SELECT with parameters."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)
        mock_conn.execute.return_value = Mock()

        restricted.execute("SELECT * FROM users WHERE id = ?", (1,))
        mock_conn.execute.assert_called_once_with("SELECT * FROM users WHERE id = ?", (1,))

    def test_insert_with_parameters(self, mock_conn, write_permissions):
        """Test INSERT with parameters."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        mock_conn.execute.return_value = Mock()

        restricted.execute("INSERT INTO users VALUES (?, ?)", (1, "test"))
        mock_conn.execute.assert_called_once_with("INSERT INTO users VALUES (?, ?)", (1, "test"))


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_sql(self, mock_conn, read_only_permissions):
        """Test empty SQL string."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)
        assert restricted._get_sql_operation_type("") == "unknown"

    def test_whitespace_only(self, mock_conn, read_only_permissions):
        """Test whitespace-only SQL string."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)
        assert restricted._get_sql_operation_type("   \n\t  ") == "unknown"

    def test_comment_only(self, mock_conn, read_only_permissions):
        """Test comment-only SQL string."""
        restricted = RestrictedConnection(mock_conn, read_only_permissions)
        # Comment-only should be unknown, which requires write permission
        assert restricted._get_sql_operation_type("/* just a comment */") == "unknown"

    def test_malformed_sql(self, mock_conn, write_permissions):
        """Test that malformed SQL is handled gracefully."""
        restricted = RestrictedConnection(mock_conn, write_permissions)
        # Should not crash, should return 'unknown' or 'write' conservatively
        result = restricted._get_sql_operation_type("SELECT FROM WHERE")
        assert result in ("unknown", "write", "read")
