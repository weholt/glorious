"""Integration tests for skills."""

import pytest

from glorious_agents.core.db import get_connection, init_skill_schema
from glorious_agents.core.loader import load_all_skills
from glorious_agents.core.registry import get_registry
from glorious_agents.core.runtime import get_ctx


@pytest.mark.integration
@pytest.mark.skip(reason="Requires example-skills package to be installed")
def test_notes_skill_integration(temp_agent_folder) -> None:  # type: ignore[no-untyped-def]
    """Test notes skill end-to-end."""
    # Initialize and load skills
    load_all_skills()

    registry = get_registry()
    ctx = get_ctx()

    # Verify notes skill loaded
    assert registry.get_manifest("notes") is not None

    # Test adding a note via callable API
    from skills.notes.skill import add_note

    note_id = add_note("Test note", tags="test")
    assert note_id > 0

    # Verify in database
    cur = ctx.conn.execute("SELECT content, tags FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "Test note"
    assert row[1] == "test"


@pytest.mark.integration
@pytest.mark.skip(reason="Requires example-skills package to be installed")
def test_issues_skill_integration(temp_agent_folder) -> None:  # type: ignore[no-untyped-def]
    """Test issues skill end-to-end."""
    load_all_skills()

    ctx = get_ctx()

    # Test creating an issue
    from skills.issues.skill import create_issue

    issue_id = create_issue("Test issue", "Description here", priority="high")
    assert issue_id > 0

    # Verify in database
    cur = ctx.conn.execute(
        """
        SELECT title, description, status, priority
        FROM issues WHERE id = ?
    """,
        (issue_id,),
    )
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "Test issue"
    assert row[1] == "Description here"
    assert row[2] == "open"
    assert row[3] == "high"


@pytest.mark.integration
@pytest.mark.skip(reason="Requires example-skills package to be installed")
def test_notes_issues_event_integration(temp_agent_folder) -> None:  # type: ignore[no-untyped-def]
    """Test event-driven integration between notes and issues."""
    load_all_skills()

    ctx = get_ctx()

    # Add a note with "todo" tag
    from skills.notes.skill import add_note

    note_id = add_note("Need to implement feature X", tags="todo,feature")

    # Check if issue was auto-created
    cur = ctx.conn.execute(
        """
        SELECT id, title, source_note_id
        FROM issues
        WHERE source_note_id = ?
    """,
        (note_id,),
    )
    row = cur.fetchone()

    # Issue should be created automatically
    assert row is not None
    assert row[2] == note_id
    assert "note" in row[1].lower()
