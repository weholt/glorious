"""Tests for skill registry."""

import pytest
from pydantic import ValidationError

from glorious_agents.core.registry import SkillManifest, SkillRegistry, get_registry


class TestSkillManifest:
    def test_create_manifest(self):
        """Test creating a SkillManifest."""
        manifest = SkillManifest(
            name="test",
            version="1.0.0",
            description="Test skill",
            entry_point="test.app:app",
            origin="local",
        )
        assert manifest.name == "test"
        assert manifest.version == "1.0.0"
        assert manifest.description == "Test skill"
        assert manifest.entry_point == "test.app:app"
        assert manifest.origin == "local"

    def test_manifest_defaults(self):
        """Test manifest default values."""
        manifest = SkillManifest(
            name="test",
            version="1.0.0",
            description="Test",
            entry_point="test:app",
            origin="local",
        )
        assert manifest.schema_file is None
        assert manifest.requires == []
        assert manifest.requires_db is True
        assert manifest.internal_doc is None
        assert manifest.external_doc is None
        assert manifest.config_schema is None
        assert manifest.path is None

    def test_manifest_with_requires_list(self):
        """Test manifest with requires as list."""
        manifest = SkillManifest(
            name="test",
            version="1.0.0",
            description="Test",
            entry_point="test:app",
            origin="local",
            requires=["dep1", "dep2"],
        )
        assert manifest.requires == ["dep1", "dep2"]

    def test_manifest_with_requires_dict(self):
        """Test manifest with requires as dict."""
        manifest = SkillManifest(
            name="test",
            version="1.0.0",
            description="Test",
            entry_point="test:app",
            origin="local",
            requires={"dep1": ">=1.0.0", "dep2": "~2.0"},
        )
        assert manifest.requires == {"dep1": ">=1.0.0", "dep2": "~2.0"}

    def test_manifest_validation_name(self):
        """Test manifest name validation."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            SkillManifest(
                name="",  # Empty name should fail
                version="1.0.0",
                description="Test",
                entry_point="test:app",
                origin="local",
            )

    def test_manifest_validation_version(self):
        """Test manifest version validation."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            SkillManifest(
                name="test",
                version="invalid",  # Invalid version
                description="Test",
                entry_point="test:app",
                origin="local",
            )

    def test_manifest_validation_entry_point(self):
        """Test manifest entry_point validation."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            SkillManifest(
                name="test",
                version="1.0.0",
                description="Test",
                entry_point="invalid",  # Missing colon
                origin="local",
            )


class TestSkillRegistry:
    def setup_method(self):
        """Create a fresh registry for each test."""
        self.registry = SkillRegistry()

    def test_add_skill(self):
        """Test adding a skill to the registry."""
        manifest = SkillManifest(
            name="test",
            version="1.0.0",
            description="Test",
            entry_point="test:app",
            origin="local",
        )
        app = object()

        self.registry.add(manifest, app)

        assert self.registry.get_manifest("test") == manifest
        assert self.registry.get_app("test") == app

    def test_get_manifest_not_found(self):
        """Test getting a manifest that doesn't exist."""
        assert self.registry.get_manifest("nonexistent") is None

    def test_get_app_not_found(self):
        """Test getting an app that doesn't exist."""
        assert self.registry.get_app("nonexistent") is None

    def test_list_all(self):
        """Test listing all manifests."""
        manifest1 = SkillManifest(
            name="skill1",
            version="1.0.0",
            description="Test 1",
            entry_point="test1:app",
            origin="local",
        )
        manifest2 = SkillManifest(
            name="skill2",
            version="2.0.0",
            description="Test 2",
            entry_point="test2:app",
            origin="entrypoint",
        )

        self.registry.add(manifest1, object())
        self.registry.add(manifest2, object())

        all_manifests = self.registry.list_all()
        assert len(all_manifests) == 2
        assert manifest1 in all_manifests
        assert manifest2 in all_manifests

    def test_clear(self):
        """Test clearing the registry."""
        manifest = SkillManifest(
            name="test",
            version="1.0.0",
            description="Test",
            entry_point="test:app",
            origin="local",
        )
        self.registry.add(manifest, object())

        self.registry.clear()

        assert self.registry.list_all() == []
        assert self.registry.get_manifest("test") is None
        assert self.registry.get_app("test") is None

    def test_get_registry_singleton(self):
        """Test that get_registry returns a singleton."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2
