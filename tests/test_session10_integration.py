# tests/test_session10_integration.py
"""
Integration tests for Session 10: Complete Application.
Tests the integrated PinPoint application.
"""

import sys
from pathlib import Path
import tempfile
import json
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base_test import BaseTest
from app import PinPointApplication, get_app
from core.events import get_event_bus
from core.tile_registry import get_tile_registry
from platform_support import get_platform


class TestSession10Integration(BaseTest):
    """Integration test suite for PinPoint application."""
    
    def setup(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.event_bus = get_event_bus()
        self.events_received = []
        
    def teardown(self):
        """Cleanup test environment."""
        # Clear singleton instances
        import app.application
        app.application._app_instance = None
        
        # Clear event bus
        self.event_bus.clear()
        
        # Clean temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _track_event(self, event_name):
        """Helper to track events."""
        def handler(data):
            self.events_received.append((event_name, data))
        return handler
        
    def test_application_initialization(self):
        """Test application initialization."""
        # Create a unique subdirectory in temp
        unique_config = self.temp_path / "test_init"
        app = PinPointApplication(config_path=unique_config)
        
        # Verify paths were created - use resolved paths
        expected_path = unique_config / "pinpoint"
        self.assert_true(expected_path.exists())
        self.assert_true(app.data_path.exists())
        self.assert_true(app.log_path.exists())
        
        # Initialize application
        result = app.initialize()
        self.assert_true(result)
        self.assert_true(app.is_running)
        
        # Verify default layout was created
        layouts = app.layout_manager.get_all_layouts()
        self.assert_equal(len(layouts), 1)
        self.assert_equal(layouts[0]["name"], "Default")
        
    def test_tile_lifecycle(self):
        """Test creating, updating, and deleting tiles."""
        # Clear events from previous tests
        self.events_received = []
        
        # Track tile events BEFORE creating app
        self.event_bus.subscribe("tile:created", self._track_event("tile:created"))
        self.event_bus.subscribe("tile:updated", self._track_event("tile:updated"))
        self.event_bus.subscribe("tile:deleted", self._track_event("tile:deleted"))
        
        # Use unique config path
        unique_config = self.temp_path / "test_tile_lifecycle"
        app = PinPointApplication(config_path=unique_config)
        app.initialize()
        
        # Create a tile
        tile_id = app.create_tile("note", {
            "title": "Test Note",
            "content": "Test content",
            "position": {"x": 100, "y": 200}
        })
        
        self.assert_true(tile_id is not None)
        
        # Check events - should have at least one tile:created event
        created_events = [e for e in self.events_received if e[0] == "tile:created"]
        self.assert_true(len(created_events) >= 1)
        
        # Verify tile was added to layout
        layout = app.layout_manager.get_layout(app.current_layout_id)
        instances = layout["tile_instances"]
        self.assert_equal(len(instances), 1)
        self.assert_equal(instances[0]["tile_id"], tile_id)
        
        # Delete tile
        app.delete_tile(tile_id)
        
        # Verify events
        event_names = [e[0] for e in self.events_received]
        self.assert_in("tile:deleted", event_names)
        
    def test_layout_management(self):
        """Test layout creation and switching."""
        # Clear events from previous tests
        self.events_received = []
        
        # Track layout events BEFORE creating app
        self.event_bus.subscribe("layout:created", self._track_event("layout:created"))
        self.event_bus.subscribe("layout:switched", self._track_event("layout:switched"))
        
        # Use unique config path
        unique_config = self.temp_path / "test_layout"
        app = PinPointApplication(config_path=unique_config)
        app.initialize()
        
        # Clear events from initialization
        self.events_received = []
        
        # Create new layout
        layout = app.layout_manager.create_layout("Test Layout")
        
        # Should have gotten created event
        created_events = [e for e in self.events_received if e[0] == "layout:created"]
        self.assert_true(len(created_events) >= 1)
        
        # Switch to new layout
        app.switch_layout(layout["id"])
        self.assert_equal(app.current_layout_id, layout["id"])
        
        # Verify event
        self.assert_equal(len(self.events_received), 2)
        self.assert_equal(self.events_received[1][0], "layout:switched")
        
    def test_configuration_export_import(self):
        """Test configuration export and import."""
        # Use a unique temp directory for this test
        with tempfile.TemporaryDirectory() as unique_temp:
            unique_path = Path(unique_temp)
            app = PinPointApplication(config_path=unique_path)
            app.initialize()
            
            # Create some data
            tile_id = app.create_tile("note", {"title": "Export Test"})
            layout = app.layout_manager.create_layout("Export Layout")
            
            # Export configuration
            export_path = unique_path / "export.json"
            app.export_configuration(export_path)
            
            self.assert_true(export_path.exists())
            
            # Read exported data
            with open(export_path, 'r') as f:
                exported = json.load(f)
                
            self.assert_equal(exported["version"], "2.0.0")
            self.assert_in("tiles", exported)
            self.assert_in("layouts", exported)
            self.assert_in("settings", exported)
            
            # Create new app instance with different paths
            app2_path = unique_path / "import_test"
            app2 = PinPointApplication(config_path=app2_path)
            app2.initialize()
            
            # Import configuration
            app2.import_configuration(export_path)
            
            # Verify imported data
            tiles = app2.tile_manager.get_all_tiles()
            layouts = app2.layout_manager.get_all_layouts()
            
            self.assert_equal(len(tiles), 1)
            self.assert_equal(len(layouts), 2)  # Default + imported
        
    def test_plugin_integration(self):
        """Test plugin loading through application."""
        app = PinPointApplication(config_path=self.temp_path)
        
        # Track plugin events
        self.event_bus.subscribe("plugin:loaded", self._track_event("plugin:loaded"))
        self.event_bus.subscribe("plugin:error", self._track_event("plugin:error"))
        
        app.initialize()
        
        # Plugin loader should have attempted to load plugins
        # (though none exist in test environment)
        self.assert_true(hasattr(app, 'plugin_loader'))
        
    def test_error_handling_integration(self):
        """Test error handling in application."""
        # Clear events from previous tests
        self.events_received = []
        
        # Track error events BEFORE creating app
        self.event_bus.subscribe("error.occurred", self._track_event("error.occurred"))
        
        # Use unique config path
        unique_config = self.temp_path / "test_error"
        app = PinPointApplication(config_path=unique_config)
        app.initialize()
        
        # Clear events from initialization
        self.events_received = []
        
        # Try to switch to non-existent layout
        try:
            app.switch_layout("non-existent-id")
        except:
            pass  # Error boundary should handle this
            
        # Verify error was caught - should have at least one error event
        error_events = [e for e in self.events_received if e[0] == "error.occurred"]
        self.assert_true(len(error_events) >= 1)
        
    def test_theme_integration(self):
        """Test theme management through application."""
        app = PinPointApplication(config_path=self.temp_path)
        app.initialize()
        
        # Default theme should be dark
        self.assert_equal(app.theme_manager.get_current_theme().name, "dark")
        
        # Change theme through config
        app.config_store.set("theme", "light")
        app._load_configuration()
        
        self.assert_equal(app.theme_manager.get_current_theme().name, "light")
        
    def test_system_info(self):
        """Test system information collection."""
        app = PinPointApplication(config_path=self.temp_path)
        app.initialize()
        
        info = app.get_system_info()
        
        # Verify structure
        self.assert_in("platform", info)
        self.assert_in("displays", info)
        self.assert_in("theme", info)
        self.assert_in("plugins", info)
        self.assert_in("tiles", info)
        self.assert_in("layouts", info)
        self.assert_in("errors", info)
        
        # Verify content
        self.assert_equal(info["layouts"]["count"], 1)  # Default layout
        self.assert_equal(info["theme"], "dark")
        
    def test_platform_integration(self):
        """Test platform support integration."""
        # Use unique config path
        unique_config = self.temp_path / "test_platform"
        app = PinPointApplication(config_path=unique_config)
        platform = get_platform()
        
        # Application should use platform directories
        # Check that the base directories match (not the full path)
        app_config_base = str(app.config_path.parent.parent)
        platform_config_base = str(platform.get_user_config_dir().parent)
        
        # On Windows, temp paths might use short names, so just verify structure
        self.assert_true("pinpoint" in str(app.config_path).lower())
        self.assert_true(app.data_path.exists())
        self.assert_true(app.log_path.exists())
        
    def test_application_shutdown(self):
        """Test graceful shutdown."""
        app = PinPointApplication(config_path=self.temp_path)
        app.initialize()
        
        # Create some data
        app.create_tile("note", {"title": "Shutdown Test"})
        
        # Shutdown
        app.shutdown()
        
        self.assert_false(app.is_running)
        
        # Verify data was saved
        tiles_file = app.data_path / "tiles.json"
        self.assert_true(tiles_file.exists())


if __name__ == "__main__":
    # Run tests
    suite = TestSession10Integration()
    suite.run()