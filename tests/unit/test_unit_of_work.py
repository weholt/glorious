"""Tests for Unit of Work pattern."""

import pytest
from sqlalchemy import create_engine
from sqlmodel import Field, Session, SQLModel

from glorious_agents.core.unit_of_work import UnitOfWork


class TestModel(SQLModel, table=True):
    """Test model for UoW tests."""

    __tablename__ = "uow_test_items"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    value: int = Field(default=0)


@pytest.fixture
def engine():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create test session."""
    return Session(engine)


def test_commit_on_success(engine):
    """Test automatic commit on successful context exit."""
    session = Session(engine)
    uow = UnitOfWork(session)

    entity_id = None
    with uow:
        repo = uow.get_repository("test", TestModel)
        entity = TestModel(name="test1", value=42)
        repo.add(entity)
        entity_id = entity.id

    # Verify entity was committed
    new_session = Session(engine)
    result = new_session.get(TestModel, entity_id)
    assert result is not None
    assert result.name == "test1"
    new_session.close()


def test_rollback_on_exception(engine):
    """Test automatic rollback on exception."""
    session = Session(engine)
    uow = UnitOfWork(session)

    entity_id = None
    try:
        with uow:
            repo = uow.get_repository("test", TestModel)
            entity = TestModel(name="test1", value=42)
            entity = repo.add(entity)
            entity_id = entity.id
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify entity was rolled back
    new_session = Session(engine)
    result = new_session.get(TestModel, entity_id)
    assert result is None
    new_session.close()


def test_multiple_repositories(engine):
    """Test using multiple repositories in same UoW."""

    class OtherModel(SQLModel, table=True):
        __tablename__ = "other_items"
        id: int | None = Field(default=None, primary_key=True)
        data: str

    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    uow = UnitOfWork(session)

    entity1_id = None
    entity2_id = None
    with uow:
        repo1 = uow.get_repository("test", TestModel)
        repo2 = uow.get_repository("other", OtherModel)

        entity1 = TestModel(name="test1", value=42)
        entity2 = OtherModel(data="data1")

        repo1.add(entity1)
        repo2.add(entity2)
        entity1_id = entity1.id
        entity2_id = entity2.id

    # Verify both committed
    new_session = Session(engine)
    result1 = new_session.get(TestModel, entity1_id)
    result2 = new_session.get(OtherModel, entity2_id)
    assert result1 is not None
    assert result2 is not None
    new_session.close()


def test_repository_caching(session):
    """Test that repositories are cached by name."""
    uow = UnitOfWork(session)

    repo1 = uow.get_repository("test", TestModel)
    repo2 = uow.get_repository("test", TestModel)

    assert repo1 is repo2


def test_manual_commit(engine):
    """Test manual commit without context manager."""
    session = Session(engine)
    uow = UnitOfWork(session)

    repo = uow.get_repository("test", TestModel)
    entity = TestModel(name="test1", value=42)
    repo.add(entity)
    entity_id = entity.id
    uow.commit()
    uow.close()

    # Verify committed
    new_session = Session(engine)
    result = new_session.get(TestModel, entity_id)
    assert result is not None
    new_session.close()


def test_manual_rollback(engine):
    """Test manual rollback."""
    session = Session(engine)
    uow = UnitOfWork(session)

    repo = uow.get_repository("test", TestModel)
    entity = TestModel(name="test1", value=42)
    entity = repo.add(entity)
    entity_id = entity.id
    uow.rollback()
    uow.close()

    # Verify rolled back
    new_session = Session(engine)
    result = new_session.get(TestModel, entity_id)
    assert result is None
    new_session.close()


def test_flush(engine):
    """Test flush without commit."""
    session = Session(engine)
    uow = UnitOfWork(session)

    repo = uow.get_repository("test", TestModel)
    entity = TestModel(name="test1", value=42)
    repo.add(entity)
    uow.flush()

    # ID should be available after flush
    assert entity.id is not None

    # But not committed yet
    uow.rollback()
    uow.close()

    new_session = Session(engine)
    result = new_session.get(TestModel, entity.id)
    assert result is None
    new_session.close()


def test_refresh(engine):
    """Test refreshing entity."""
    session = Session(engine)
    uow = UnitOfWork(session)

    repo = uow.get_repository("test", TestModel)
    entity = TestModel(name="test1", value=42)
    repo.add(entity)
    uow.commit()

    # Modify entity outside UoW
    new_session = Session(engine)
    db_entity = new_session.get(TestModel, entity.id)
    db_entity.value = 100
    new_session.commit()
    new_session.close()

    # Refresh should get new value
    uow.refresh(entity)
    assert entity.value == 100

    uow.close()


def test_atomic_transaction(engine):
    """Test that all operations are atomic."""
    session = Session(engine)

    # Add first entity successfully
    entity1_id = None
    with UnitOfWork(session) as uow:
        repo = uow.get_repository("test", TestModel)
        entity1 = TestModel(name="test1", value=1)
        repo.add(entity1)
        entity1_id = entity1.id

    # Try to add two more, but fail on second
    entity2_id = None
    entity3_id = None
    try:
        with UnitOfWork(Session(engine)) as uow:
            repo = uow.get_repository("test", TestModel)
            entity2 = TestModel(name="test2", value=2)
            entity2 = repo.add(entity2)
            entity2_id = entity2.id

            entity3 = TestModel(name="test3", value=3)
            entity3 = repo.add(entity3)
            entity3_id = entity3.id

            raise ValueError("Simulated error")
    except ValueError:
        pass

    # Verify only first entity exists
    new_session = Session(engine)
    assert new_session.get(TestModel, entity1_id) is not None
    assert new_session.get(TestModel, entity2_id) is None
    assert new_session.get(TestModel, entity3_id) is None
    new_session.close()
