"""Tests for BaseSkill class."""

import pytest
from sqlalchemy import create_engine
from sqlmodel import Field, Session, SQLModel

from glorious_agents.core.context import EventBus
from glorious_agents.core.skill_base import BaseSkill


class TestModel(SQLModel, table=True):
    """Test model for skill tests."""

    __tablename__ = "skill_test_items"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    value: int = Field(default=0)


class TestSkill(BaseSkill[TestModel]):
    """Test skill implementation."""

    def get_model_class(self) -> type[TestModel]:
        return TestModel


@pytest.fixture
def engine():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def event_bus():
    """Create test event bus."""
    return EventBus()


def test_skill_initialization(engine, event_bus):
    """Test basic skill initialization."""
    skill = TestSkill(engine, event_bus)
    assert skill.engine is engine
    assert skill.event_bus is event_bus


def test_lazy_session_creation(engine, event_bus):
    """Test that session is created lazily."""
    skill = TestSkill(engine, event_bus)
    assert skill._session is None

    # Access session
    session = skill.session
    assert session is not None
    assert isinstance(session, Session)

    # Same session on second access
    session2 = skill.session
    assert session2 is session


def test_lazy_repository_creation(engine, event_bus):
    """Test that repository is created lazily."""
    skill = TestSkill(engine, event_bus)
    assert skill._repository is None

    # Access repository
    repo = skill.get_repository()
    assert repo is not None

    # Same repository on second access
    repo2 = skill.get_repository()
    assert repo2 is repo


def test_context_manager_commit(engine, event_bus):
    """Test automatic commit with context manager."""
    entity_id = None
    with TestSkill(engine, event_bus) as skill:
        repo = skill.get_repository()
        entity = TestModel(name="test1", value=42)
        repo.add(entity)
        entity_id = entity.id

    # Verify committed
    session = Session(engine)
    result = session.get(TestModel, entity_id)
    assert result is not None
    assert result.name == "test1"
    session.close()


def test_context_manager_rollback(engine, event_bus):
    """Test automatic rollback on exception."""
    entity_id = None
    try:
        with TestSkill(engine, event_bus) as skill:
            repo = skill.get_repository()
            entity = TestModel(name="test1", value=42)
            entity = repo.add(entity)
            entity_id = entity.id
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify rolled back
    session = Session(engine)
    result = session.get(TestModel, entity_id)
    assert result is None
    session.close()


def test_manual_commit(engine, event_bus):
    """Test manual commit."""
    skill = TestSkill(engine, event_bus)
    repo = skill.get_repository()
    entity = TestModel(name="test1", value=42)
    repo.add(entity)
    skill.commit()

    # Verify committed
    session = Session(engine)
    result = session.get(TestModel, entity.id)
    assert result is not None
    session.close()

    skill.close()


def test_manual_rollback(engine, event_bus):
    """Test manual rollback."""
    skill = TestSkill(engine, event_bus)
    repo = skill.get_repository()
    entity = TestModel(name="test1", value=42)
    entity = repo.add(entity)
    entity_id = entity.id
    skill.rollback()

    # Verify rolled back
    session = Session(engine)
    result = session.get(TestModel, entity_id)
    assert result is None
    session.close()

    skill.close()


def test_publish_event(engine, event_bus):
    """Test event publishing."""
    events_received = []

    def handler(data):
        events_received.append(data)

    event_bus.subscribe("test_event", handler)

    skill = TestSkill(engine, event_bus)
    skill.publish_event("test_event", {"key": "value"})

    assert len(events_received) == 1
    assert events_received[0] == {"key": "value"}

    skill.close()


def test_create_unit_of_work(engine, event_bus):
    """Test creating Unit of Work."""
    skill = TestSkill(engine, event_bus)
    uow = skill.create_unit_of_work()

    assert uow is not None
    assert uow.session is skill.session

    skill.close()


def test_close_cleanup(engine, event_bus):
    """Test that close cleans up resources."""
    skill = TestSkill(engine, event_bus)

    # Create session and repository
    skill.get_repository()

    assert skill._session is not None
    assert skill._repository is not None

    # Close
    skill.close()

    assert skill._session is None
    assert skill._repository is None


def test_multiple_operations(engine, event_bus):
    """Test multiple operations in single skill instance."""
    with TestSkill(engine, event_bus) as skill:
        repo = skill.get_repository()

        # Add entities
        entity1 = TestModel(name="test1", value=1)
        entity2 = TestModel(name="test2", value=2)
        repo.add(entity1)
        repo.add(entity2)

        # Search
        results = repo.search(name="test1")
        assert len(results) == 1
        assert results[0].name == "test1"

    # Verify all committed
    session = Session(engine)
    all_entities = session.query(TestModel).all()
    assert len(all_entities) == 2
    session.close()
