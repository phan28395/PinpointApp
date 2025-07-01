# app/application.py
"""
Main PinPoint application using the new architecture.
Integrates all systems built in sessions 1-9.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Core systems
from core.events import get_event_bus
from core.logger import get_logger, configure_global_logger
from core.tile_manager import get_tile_manager
from core.layout_manager import LayoutManager
from core.display_manager import get_display_manager
from core.error_boundary import ErrorBoundary, get_error_boundary

# Data layer
from data.json_store import JSONStore

# Plugin system
from plugins.loader import PluginLoader

# Design system
from design.theme import get_theme_manager
from design.components import get_component_registry

# Platform support
from platform_support import get_platform


class PinPointApplication:
    """Main application class integrating all systems."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the application.
        
        Args:
            config_path: Optional custom config path
        """
        self.platform = get_platform()
        self.event_bus = get_event_bus()
        self.logger = get_logger()
        self.error_boundary = get_error_boundary()
        
        # Setup paths
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = self.platform.get_config_dir() / "pinpoint"
        
        self.data_path = self.platform.get_app_data_dir() / "pinpoint"
        self.log_path = self.platform.get_log_dir() / "pinpoint"
        
        # Ensure directories exist
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize stores
        self.tile_store = JSONStore(self.data_path / "tiles.json")
        self.layout_store = JSONStore(self.data_path / "layouts.json")
        self.config_store = JSONStore(self.config_path / "config.json")
        
        # Initialize managers
        self.tile_manager = get_tile_manager()
        self.layout_manager = LayoutManager(self.layout_store)
        self.display_manager = get_display_manager()
        self.theme_manager = get_theme_manager()
        self.component_registry = get_component_registry()
        
        # Plugin loader
        self.plugin_loader = PluginLoader(
            self.config_path / "plugins",
            self.config_store
        )
        
        # State
        self.current_layout_id = None
        self.is_running = False
        
        # Setup logging
        self._setup_logging()
        
        # Subscribe to events
        self._setup_event_handlers()
        
    def _setup_logging(self):
        """Configure application logging."""
        log_file = self.log_path / "pinpoint.log"
        configure_global_logger(
            name="pinpoint",
            log_file=log_file,
            console=True
        )
        self.logger.info("PinPoint application initialized", data={
            "config_path": str(self.config_path),
            "data_path": str(self.data_path),
            "platform": self.platform.get_platform_name()
        })
        
    def _setup_event_handlers(self):
        """Subscribe to system events."""
        # Tile events
        self.event_bus.subscribe("tile:created", self._on_tile_created)
        self.event_bus.subscribe("tile:updated", self._on_tile_updated)
        self.event_bus.subscribe("tile:deleted", self._on_tile_deleted)
        
        # Layout events
        self.event_bus.subscribe("layout:created", self._on_layout_created)
        self.event_bus.subscribe("layout:switched", self._on_layout_switched)
        
        # Plugin events
        self.event_bus.subscribe("plugin:loaded", self._on_plugin_loaded)
        self.event_bus.subscribe("plugin:error", self._on_plugin_error)
        
        # Error events
        self.event_bus.subscribe("error:caught", self._on_error_caught)
        self.event_bus.subscribe("error:recovered", self._on_error_recovered)
        
    def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load configuration
            self._load_configuration()
            
            # Initialize tile manager storage
            self.tile_manager.set_storage(self.tile_store)
            
            # Load plugins
            self.plugin_loader.load_all_plugins()
            
            # Setup platform integration
            if self.config_store.get("startup.enabled", False):
                self.platform.register_startup("PinPoint", str(Path(__file__).parent.parent / "main.py"))
                
            # Load last layout or create default
            last_layout = self.config_store.get("last_layout_id")
            if last_layout and self.layout_manager.get_layout(last_layout):
                self.switch_layout(last_layout)
            else:
                # Create default layout
                layout = self.layout_manager.create_layout("Default")
                self.switch_layout(layout["id"])
                
            self.is_running = True
            self.logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize application", data={"error": str(e)})
            return False
            
    def _load_configuration(self):
        """Load application configuration."""
        # Set default configuration if not exists
        if not self.config_store.exists():
            default_config = {
                "theme": "dark",
                "startup": {
                    "enabled": False,
                    "minimized": True
                },
                "plugins": {
                    "enabled": True,
                    "directories": []
                },
                "display": {
                    "default_display": 0
                }
            }
            for key, value in default_config.items():
                self.config_store.set(key, value)
                
        # Apply theme
        theme_name = self.config_store.get("theme", "dark")
        self.theme_manager.set_theme(theme_name)
        
    def switch_layout(self, layout_id: str):
        """
        Switch to a different layout.
        
        Args:
            layout_id: ID of layout to switch to
        """
        with self.error_boundary.protect("layout_switch"):
            layout = self.layout_manager.get_layout(layout_id)
            if not layout:
                raise ValueError(f"Layout {layout_id} not found")
                
            self.current_layout_id = layout_id
            self.config_store.set("last_layout_id", layout_id)
            
            self.event_bus.emit("layout:switched", {
                "layout_id": layout_id,
                "layout": layout
            })
            
            self.logger.info("Switched layout", data={"layout_id": layout_id})
            
    def create_tile(self, tile_type: str, config: Dict[str, Any]) -> Optional[str]:
        """
        Create a new tile.
        
        Args:
            tile_type: Type of tile to create
            config: Tile configuration
            
        Returns:
            Tile ID if successful, None otherwise
        """
        try:
            tile = self.tile_manager.create_tile(tile_type, config)
            
            # Add to current layout
            if self.current_layout_id and tile:
                self.layout_manager.add_tile_instance(
                    self.current_layout_id,
                    tile["id"],
                    position=config.get("position", {"x": 100, "y": 100}),
                    size=config.get("size", {"width": 250, "height": 150})
                )
                
            return tile["id"] if tile else None
            
        except Exception as e:
            self.logger.error("Failed to create tile", data={
                "tile_type": tile_type,
                "error": str(e)
            })
            return None
            
    def delete_tile(self, tile_id: str):
        """Delete a tile."""
        with self.error_boundary.protect("tile_delete"):
            # Remove from all layouts
            for layout in self.layout_manager.get_all_layouts():
                self.layout_manager.remove_tile_instance(layout["id"], tile_id)
                
            # Delete tile
            self.tile_manager.delete_tile(tile_id)
            
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for diagnostics."""
        return {
            "platform": self.platform.get_system_info().to_dict(),
            "displays": [d.to_dict() for d in self.display_manager.get_all_displays()],
            "theme": self.theme_manager.get_current_theme_name(),
            "plugins": {
                "loaded": len(self.plugin_loader.loaded_plugins),
                "available": self.plugin_loader.list_available_plugins()
            },
            "tiles": {
                "count": len(self.tile_manager.tiles),
                "types": list(self.tile_manager.registry.tile_types.keys())
            },
            "layouts": {
                "count": len(self.layout_manager.get_all_layouts()),
                "current": self.current_layout_id
            },
            "errors": {
                "total": self.error_boundary.get_error_count(),
                "recent": self.error_boundary.get_recent_errors(5)
            }
        }
        
    def export_configuration(self, path: Path):
        """Export application configuration."""
        config = {
            "version": "2.0.0",
            "platform": self.platform.get_platform_name(),
            "tiles": self.tile_store.load(),
            "layouts": self.layout_store.load(),
            "settings": self.config_store.load(),
            "theme": self.theme_manager.get_current_theme_name()
        }
        
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
            
        self.logger.info("Configuration exported", data={"path": str(path)})
        
    def import_configuration(self, path: Path):
        """Import application configuration."""
        with self.error_boundary.protect("config_import"):
            with open(path, 'r') as f:
                config = json.load(f)
                
            # Validate version
            if config.get("version", "").split('.')[0] != "2":
                raise ValueError("Incompatible configuration version")
                
            # Import data
            if "tiles" in config:
                self.tile_store.save(config["tiles"])
                self.tile_manager.load_tiles()
                
            if "layouts" in config:
                self.layout_store.save(config["layouts"])
                
            if "settings" in config:
                for key, value in config["settings"].items():
                    self.config_store.set(key, value)
                    
            if "theme" in config:
                self.theme_manager.set_theme(config["theme"])
                
            self.logger.info("Configuration imported", data={"path": str(path)})
            
    def shutdown(self):
        """Shutdown the application gracefully."""
        if not self.is_running:
            return
            
        self.logger.info("Shutting down application")
        
        # Save current state
        self.tile_manager.save_tiles()
        
        # Unload plugins
        self.plugin_loader.unload_all_plugins()
        
        # Clear event subscriptions
        self.event_bus.clear()
        
        self.is_running = False
        self.logger.info("Application shutdown complete")
        
    # Event handlers
    def _on_tile_created(self, event_data: Dict[str, Any]):
        """Handle tile creation events."""
        self.logger.debug("Tile created", data=event_data)
        
    def _on_tile_updated(self, event_data: Dict[str, Any]):
        """Handle tile update events."""
        self.logger.debug("Tile updated", data={"tile_id": event_data.get("tile_id")})
        
    def _on_tile_deleted(self, event_data: Dict[str, Any]):
        """Handle tile deletion events."""
        self.logger.debug("Tile deleted", data={"tile_id": event_data.get("tile_id")})
        
    def _on_layout_created(self, event_data: Dict[str, Any]):
        """Handle layout creation events."""
        self.logger.info("Layout created", data={"layout_id": event_data.get("layout", {}).get("id")})
        
    def _on_layout_switched(self, event_data: Dict[str, Any]):
        """Handle layout switch events."""
        self.logger.info("Layout switched", data={"layout_id": event_data.get("layout_id")})
        
    def _on_plugin_loaded(self, event_data: Dict[str, Any]):
        """Handle plugin loaded events."""
        self.logger.info("Plugin loaded", data={"plugin": event_data.get("plugin_id")})
        
    def _on_plugin_error(self, event_data: Dict[str, Any]):
        """Handle plugin error events."""
        self.logger.error("Plugin error", data=event_data)
        
    def _on_error_caught(self, event_data: Dict[str, Any]):
        """Handle caught errors."""
        self.logger.error("Error caught", data=event_data)
        
    def _on_error_recovered(self, event_data: Dict[str, Any]):
        """Handle error recovery."""
        self.logger.info("Error recovered", data=event_data)


# Global instance
_app_instance = None


def get_app() -> PinPointApplication:
    """Get the global application instance."""
    global _app_instance
    if _app_instance is None:
        _app_instance = PinPointApplication()
    return _app_instance