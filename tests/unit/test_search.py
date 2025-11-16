"""Tests for search functionality."""

import pytest

from glorious_agents.core.search import SearchResult, search_all_skills


class TestSearchResult:
    def test_create_search_result(self):
        """Test creating a SearchResult."""
        result = SearchResult(
            skill="notes",
            id=123,
            type="note",
            content="Test content",
            metadata={"tags": ["test"]},
            score=0.95,
        )
        assert result.skill == "notes"
        assert result.id == 123
        assert result.type == "note"
        assert result.content == "Test content"
        assert result.metadata == {"tags": ["test"]}
        assert result.score == 0.95

    def test_search_result_default_score(self):
        """Test that default score is 1.0."""
        result = SearchResult(
            skill="notes",
            id="1",
            type="note",
            content="Content",
            metadata={},
        )
        assert result.score == 1.0

    def test_to_dict(self):
        """Test converting SearchResult to dictionary."""
        result = SearchResult(
            skill="notes",
            id=456,
            type="note",
            content="Test",
            metadata={"tag": "value"},
            score=0.8,
        )
        d = result.to_dict()
        assert d == {
            "skill": "notes",
            "id": 456,
            "type": "note",
            "content": "Test",
            "metadata": {"tag": "value"},
            "score": 0.8,
        }


class MockSearchableSkill:
    """Mock skill that implements search."""

    def __init__(self, results):
        self._results = results

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Return mock search results."""
        return self._results[:limit]


class MockFailingSkill:
    """Mock skill that fails search."""

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Raise an exception."""
        raise RuntimeError("Search failed")


class MockContext:
    """Mock context for testing."""

    def __init__(self):
        self.notes = MockSearchableSkill(
            [
                SearchResult(
                    skill="notes",
                    id=1,
                    type="note",
                    content="Note 1",
                    metadata={},
                    score=0.9,
                ),
                SearchResult(
                    skill="notes",
                    id=2,
                    type="note",
                    content="Note 2",
                    metadata={},
                    score=0.7,
                ),
            ]
        )
        self.tasks = MockSearchableSkill(
            [
                SearchResult(
                    skill="tasks",
                    id=10,
                    type="task",
                    content="Task 1",
                    metadata={},
                    score=0.95,
                ),
            ]
        )
        self.failing = MockFailingSkill()
        self.non_searchable = "not a skill"


class TestSearchAllSkills:
    def test_search_all_skills(self):
        """Test searching across multiple skills."""
        ctx = MockContext()
        results = search_all_skills(ctx, "test query")
        
        # Should get results from both skills, sorted by score
        assert len(results) == 3
        assert results[0].skill == "tasks"
        assert results[0].score == 0.95
        assert results[1].skill == "notes"
        assert results[1].score == 0.9
        assert results[2].skill == "notes"
        assert results[2].score == 0.7

    def test_search_with_limit_per_skill(self):
        """Test limiting results per skill."""
        ctx = MockContext()
        results = search_all_skills(ctx, "test", limit_per_skill=1)
        
        # Should get max 1 result per skill
        assert len(results) == 2  # One from notes, one from tasks

    def test_search_with_total_limit(self):
        """Test total result limit."""
        ctx = MockContext()
        results = search_all_skills(ctx, "test", total_limit=2)
        
        # Should get max 2 total results
        assert len(results) == 2

    def test_search_skips_failing_skills(self):
        """Test that failing skills are skipped."""
        ctx = MockContext()
        # Should not raise exception despite failing skill
        results = search_all_skills(ctx, "test")
        
        # Should still get results from working skills
        assert len(results) == 3
        assert all(r.skill != "failing" for r in results)

    def test_search_skips_non_searchable(self):
        """Test that non-searchable attributes are skipped."""
        ctx = MockContext()
        results = search_all_skills(ctx, "test")
        
        # Should only get results from searchable skills
        assert all(hasattr(getattr(ctx, r.skill), "search") for r in results)

    def test_search_empty_context(self):
        """Test searching with empty context."""
        class EmptyContext:
            pass
        
        ctx = EmptyContext()
        results = search_all_skills(ctx, "test")
        
        assert results == []
