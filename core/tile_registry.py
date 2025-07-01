# core/tile_registry.py
"""
Registry for tile types and their metadata.
Tracks available tile types and their capabilities.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.exceptions import PluginError
from core.logger import get_logger


@dataclass
class TileTypeInfo:
    """Information about a tile type."""
    tile_type: str
    name: str
    description: str
    icon: str
    category: str
    default_config: Dict[str, Any]
    capabilities: List[str]
    

class TileRegistry:
    """
    Registry for tile types.
    Manages available tile types and their metadata.
    """
    
    def __init__(self):
        """Initialize tile registry."""
        self._types: Dict[str, TileTypeInfo] = {}
        self.logger = get_logger("tile_registry")
        
        # Register built-in types
        self._register_builtin_types()
        
    def _register_builtin_types(self) -> None:
        """Register built-in tile types."""
        # Note tile type
        self.register_type(TileTypeInfo(
            tile_type="note",
            name="Text Note",
            description="A simple text note",
            icon="📝",
            category="Productivity",
            default_config={
                "content": "",
                "font_size": 14,
                "font_family": "Arial"
            },
            capabilities=["editable", "resizable", "exportable"]
        ))
        
        # Clock tile type
        self.register_type(TileTypeInfo(
            tile_type="clock",
            name="Clock",
            description="Display current time",
            icon="🕐",
            category="Utility",
            default_config={
                "format": "HH:mm:ss",
                "timezone": "local"
            },
            capabilities=["resizable"]
        ))
        
        # Weather tile type
        self.register_type(TileTypeInfo(
            tile_type="weather",
            name="Weather",
            description="Display weather information",
            icon="🌤️",
            category="Information",
            default_config={
                "location": "",
                "units": "metric"
            },
            capabilities=["resizable", "refreshable"]
        ))
        
        # Todo tile type
        self.register_type(TileTypeInfo(
            tile_type="todo",
            name="Todo List",
            description="Manage your tasks",
            icon="✅",
            category="Productivity",
            default_config={
                "tasks": [],
                "show_completed": True
            },
            capabilities=["editable", "resizable", "exportable"]
        ))
        
        self.logger.info(f"Registered {len(self._types)} built-in tile types")
        
    def register_type(self, type_info: TileTypeInfo) -> None:
        """
        Register a tile type.
        
        Args:
            type_info: Information about the tile type
            
        Raises:
            PluginError: If type already registered
        """
        if type_info.tile_type in self._types:
            raise PluginError(
                plugin_id=type_info.tile_type,
                message="Tile type already registered"
            )
            
        self._types[type_info.tile_type] = type_info
        self.logger.debug(f"Registered tile type: {type_info.tile_type}")
        
    def unregister_type(self, tile_type: str) -> None:
        """
        Unregister a tile type.
        
        Args:
            tile_type: Type to unregister
        """
        if tile_type in self._types:
            del self._types[tile_type]
            self.logger.debug(f"Unregistered tile type: {tile_type}")
            
    def get_type_info(self, tile_type: str) -> Optional[TileTypeInfo]:
        """
        Get information about a tile type.
        
        Args:
            tile_type: Type to look up
            
        Returns:
            Type information or None if not found
        """
        return self._types.get(tile_type)
        
    def get_all_types(self) -> List[TileTypeInfo]:
        """
        Get all registered tile types.
        
        Returns:
            List of all tile type information
        """
        return list(self._types.values())
        
    def get_types_by_category(self, category: str) -> List[TileTypeInfo]:
        """
        Get tile types in a specific category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of tile types in the category
        """
        return [
            info for info in self._types.values()
            if info.category == category
        ]
        
    def get_categories(self) -> List[str]:
        """
        Get all unique categories.
        
        Returns:
            List of category names
        """
        categories = set(info.category for info in self._types.values())
        return sorted(list(categories))
        
    def is_valid_type(self, tile_type: str) -> bool:
        """
        Check if a tile type is registered.
        
        Args:
            tile_type: Type to check
            
        Returns:
            True if type is registered
        """
        return tile_type in self._types
        
    def get_default_config(self, tile_type: str) -> Dict[str, Any]:
        """
        Get default configuration for a tile type.
        
        Args:
            tile_type: Type to get config for
            
        Returns:
            Default configuration or empty dict if type not found
        """
        info = self.get_type_info(tile_type)
        return info.default_config.copy() if info else {}
        
    def has_capability(self, tile_type: str, capability: str) -> bool:
        """
        Check if a tile type has a specific capability.
        
        Args:
            tile_type: Type to check
            capability: Capability to look for
            
        Returns:
            True if type has the capability
        """
        info = self.get_type_info(tile_type)
        return capability in info.capabilities if info else False


# Global registry instance
_global_registry: Optional[TileRegistry] = None


def get_tile_registry() -> TileRegistry:
    """Get the global tile registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TileRegistry()
    return _global_registry