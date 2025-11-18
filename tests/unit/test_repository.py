"""Tests for BaseRepository pattern."""

import pytest
from sqlalchemy import create_engine
from sqlmodel import Field, Session, SQLModel

from glorious_agents.core.repository import BaseRepository


class TestModel(SQLModel, table=True):
    """Test model for repository tests."""

    __tablename__ = "test_items"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    value: int = Field(default=0)
    active: bool = Field(default=True)


@pytest.fixture
def engine():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    """Create test session."""
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def repository(session):
    """Create test repository."""
    return BaseRepository(session, TestModel)


def test_add_entity(repository, session):
    """Test adding entity to database."""
    entity = TestModel(name="test1", value=42)
    result = repository.add(entity)

    assert result.id is not None
    assert result.name == "test1"
    assert result.value == 42

    # Verify in database
    session.commit()
    db_entity = session.get(TestModel, result.id)
    assert db_entity is not None
    assert db_entity.name == "test1"


def test_get_entity(repository, session):
    """Test getting entity by ID."""
    entity = TestModel(name="test1", value=42)
    session.add(entity)
    session.commit()

    result = repository.get(entity.id)
    assert result is not None
    assert result.name == "test1"
    assert result.value == 42


def test_get_nonexistent(repository):
    """Test getting non-existent entity."""
    result = repository.get(999)
    assert result is None


def test_get_all(repository, session):
    """Test getting all entities."""
    entities = [TestModel(name=f"test{i}", value=i) for i in range(5)]
    for entity in entities:
        session.add(entity)
    session.commit()

    results = repository.get_all()
    assert len(results) == 5
    assert all(isinstance(r, TestModel) for r in results)


def test_get_all_with_pagination(repository, session):
    """Test pagination."""
    entities = [TestModel(name=f"test{i}", value=i) for i in range(10)]
    for entity in entities:
        session.add(entity)
    session.commit()

    # Get first page
    page1 = repository.get_all(limit=3, offset=0)
    assert len(page1) == 3

    # Get second page
    page2 = repository.get_all(limit=3, offset=3)
    assert len(page2) == 3

    # Verify no overlap
    page1_ids = {e.id for e in page1}
    page2_ids = {e.id for e in page2}
    assert len(page1_ids & page2_ids) == 0


def test_update_entity(repository, session):
    """Test updating entity."""
    entity = TestModel(name="test1", value=42)
    session.add(entity)
    session.commit()

    # Update
    entity.name = "updated"
    entity.value = 100
    result = repository.update(entity)

    assert result.name == "updated"
    assert result.value == 100

    # Verify in database
    session.commit()
    db_entity = session.get(TestModel, entity.id)
    assert db_entity.name == "updated"
    assert db_entity.value == 100


def test_delete_entity(repository, session):
    """Test deleting entity."""
    entity = TestModel(name="test1", value=42)
    session.add(entity)
    session.commit()
    entity_id = entity.id

    # Delete
    result = repository.delete(entity_id)
    assert result is True

    # Verify deleted
    session.commit()
    db_entity = session.get(TestModel, entity_id)
    assert db_entity is None


def test_delete_nonexistent(repository):
    """Test deleting non-existent entity."""
    result = repository.delete(999)
    assert result is False


def test_search_by_filters(repository, session):
    """Test searching with filters."""
    entities = [
        TestModel(name="test1", value=10, active=True),
        TestModel(name="test2", value=20, active=True),
        TestModel(name="test3", value=30, active=False),
    ]
    for entity in entities:
        session.add(entity)
    session.commit()

    # Search by single field
    results = repository.search(active=True)
    assert len(results) == 2

    # Search by multiple fields
    results = repository.search(active=True, value=10)
    assert len(results) == 1
    assert results[0].name == "test1"


def test_count_entities(repository, session):
    """Test counting entities."""
    entities = [TestModel(name=f"test{i}", value=i, active=(i % 2 == 0)) for i in range(10)]
    for entity in entities:
        session.add(entity)
    session.commit()

    # Count all
    total = repository.count()
    assert total == 10

    # Count with filter
    active_count = repository.count(active=True)
    assert active_count == 5


def test_exists(repository, session):
    """Test checking if entity exists."""
    entity = TestModel(name="test1", value=42)
    session.add(entity)
    session.commit()

    assert repository.exists(entity.id) is True
    assert repository.exists(999) is False
