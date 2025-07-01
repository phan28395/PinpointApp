# tests/test_session4_simple.py
"""
Simple tests for Session 4: Basic Plugin System.
No complex infrastructure - just basic asserts.
"""

import sys
from pathlib import Path
import tempfile
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.base import BasePlugin, PluginMetadata
from plugins.loader import PluginLoader, get_plugin_loader
from core.exceptions import PluginError
from core.tile_registry import get_tile_registry


def test_plugin_metadata():
    """Test plugin metadata creation."""
    metadata = PluginMetadata(
        plugin_id="test_plugin",
        name="Test Plugin",
        version="1.0.0",
        author="Test Author",
        description="A test plugin",
        tile_types=["test_tile"]
    )
    
    assert metadata.plugin_id == "test_plugin"
    assert metadata.tile_types == ["test_tile"]
    assert metadata.requires == []  # Default
    
    print("✓ Plugin metadata test passed")


def test_plugin_loader_init():
    """Test plugin loader initialization."""
    loader = PluginLoader()
    
    # Should have default builtin directory
    assert len(loader.plugin_dirs) >= 1
    assert any("builtin" in str(p) for p in loader.plugin_dirs)
    
    # Can add directories
    with tempfile.TemporaryDirectory() as temp_dir:
        loader.add_plugin_dir(Path(temp_dir))
        assert Path(temp_dir) in loader.plugin_dirs
        
    print("✓ Plugin loader init test passed")


def test_plugin_discovery():
    """Test plugin file discovery."""
    loader = PluginLoader()
    
    # Should find example plugin
    plugins = loader.discover_plugins()
    assert len(plugins) > 0
    assert any("example_plugin" in str(p) for p in plugins)
    
    print("✓ Plugin discovery test passed")


def test_plugin_loading():
    """Test loading a plugin."""
    loader = PluginLoader()
    
    # Find and load example plugin
    plugin_files = loader.discover_plugins()
    example_file = next(p for p in plugin_files if "example_plugin" in str(p))
    
    plugin = loader.load_plugin_from_file(example_file)
    assert plugin is not None
    
    # Check it's registered
    assert "counter_plugin" in loader.plugins
    
    # Check metadata
    metadata = plugin.get_metadata()
    assert metadata.plugin_id == "counter_plugin"
    assert "counter" in metadata.tile_types
    
    print("✓ Plugin loading test passed")


def test_plugin_tile_registration():
    """Test that plugin tile types are registered."""
    # Clear registry first
    registry = get_tile_registry()
    
    # Load plugins
    loader = PluginLoader()
    loader.load_all_plugins()
    
    # Check counter type is registered
    counter_info = registry.get_type_info("counter")
    assert counter_info is not None
    assert counter_info.category == "Plugins"
    
    print("✓ Plugin tile registration test passed")


def test_create_tile_widget():
    """Test creating tile widget through plugin."""
    loader = PluginLoader()
    loader.load_all_plugins()
    
    # Create counter widget
    tile_data = {"id": "test_tile", "count": 5, "step": 2}
    widget = loader.create_tile_widget("counter", tile_data)
    
    assert widget is not None
    assert widget["type"] == "counter_widget"
    assert widget["count"] == 5
    assert widget["step"] == 2
    
    # Try invalid type
    try:
        loader.create_tile_widget("invalid_type", {})
        assert False, "Should raise PluginError"
    except PluginError:
        pass
        
    print("✓ Create tile widget test passed")


def test_plugin_config_schema():
    """Test plugin configuration schema."""
    loader = PluginLoader()
    loader.load_all_plugins()
    
    plugin = loader.get_plugin("counter_plugin")
    schema = plugin.get_tile_config_schema("counter")
    
    assert schema is not None
    assert "properties" in schema
    assert "count" in schema["properties"]
    assert schema["properties"]["count"]["default"] == 0
    
    print("✓ Plugin config schema test passed")


def test_plugin_validation():
    """Test plugin configuration validation."""
    loader = PluginLoader()
    loader.load_all_plugins()
    
    plugin = loader.get_plugin("counter_plugin")
    
    # Valid config
    assert plugin.validate_tile_config("counter", {"count": 10, "step": 1})
    
    # Invalid configs
    assert not plugin.validate_tile_config("counter", {"count": "not a number"})
    assert not plugin.validate_tile_config("counter", {"step": 0})
    assert not plugin.validate_tile_config("counter", {"count": 10, "max_value": 5})
    
    print("✓ Plugin validation test passed")


def test_plugin_export_import():
    """Test plugin data export/import."""
    loader = PluginLoader()
    loader.load_all_plugins()
    
    plugin = loader.get_plugin("counter_plugin")
    
    # Export
    tile_data = {"count": 42, "step": 3, "min_value": 0, "max_value": 100}
    exported = plugin.export_tile_data("counter", tile_data)
    assert exported is not None
    
    # Should be valid JSON
    parsed = json.loads(exported)
    assert parsed["count"] == 42
    
    # Import
    imported = plugin.import_tile_data("counter", exported)
    assert imported is not None
    assert imported["count"] == 42
    assert imported["step"] == 3
    
    print("✓ Plugin export/import test passed")


def test_plugin_unload():
    """Test unloading a plugin."""
    loader = PluginLoader()
    loader.load_all_plugins()
    
    # Verify loaded
    assert "counter_plugin" in loader.plugins
    
    # Unload
    loader.unload_plugin("counter_plugin")
    
    # Verify unloaded
    assert "counter_plugin" not in loader.plugins
    
    # Registry should be updated
    registry = get_tile_registry()
    assert not registry.is_valid_type("counter")
    
    print("✓ Plugin unload test passed")


def test_global_loader():
    """Test global plugin loader singleton."""
    loader1 = get_plugin_loader()
    loader2 = get_plugin_loader()
    
    assert loader1 is loader2
    
    print("✓ Global loader test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 4 tests...")
    test_plugin_metadata()
    test_plugin_loader_init()
    test_plugin_discovery()
    test_plugin_loading()
    test_plugin_tile_registration()
    test_create_tile_widget()
    test_plugin_config_schema()
    test_plugin_validation()
    test_plugin_export_import()
    test_plugin_unload()
    test_global_loader()
    print("\n✅ All Session 4 tests passed!")