# plugins/builtin/example_plugin.py
"""
Example plugin demonstrating the plugin interface.
Provides a simple counter tile type.
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plugins.base import BasePlugin, PluginMetadata
from core.exceptions import PluginError


class CounterPlugin(BasePlugin):
    """
    Example plugin that provides a counter tile.
    """
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            plugin_id="counter_plugin",
            name="Counter Plugin",
            version="1.0.0",
            author="PinPoint Team",
            description="Provides a simple counter tile",
            tile_types=["counter"]
        )
        
    def initialize(self) -> None:
        """Initialize the plugin."""
        # In a real plugin, might set up resources here
        print(f"Counter plugin initialized")
        
    def shutdown(self) -> None:
        """Shutdown the plugin."""
        # In a real plugin, might clean up resources here
        print(f"Counter plugin shutting down")
        
    def create_tile_widget(self, tile_type: str, tile_data: Dict[str, Any]) -> Any:
        """
        Create a tile widget instance.
        
        Note: In a real implementation, this would return a Qt widget.
        For testing, we return a mock widget dictionary.
        """
        if tile_type != "counter":
            raise PluginError(
                plugin_id="counter_plugin",
                message=f"Unsupported tile type: {tile_type}"
            )
            
        # Mock widget for testing
        return {
            "type": "counter_widget",
            "tile_id": tile_data.get("id"),
            "count": tile_data.get("count", 0),
            "step": tile_data.get("step", 1)
        }
        
    def get_tile_config_schema(self, tile_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration schema for counter tile."""
        if tile_type != "counter":
            return None
            
        return {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "default": 0,
                    "description": "Current count value"
                },
                "step": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 1,
                    "description": "Increment step"
                },
                "min_value": {
                    "type": "integer",
                    "default": None,
                    "description": "Minimum allowed value"
                },
                "max_value": {
                    "type": "integer",
                    "default": None,
                    "description": "Maximum allowed value"
                }
            }
        }
        
    def validate_tile_config(self, tile_type: str, config: Dict[str, Any]) -> bool:
        """Validate counter configuration."""
        if tile_type != "counter":
            return False
            
        # Check basic types
        if "count" in config and not isinstance(config["count"], int):
            return False
            
        if "step" in config:
            if not isinstance(config["step"], int) or config["step"] < 1:
                return False
                
        # Check min/max constraints
        min_val = config.get("min_value")
        max_val = config.get("max_value")
        count = config.get("count", 0)
        
        if min_val is not None and count < min_val:
            return False
            
        if max_val is not None and count > max_val:
            return False
            
        return True
        
    def export_tile_data(self, tile_type: str, tile_data: Dict[str, Any]) -> Optional[str]:
        """Export counter data as JSON."""
        if tile_type != "counter":
            return None
            
        export_data = {
            "count": tile_data.get("count", 0),
            "step": tile_data.get("step", 1),
            "min_value": tile_data.get("min_value"),
            "max_value": tile_data.get("max_value")
        }
        
        return json.dumps(export_data, indent=2)
        
    def import_tile_data(self, tile_type: str, data: str) -> Optional[Dict[str, Any]]:
        """Import counter data from JSON."""
        if tile_type != "counter":
            return None
            
        try:
            imported = json.loads(data)
            
            # Validate imported data
            if not self.validate_tile_config(tile_type, imported):
                return None
                
            return imported
            
        except json.JSONDecodeError:
            return None