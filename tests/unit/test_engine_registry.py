"""Tests for SQLAlchemy engine registry."""

import pytest
from sqlalchemy import Engine

from glorious_agents.core.engine_registry import (
    dispose_all_engines,
    dispose_engine,
    get_active_engines,
    get_engine,
    has_engine,
)


@pytest.fixture(autouse=True)
def _cleanup_engines():
    """Clean up all engines after each test."""
    yield
    dispose_all_engines()


def test_get_engine_creates_new():
    """Test that get_engine creates new engine for new URL."""
    engine = get_engine("sqlite:///:memory:")
    assert isinstance(engine, Engine)


def test_get_engine_caches():
    """Test that get_engine caches engines by URL."""
    db_url = "sqlite:///:memory:"
    engine1 = get_engine(db_url)
    engine2 = get_engine(db_url)
    assert engine1 is engine2


def test_get_engine_different_urls():
    """Test that different URLs get different engines."""
    engine1 = get_engine("sqlite:///test1.db")
    engine2 = get_engine("sqlite:///test2.db")
    assert engine1 is not engine2


def test_dispose_engine():
    """Test disposing single engine."""
    db_url = "sqlite:///:memory:"
    get_engine(db_url)
    assert has_engine(db_url)

    result = dispose_engine(db_url)
    assert result is True
    assert not has_engine(db_url)


def test_dispose_nonexistent_engine():
    """Test disposing non-existent engine."""
    result = dispose_engine("sqlite:///nonexistent.db")
    assert result is False


def test_dispose_all_engines():
    """Test disposing all engines."""
    get_engine("sqlite:///test1.db")
    get_engine("sqlite:///test2.db")
    get_engine("sqlite:///test3.db")

    count = dispose_all_engines()
    assert count == 3
    assert len(get_active_engines()) == 0


def test_get_active_engines():
    """Test getting list of active engines."""
    db_urls = [
        "sqlite:///test1.db",
        "sqlite:///test2.db",
        "sqlite:///test3.db",
    ]

    for url in db_urls:
        get_engine(url)

    active = get_active_engines()
    assert len(active) == 3
    assert set(active) == set(db_urls)


def test_has_engine():
    """Test checking if engine exists."""
    db_url = "sqlite:///:memory:"
    assert not has_engine(db_url)

    get_engine(db_url)
    assert has_engine(db_url)

    dispose_engine(db_url)
    assert not has_engine(db_url)


def test_get_engine_with_options():
    """Test creating engine with custom options."""
    db_url = "sqlite:///:memory:"
    engine = get_engine(
        db_url,
        echo=True,
        connect_args={"timeout": 10.0},
    )
    assert isinstance(engine, Engine)


def test_sqlite_connect_args():
    """Test that SQLite engines get proper connect_args."""
    db_url = "sqlite:///:memory:"
    get_engine(db_url)

    # Test that we can use engine across threads


def test_get_engine_for_agent_db_respects_data_folder(tmp_path, monkeypatch):
    """Test that get_engine_for_agent_db uses configured DATA_FOLDER."""
    from glorious_agents.config import reset_config
    from glorious_agents.core.engine_registry import get_engine_for_agent_db

    # Set custom DATA_FOLDER
    custom_data_folder = tmp_path / "custom_agent_data"
    monkeypatch.setenv("DATA_FOLDER", str(custom_data_folder))

    # Reset config to pick up new environment
    reset_config()

    try:
        # Get engine - should use custom DATA_FOLDER
        engine = get_engine_for_agent_db()

        # Check that engine URL uses the custom path
        expected_path = custom_data_folder / "glorious.db"
        expected_url = f"sqlite:///{expected_path}"

        # Verify the engine was created for correct path
        from glorious_agents.core.engine_registry import get_active_engines

        active_engines = get_active_engines()
        assert len(active_engines) == 1
        assert active_engines[0] == expected_url
    finally:
        reset_config()
    # (check_same_thread should be False)
    from sqlmodel import Field, Session, SQLModel

    class TestEngineModel(SQLModel, table=True):
        __tablename__ = "engine_test"
        id: int | None = Field(default=None, primary_key=True)
        value: str = Field(default="")

    SQLModel.metadata.create_all(engine)

    # Should work without error
    session = Session(engine)
    session.close()


def test_engine_reuse_after_dispose():
    """Test that we can get new engine after disposal."""
    db_url = "sqlite:///:memory:"

    engine1 = get_engine(db_url)
    dispose_engine(db_url)

    engine2 = get_engine(db_url)
    assert engine2 is not engine1
    assert has_engine(db_url)
