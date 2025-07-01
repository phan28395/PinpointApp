# plugins/loader.py
"""
Plugin loader for PinPoint.
Discovers and loads plugins from specified directories.
"""

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.exceptions import PluginError
from core.logger import get_logger
from core.events import get_event_bus
from core.tile_registry import get_tile_registry, TileTypeInfo
from plugins.base import BasePlugin, PluginMetadata


class PluginLoader:
    """
    Loads and manages plugins.
    """
    
    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        """
        Initialize plugin loader.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or []
        self.plugins: Dict[str, BasePlugin] = {}
        self.logger = get_logger("plugin_loader")
        self.event_bus = get_event_bus()
        self.registry = get_tile_registry()
        
        # Add default plugin directory
        default_dir = Path(__file__).parent / "builtin"
        if default_dir not in self.plugin_dirs:
            self.plugin_dirs.append(default_dir)
            
    def add_plugin_dir(self, path: Path) -> None:
        """
        Add a directory to search for plugins.
        
        Args:
            path: Directory path
        """
        if path not in self.plugin_dirs and path.exists() and path.is_dir():
            self.plugin_dirs.append(path)
            self.logger.info(f"Added plugin directory: {path}")
            
    def discover_plugins(self) -> List[Path]:
        """
        Discover plugin files in all plugin directories.
        
        Returns:
            List of plugin file paths
        """
        plugin_files = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
                
            # Look for Python files
            for file_path in plugin_dir.glob("*.py"):
                # Skip __init__.py and test files
                if file_path.stem.startswith("_") or "test" in file_path.stem:
                    continue
                    
                plugin_files.append(file_path)
                
        self.logger.info(f"Discovered {len(plugin_files)} plugin files")
        return plugin_files
        
    def load_plugin_from_file(self, file_path: Path) -> Optional[BasePlugin]:
        """
        Load a plugin from a Python file.
        
        Args:
            file_path: Path to plugin file
            
        Returns:
            Loaded plugin instance or None
        """
        try:
            # Load the module
            module_name = f"plugin_{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                raise PluginError(message=f"Could not load spec for {file_path}")
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and
                    obj is not BasePlugin):
                    plugin_class = obj
                    break
                    
            if not plugin_class:
                self.logger.warning(f"No plugin class found in {file_path}")
                return None
                
            # Create instance
            plugin = plugin_class()
            metadata = plugin.get_metadata()
            
            # Validate metadata
            if not metadata.plugin_id:
                raise PluginError(message="Plugin must have an ID")
                
            # Check for duplicate
            if metadata.plugin_id in self.plugins:
                raise PluginError(
                    plugin_id=metadata.plugin_id,
                    message="Plugin already loaded"
                )
                
            # Initialize plugin
            plugin.initialize()
            
            # Store plugin
            self.plugins[metadata.plugin_id] = plugin
            
            # Register tile types
            self._register_plugin_tiles(plugin, metadata)
            
            self.logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
            
            # Emit event
            self.event_bus.emit("plugin.loaded", {
                "plugin_id": metadata.plugin_id,
                "metadata": metadata.__dict__
            })
            
            return plugin
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {file_path}", {
                "error": str(e)
            })
            return None
            
    def _register_plugin_tiles(self, plugin: BasePlugin, metadata: PluginMetadata) -> None:
        """Register tile types provided by a plugin."""
        for tile_type in metadata.tile_types:
            # Get default config from plugin
            schema = plugin.get_tile_config_schema(tile_type)
            default_config = {}
            if schema and "properties" in schema:
                for prop, spec in schema["properties"].items():
                    if "default" in spec:
                        default_config[prop] = spec["default"]
                        
            # Register with tile registry
            self.registry.register_type(TileTypeInfo(
                tile_type=tile_type,
                name=f"{metadata.name} - {tile_type}",
                description=f"Provided by {metadata.name}",
                icon="🔌",  # Default plugin icon
                category="Plugins",
                default_config=default_config,
                capabilities=[]
            ))
            
    def load_all_plugins(self) -> int:
        """
        Load all discovered plugins.
        
        Returns:
            Number of successfully loaded plugins
        """
        plugin_files = self.discover_plugins()
        loaded_count = 0
        
        for file_path in plugin_files:
            if self.load_plugin_from_file(file_path):
                loaded_count += 1
                
        return loaded_count
        
    def unload_plugin(self, plugin_id: str) -> None:
        """
        Unload a plugin.
        
        Args:
            plugin_id: ID of plugin to unload
            
        Raises:
            PluginError: If plugin not found
        """
        if plugin_id not in self.plugins:
            raise PluginError(
                plugin_id=plugin_id,
                message="Plugin not found"
            )
            
        plugin = self.plugins[plugin_id]
        metadata = plugin.get_metadata()
        
        # Shutdown plugin
        try:
            plugin.shutdown()
        except Exception as e:
            self.logger.error(f"Error shutting down plugin {plugin_id}", {
                "error": str(e)
            })
            
        # Unregister tile types
        for tile_type in metadata.tile_types:
            self.registry.unregister_type(tile_type)
            
        # Remove plugin
        del self.plugins[plugin_id]
        
        # Emit event
        self.event_bus.emit("plugin.unloaded", {
            "plugin_id": plugin_id
        })
        
        self.logger.info(f"Unloaded plugin: {plugin_id}")
        
    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """
        Get a loaded plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_id)
        
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        Get all loaded plugins.
        
        Returns:
            Dictionary of plugin_id -> plugin
        """
        return self.plugins.copy()
        
    def create_tile_widget(self, tile_type: str, tile_data: Dict[str, any]) -> any:
        """
        Create a tile widget using the appropriate plugin.
        
        Args:
            tile_type: Type of tile
            tile_data: Tile data
            
        Returns:
            Tile widget instance
            
        Raises:
            PluginError: If no plugin supports the tile type
        """
        # Find plugin that supports this tile type
        for plugin in self.plugins.values():
            metadata = plugin.get_metadata()
            if tile_type in metadata.tile_types:
                return plugin.create_tile_widget(tile_type, tile_data)
                
        raise PluginError(
            message=f"No plugin found for tile type: {tile_type}"
        )


# Global loader instance
_global_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get the global plugin loader instance."""
    global _global_loader
    if _global_loader is None:
        _global_loader = PluginLoader()
    return _global_loader