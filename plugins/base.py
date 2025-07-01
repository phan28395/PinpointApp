# plugins/base.py
"""
Base plugin interface for PinPoint.
All plugins must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    """Metadata about a plugin."""
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    tile_types: List[str]  # Tile types this plugin provides
    requires: List[str] = None  # Dependencies on other plugins
    
    def __post_init__(self):
        if self.requires is None:
            self.requires = []


class BasePlugin(ABC):
    """
    Abstract base class for all PinPoint plugins.
    Plugins must implement all abstract methods.
    """
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Get plugin metadata.
        
        Returns:
            Plugin metadata
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the plugin.
        Called when plugin is loaded.
        
        Raises:
            PluginError: If initialization fails
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Shutdown the plugin.
        Called when plugin is being unloaded.
        """
        pass
    
    @abstractmethod
    def create_tile_widget(self, tile_type: str, tile_data: Dict[str, Any]) -> Any:
        """
        Create a tile widget instance.
        
        Args:
            tile_type: Type of tile to create
            tile_data: Initial tile data
            
        Returns:
            Tile widget instance (specific type depends on UI framework)
            
        Raises:
            PluginError: If tile type not supported
        """
        pass
    
    def get_tile_config_schema(self, tile_type: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration schema for a tile type.
        
        Args:
            tile_type: Type of tile
            
        Returns:
            JSON Schema for tile configuration or None
        """
        return None
    
    def validate_tile_config(self, tile_type: str, config: Dict[str, Any]) -> bool:
        """
        Validate tile configuration.
        
        Args:
            tile_type: Type of tile
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def get_tile_editor_widget(self, tile_type: str, tile_data: Dict[str, Any]) -> Optional[Any]:
        """
        Get editor widget for a tile type.
        
        Args:
            tile_type: Type of tile
            tile_data: Current tile data
            
        Returns:
            Editor widget or None if no custom editor
        """
        return None
    
    def export_tile_data(self, tile_type: str, tile_data: Dict[str, Any]) -> Optional[str]:
        """
        Export tile data to a string format.
        
        Args:
            tile_type: Type of tile
            tile_data: Tile data to export
            
        Returns:
            Exported data as string or None if not supported
        """
        return None
    
    def import_tile_data(self, tile_type: str, data: str) -> Optional[Dict[str, Any]]:
        """
        Import tile data from a string format.
        
        Args:
            tile_type: Type of tile
            data: Data to import
            
        Returns:
            Imported tile data or None if not supported
        """
        return None