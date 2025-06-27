# pinpoint/plugin_registry.py

import importlib
import inspect
import json
from pathlib import Path
from typing import Dict, Type, Any, List, Optional
from PySide6.QtCore import QObject, Signal
from .base_tile import BaseTile


class TileCapabilities:
    """Defines what a tile type can do."""
    CAN_EDIT = "can_edit"
    CAN_REFRESH = "can_refresh"
    CAN_INTEGRATE = "can_integrate"
    CAN_EXPORT = "can_export"
    CAN_SCRIPT = "can_script"
    HAS_SETTINGS = "has_settings"
    SUPPORTS_THEMES = "supports_themes"


class TileMetadata:
    """Metadata about a tile type."""
    def __init__(self, 
                 tile_id: str,
                 name: str,
                 description: str,
                 author: str,
                 version: str,
                 icon: Optional[str] = None,
                 category: str = "General",
                 capabilities: List[str] = None,
                 config_schema: Dict[str, Any] = None):
        self.tile_id = tile_id
        self.name = name
        self.description = description
        self.author = author
        self.version = version
        self.icon = icon
        self.category = category
        self.capabilities = capabilities or []
        self.config_schema = config_schema or {}


class TilePlugin:
    """Base class for tile plugins."""
    
    @classmethod
    def get_metadata(cls) -> TileMetadata:
        """Return metadata about this tile type."""
        raise NotImplementedError("Plugins must implement get_metadata()")
    
    @classmethod
    def get_tile_class(cls) -> Type[BaseTile]:
        """Return the tile widget class."""
        raise NotImplementedError("Plugins must implement get_tile_class()")
    
    @classmethod
    def get_editor_class(cls):
        """Return the editor widget class, if any."""
        return None
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Return default configuration for new tiles of this type."""
        return {
            "width": 250,
            "height": 150,
            "opacity": 1.0,
            "theme": "default"
        }
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """Validate a configuration against the schema."""
        # Basic validation - can be extended with jsonschema
        schema = cls.get_metadata().config_schema
        if not schema:
            return True
            
        for key, spec in schema.items():
            if spec.get("required", False) and key not in config:
                return False
                
            if key in config:
                value = config[key]
                expected_type = spec.get("type")
                
                # Basic type checking
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                    
        return True


class PluginRegistry(QObject):
    """Central registry for all tile plugins."""
    
    plugin_loaded = Signal(str)  # tile_id
    plugin_error = Signal(str, str)  # tile_id, error_message
    
    def __init__(self):
        super().__init__()
        self._plugins: Dict[str, TilePlugin] = {}
        self._metadata: Dict[str, TileMetadata] = {}
        self._builtin_plugins: List[str] = ["note", "clock", "weather", "todo"]
        
    def initialize(self):
        """Initialize the registry and load all plugins."""
        # Load built-in plugins
        self._load_builtin_plugins()
        
        # Load user plugins
        self._load_user_plugins()
        
    def _load_builtin_plugins(self):
        """Load plugins that ship with the application."""
        for plugin_name in self._builtin_plugins:
            try:
                module_name = f"pinpoint.plugins.{plugin_name}_plugin"
                self._load_plugin_module(module_name, builtin=True)
            except Exception as e:
                print(f"Failed to load builtin plugin {plugin_name}: {e}")
                self.plugin_error.emit(plugin_name, str(e))
                
    def _load_user_plugins(self):
        """Load user-created plugins from the plugins directory."""
        user_plugin_dir = Path.home() / ".pinpoint" / "plugins"
        user_plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Add user plugin directory to Python path
        import sys
        if str(user_plugin_dir) not in sys.path:
            sys.path.insert(0, str(user_plugin_dir))
        
        # Load each .py file in the plugins directory
        for plugin_file in user_plugin_dir.glob("*.py"):
            if plugin_file.stem.startswith("_"):
                continue
                
            try:
                module_name = plugin_file.stem
                self._load_plugin_module(module_name, builtin=False)
            except Exception as e:
                print(f"Failed to load user plugin {plugin_file}: {e}")
                self.plugin_error.emit(plugin_file.stem, str(e))
                
    def _load_plugin_module(self, module_name: str, builtin: bool = False):
        """Load a single plugin module."""
        module = importlib.import_module(module_name)
        
        # Find all TilePlugin subclasses in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, TilePlugin) and 
                obj is not TilePlugin):
                
                try:
                    # Get metadata
                    metadata = obj.get_metadata()
                    
                    # Validate the plugin
                    tile_class = obj.get_tile_class()
                    if not issubclass(tile_class, BaseTile):
                        raise ValueError(f"Tile class must inherit from BaseTile")
                    
                    # Register the plugin
                    self._plugins[metadata.tile_id] = obj
                    self._metadata[metadata.tile_id] = metadata
                    
                    print(f"Loaded plugin: {metadata.name} v{metadata.version}")
                    self.plugin_loaded.emit(metadata.tile_id)
                    
                except Exception as e:
                    print(f"Failed to register plugin {name}: {e}")
                    self.plugin_error.emit(name, str(e))
                    
    def get_plugin(self, tile_id: str) -> Optional[TilePlugin]:
        """Get a plugin by its ID."""
        return self._plugins.get(tile_id)
        
    def get_metadata(self, tile_id: str) -> Optional[TileMetadata]:
        """Get metadata for a plugin."""
        return self._metadata.get(tile_id)
        
    def get_all_metadata(self) -> Dict[str, TileMetadata]:
        """Get metadata for all registered plugins."""
        return self._metadata.copy()
        
    def get_plugins_by_category(self, category: str) -> List[TileMetadata]:
        """Get all plugins in a specific category."""
        return [
            meta for meta in self._metadata.values() 
            if meta.category == category
        ]
        
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        categories = set()
        for meta in self._metadata.values():
            categories.add(meta.category)
        return sorted(list(categories))
        
    def create_tile(self, tile_id: str, instance_data: dict) -> Optional[BaseTile]:
        """Create a tile instance from a plugin."""
        plugin = self.get_plugin(tile_id)
        if not plugin:
            print(f"Plugin not found: {tile_id}")
            return None
            
        try:
            tile_class = plugin.get_tile_class()
            
            # Merge default config with instance data
            default_config = plugin.get_default_config()
            tile_data = {**default_config, **instance_data}
            
            # Validate configuration
            if not plugin.validate_config(tile_data):
                print(f"Invalid configuration for tile {tile_id}")
                return None
                
            # Create the tile
            return tile_class(tile_data)
            
        except Exception as e:
            print(f"Failed to create tile {tile_id}: {e}")
            self.plugin_error.emit(tile_id, str(e))
            return None
            
    def create_editor(self, tile_id: str, tile_data: dict, manager):
        """Create an editor widget for a tile type."""
        plugin = self.get_plugin(tile_id)
        if not plugin:
            return None
            
        editor_class = plugin.get_editor_class()
        if not editor_class:
            return None
            
        try:
            return editor_class(tile_data, manager)
        except Exception as e:
            print(f"Failed to create editor for {tile_id}: {e}")
            return None
            
    def export_plugin_info(self) -> Dict[str, Any]:
        """Export information about all loaded plugins."""
        info = {}
        for tile_id, metadata in self._metadata.items():
            info[tile_id] = {
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "author": metadata.author,
                "category": metadata.category,
                "capabilities": metadata.capabilities,
                "has_editor": self._plugins[tile_id].get_editor_class() is not None
            }
        return info


# Global registry instance
_registry = None

def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.initialize()
    return _registry