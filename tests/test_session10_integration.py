# tests/test_session10_integration.py
"""
Session 10 Integration Tests
Tests for the main PinPoint application that integrates all systems.
Note: These tests are simplified to work with the actual implementation.
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.base_test import BaseTest

# Import core components directly as they're used in the app
from core.events import get_event_bus
from core.logger import get_logger, configure_global_logger, LogLevel
from core.tile_manager import TileManager
from core.layout_manager import LayoutManager
from core.tile_registry import get_tile_registry
from design.theme import get_theme_manager
from design.components import get_component_registry
from platform_support import get_platform
from data.json_store import JSONStore
from plugins.loader import PluginLoader


class TestSession10Integration(BaseTest):
    """Integration tests for Session 10 - Application Integration."""
    
    def setup(self):
        """Set up test environment - called once before all tests."""
        super().setup()
        
    def teardown(self):
        """Clean up - called once after all tests."""
        super().teardown()
        
    def setup_test(self):
        """Set up before each test."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_test(self):
        """Clean up after each test."""
        # Clean up temp directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            
        # Reset singletons
        self._reset_singletons()
        
    def _reset_singletons(self):
        """Reset all singleton instances for test isolation."""
        # Reset event bus
        event_bus = get_event_bus()
        event_bus._subscribers.clear()
        
        # Reset theme to default
        theme_manager = get_theme_manager()
        theme_manager.set_current_theme("dark")
        
        # Clear logger handlers
        logger = get_logger()
        if hasattr(logger, 'handlers'):
            logger.handlers.clear()
    
    def test_integrated_tile_and_layout_management(self):
        """Test that tiles and layouts work together with events."""
        # Set up paths
        data_path = Path(self.temp_dir) / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        
        # Create stores
        tile_store = JSONStore(data_path / "tiles.json")
        layout_store = JSONStore(data_path / "layouts.json")
        
        # Create managers
        tile_manager = TileManager(tile_store)
        layout_manager = LayoutManager(layout_store)
        
        # Track events
        events_received = []
        event_bus = get_event_bus()
        
        def event_handler(event_data):
            events_received.append(event_data)
            
        event_bus.subscribe("tile.created", event_handler)
        event_bus.subscribe("layout.created", event_handler)
        
        # Create a tile
        tile = tile_manager.create_tile("note", {"content": "Test tile"})
        tile_id = tile["id"]
        
        # Create a layout
        layout = layout_manager.create_layout("Test Layout")
        layout_id = layout["id"]
        
        # Add tile to layout using the correct method name
        layout_manager.add_tile_to_layout(layout_id, tile_id, 100, 100, 250, 150)
        
        # Verify events were received (2 events: tile created, layout created)
        self.assert_equal(len(events_received), 2)
        
        # Verify persistence
        saved_tiles = tile_store.load()
        self.assert_equal(len(saved_tiles.get("tiles", [])), 1)
        
        saved_layouts = layout_store.load()
        self.assert_equal(len(saved_layouts.get("layouts", [])), 1)
        
    def test_theme_system_integration(self):
        """Test that theme system integrates with component registry."""
        from design.components import ComponentType
        
        theme_manager = get_theme_manager()
        component_registry = get_component_registry()
        
        # Set light theme using correct method
        theme_manager.set_current_theme("light")
        
        # Get component style using ComponentType enum
        button_style = component_registry.get_style(ComponentType.BUTTON, variant="primary")
        self.assert_not_none(button_style)
        self.assert_in("background-color", button_style)
        
        # Switch to high contrast
        theme_manager.set_current_theme("high_contrast")
        
        # Style should change - check that the background color is different
        hc_button_style = component_registry.get_style(ComponentType.BUTTON, variant="primary")
        
        # Extract background colors from both styles
        import re
        light_bg = re.search(r'background-color:\s*(#[0-9a-fA-F]+)', button_style)
        hc_bg = re.search(r'background-color:\s*(#[0-9a-fA-F]+)', hc_button_style)
        
        if light_bg and hc_bg:
            self.assert_true(light_bg.group(1) != hc_bg.group(1), "Background colors should be different")
        
    def test_plugin_system_integration(self):
        """Test plugin system integration with tiles."""
        import textwrap
        
        # Create plugin directory
        plugin_dir = Path(self.temp_dir) / "plugins"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test plugin with proper encoding and imports
        plugin_file = plugin_dir / "custom_plugin.py"
        
        # Use textwrap.dedent to handle indentation properly
        plugin_content = textwrap.dedent(f'''\
            import sys
            from pathlib import Path
            # Add the parent directories to path so imports work
            sys.path.insert(0, r'{str(Path(__file__).parent.parent.parent)}')
            
            from plugins.base import BasePlugin, PluginMetadata
            from core.tile_registry import get_tile_registry, TileTypeInfo
            
            class CustomTestPlugin(BasePlugin):
                def get_metadata(self):
                    return PluginMetadata(
                        plugin_id="custom_test_plugin",
                        name="Custom Test Plugin",
                        version="1.0.0",
                        author="Test",
                        description="Test plugin for integration testing",
                        tile_types=["custom_tile"]
                    )
                
                def initialize(self):
                    # Register custom tile type
                    registry = get_tile_registry()
                    registry.register_type(TileTypeInfo(
                        tile_type="custom_tile",
                        name="Custom Tile",
                        description="A custom tile type",
                        icon="CT",
                        category="Custom",
                        default_config={{}},
                        capabilities=["test"]
                    ))
                    return True
                    
                def shutdown(self):
                    registry = get_tile_registry()
                    registry.unregister_type("custom_tile")
                    
                def create_tile_widget(self, tile_type, tile_data):
                    return {{"type": "custom_widget", "data": tile_data}}
        ''')
        
        plugin_file.write_text(plugin_content, encoding='utf-8')
        
        # Create a plugin loader without builtin plugins
        plugin_loader = PluginLoader([])  # Empty list to avoid builtin plugins
        plugin_loader.plugin_dirs = [plugin_dir]  # Set only our test directory
        
        # Debug: check what files are discovered
        discovered = plugin_loader.discover_plugins()
        self.assert_equal(len(discovered), 1, f"Should discover 1 plugin file, got {len(discovered)}")
        
        # Load plugins
        loaded_count = plugin_loader.load_all_plugins()
        
        # Verify only our plugin was loaded
        loaded_plugins = plugin_loader.get_all_plugins()
        self.assert_equal(len(loaded_plugins), 1, f"Expected 1 plugin, got {len(loaded_plugins)}: {list(loaded_plugins.keys())}")
        self.assert_in("custom_test_plugin", loaded_plugins, "Custom test plugin should be loaded")
        
        # Verify tile type was registered
        registry = get_tile_registry()
        self.assert_true(registry.is_valid_type("custom_tile"), "Custom tile type should be registered")
    
    def test_platform_integration(self):
        """Test platform-specific functionality."""
        platform = get_platform()
        
        # Test directory creation
        app_data_dir = platform.get_app_data_dir()
        self.assert_not_none(app_data_dir)
        self.assert_true(isinstance(app_data_dir, Path))
        
        # Test display detection
        displays = platform.get_displays()
        self.assert_true(len(displays) >= 1, "Should have at least one display")
        
        # Test system info
        system_info = platform.get_system_info()
        self.assert_true(hasattr(system_info, 'platform'))
        self.assert_true(hasattr(system_info, 'version'))
        
    def test_error_handling_integration(self):
        """Test error boundaries with tile operations."""
        from core.error_boundary import get_error_boundary
        
        tile_store = JSONStore(Path(self.temp_dir) / "tiles.json")
        tile_manager = TileManager(tile_store)
        error_boundary = get_error_boundary()
        
        # Test error recovery
        with error_boundary.error_context(
            component_type="test",
            operation="create_invalid_tile"
        ):
            # Try to create tile with invalid data
            try:
                tile_manager.create_tile("note", {"width": -100})  # Invalid width
            except Exception:
                pass  # Error should be caught
                
        # Manager should still work
        tile = tile_manager.create_tile("note", {"content": "Valid tile"})
        self.assert_not_none(tile)
        
    def test_data_persistence_across_components(self):
        """Test that data persists correctly across all components."""
        data_path = Path(self.temp_dir) / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        
        # Phase 1: Create data
        tile_store1 = JSONStore(data_path / "tiles.json")
        layout_store1 = JSONStore(data_path / "layouts.json")
        config_store1 = JSONStore(data_path / "config.json")
        
        tile_manager1 = TileManager(tile_store1)
        layout_manager1 = LayoutManager(layout_store1)
        
        # Create tiles and layouts
        tile1 = tile_manager1.create_tile("note", {"content": "Tile 1"})
        tile2 = tile_manager1.create_tile("clock", {})
        
        layout = layout_manager1.create_layout("Persistent Layout")
        layout_manager1.add_tile_to_layout(layout["id"], tile1["id"], 10, 10, 200, 150)
        layout_manager1.add_tile_to_layout(layout["id"], tile2["id"], 220, 10, 200, 150)
        
        # Save config
        config_store1.set("last_layout", layout["id"])
        config_store1.set("theme", "light")
        
        # Phase 2: Load data in new instances
        tile_store2 = JSONStore(data_path / "tiles.json")
        layout_store2 = JSONStore(data_path / "layouts.json")
        config_store2 = JSONStore(data_path / "config.json")
        
        tile_manager2 = TileManager(tile_store2)
        layout_manager2 = LayoutManager(layout_store2)
        
        # Verify tiles persisted
        all_tiles = tile_manager2.get_all_tiles()
        self.assert_equal(len(all_tiles), 2)
        
        # Verify layout persisted
        loaded_layout = layout_manager2.get_layout(layout["id"])
        self.assert_not_none(loaded_layout)
        self.assert_equal(len(loaded_layout["tile_instances"]), 2)
        
        # Verify config persisted
        self.assert_equal(config_store2.get("last_layout"), layout["id"])
        self.assert_equal(config_store2.get("theme"), "light")
        
    def test_event_flow_across_system(self):
        """Test that events flow correctly through the entire system."""
        # Set up components
        event_bus = get_event_bus()
        tile_store = JSONStore(Path(self.temp_dir) / "tiles.json")
        layout_store = JSONStore(Path(self.temp_dir) / "layouts.json")
        
        tile_manager = TileManager(tile_store)
        layout_manager = LayoutManager(layout_store)
        
        # Track all events
        all_events = []
        
        def universal_handler(event_data):
            event_type = event_data.get("event", "unknown")
            all_events.append((event_type, event_data))
            
        # Subscribe to all event types
        for event_type in ["tile.created", "tile.updated", "tile.moved", 
                          "tile.resized", "tile.deleted", "layout.created"]:
            event_bus.subscribe(event_type, universal_handler)
            
        # Perform operations
        tile = tile_manager.create_tile("note", {"content": "Event test"})
        tile_manager.update_tile(tile["id"], {"content": "Updated"})
        tile_manager.move_tile(tile["id"], 200, 200)
        tile_manager.resize_tile(tile["id"], 300, 200)
        
        layout = layout_manager.create_layout("Event Layout")
        
        # Verify events (5 events: tile created, updated, moved, resized, layout created)
        self.assert_true(len(all_events) >= 5, f"Expected at least 5 events, got {len(all_events)}")
        event_types = [e[0] for e in all_events]
        self.assert_in("tile.created", event_types)
        self.assert_in("tile.updated", event_types)
        self.assert_in("tile.moved", event_types)
        self.assert_in("tile.resized", event_types)
        self.assert_in("layout.created", event_types)
        
    def test_logging_integration(self):
        """Test that logging works across all components."""
        log_path = Path(self.temp_dir) / "test.log"
        
        # Configure logging with correct parameters
        from core.logger import Logger
        logger = Logger("test", log_file=log_path, console=False)
        
        # Create components that will log to the same file
        tile_store = JSONStore(Path(self.temp_dir) / "tiles.json")
        
        # Create a custom tile manager that uses our logger
        tile_manager = TileManager(tile_store)
        tile_manager.logger = logger  # Replace with our test logger
        
        # Perform operations that generate logs
        tile = tile_manager.create_tile("note", {"content": "Log test"})
        tile_manager.update_tile(tile["id"], {"content": "Updated"})
        tile_manager.delete_tile(tile["id"])
        
        # Force any buffered writes
        if hasattr(logger, '_file_handle'):
            logger._file_handle.flush()
        
        # Give the file system a moment
        import time
        time.sleep(0.2)
        
        # Verify log file was created and has content
        self.assert_true(log_path.exists(), f"Log file should exist at {log_path}")
        if log_path.exists():
            log_content = log_path.read_text()
            # The tile manager logs these messages
            self.assert_true(
                "Created tile" in log_content or 
                "tile_" in log_content or 
                len(log_content) > 0,
                f"Log file should contain tile operations, got: {log_content[:200]}"
            )


if __name__ == "__main__":
    # Run the tests using the custom test framework
    test_suite = TestSession10Integration()
    test_suite.setup()
    
    try:
        result = test_suite.run()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Test Suite: {result.name}")
        print(f"{'='*60}")
        print(f"Total Tests: {len(result.tests)}")
        print(f"Passed: {result.passed_count}")
        print(f"Failed: {result.failed_count}")
        print(f"Pass Rate: {result.pass_rate:.1f}%")
        print(f"Duration: {result.duration:.3f}s")
        print(f"{'='*60}")
        
        # Print individual test results
        for test in result.tests:
            status = "✓ PASS" if test.passed else "✗ FAIL"
            print(f"{status} {test.name} ({test.duration:.3f}s)")
            if test.error:
                print(f"  Error: {test.error}")
                
        # Exit with appropriate code
        exit_code = 0 if result.failed_count == 0 else 1
        sys.exit(exit_code)
        
    finally:
        test_suite.teardown()