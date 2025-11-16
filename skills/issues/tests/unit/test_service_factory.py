"""Tests for service factory."""

from unittest.mock import MagicMock

from issue_tracker.factories import ServiceFactory


class TestServiceFactory:
    """Test service factory class."""

    def test_create_clock(self):
        """Test clock creation."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        clock = factory.create_clock()
        assert clock is not None
        # Clock should return current time
        now1 = clock.now()
        now2 = clock.now()
        assert now2 >= now1

    def test_create_identifier_service(self):
        """Test identifier service creation."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        id_service = factory.create_identifier_service()
        assert id_service is not None
        # Should generate unique IDs
        id1 = id_service.generate()
        id2 = id_service.generate()
        assert id1 != id2
        assert isinstance(id1, str)
        assert isinstance(id2, str)

    def test_create_unit_of_work(self):
        """Test unit of work creation."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        uow = factory.create_unit_of_work()
        assert uow is not None

    def test_create_issue_service(self):
        """Test issue service creation."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        mock_uow = MagicMock()
        mock_clock = MagicMock()
        mock_id = MagicMock()
        
        service = factory.create_issue_service(
            uow=mock_uow,
            clock=mock_clock,
            id_service=mock_id,
        )
        assert service is not None
        assert service.uow == mock_uow
        assert service.clock == mock_clock
        assert service.id_service == mock_id

    def test_create_issue_service_defaults(self):
        """Test issue service creation with defaults."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        service = factory.create_issue_service()
        assert service is not None

    def test_create_issue_graph_service(self):
        """Test graph service creation."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        mock_uow = MagicMock()
        service = factory.create_issue_graph_service(uow=mock_uow)
        assert service is not None
        assert service._uow == mock_uow

    def test_create_issue_graph_service_defaults(self):
        """Test graph service creation with defaults."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        service = factory.create_issue_graph_service()
        assert service is not None

    def test_create_issue_graph_service_custom_depth(self):
        """Test graph service creation with custom max depth."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        service = factory.create_issue_graph_service(max_depth=20)
        assert service is not None
        assert service._max_depth == 20

    def test_create_issue_stats_service(self):
        """Test stats service creation."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        mock_uow = MagicMock()
        service = factory.create_issue_stats_service(uow=mock_uow)
        assert service is not None
        assert service._uow == mock_uow

    def test_create_issue_stats_service_defaults(self):
        """Test stats service creation with defaults."""
        mock_engine = MagicMock()
        factory = ServiceFactory(mock_engine)
        service = factory.create_issue_stats_service()
        assert service is not None
