# core/layout_manager.py
"""
Event-driven layout manager for PinPoint.
Manages layout data and tile arrangements.
"""

import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.constants import (
    EVENT_LAYOUT_CREATED, EVENT_LAYOUT_UPDATED, 
    EVENT_LAYOUT_DELETED, EVENT_LAYOUT_PROJECTED
)
from core.exceptions import LayoutError, ValidationError
from core.events import get_event_bus
from core.logger import get_logger
from data.base_store import BaseStore
from data.json_store import JSONStore


@dataclass
class TileInstance:
    """Represents a tile instance in a layout."""
    instance_id: str
    tile_id: str
    x: int
    y: int
    width: int
    height: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "tile_id": self.tile_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TileInstance':
        """Create from dictionary."""
        return cls(
            instance_id=data["instance_id"],
            tile_id=data["tile_id"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"]
        )


class LayoutManager:
    """
    Manages layouts and tile arrangements.
    Uses events for state changes and storage abstraction.
    """
    
    def __init__(self, store: Optional[BaseStore] = None):
        """
        Initialize layout manager.
        
        Args:
            store: Storage backend. If None, uses default JSONStore.
        """
        self.store = store or JSONStore()
        self.event_bus = get_event_bus()
        self.logger = get_logger("layout_manager")
        
        # Cache for layout data
        self._layouts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._cache_dirty = False
        
        # Load initial data
        self._load_layouts()
        
    def _load_layouts(self) -> None:
        """Load layouts from storage into cache."""
        try:
            data = self.store.load()
            layouts_list = data.get("layouts", [])
            
            # Convert list to dict for efficient lookup
            self._layouts_cache = {}
            for layout in layouts_list:
                if "id" in layout:
                    self._layouts_cache[layout["id"]] = layout
                    
            self.logger.info(f"Loaded {len(self._layouts_cache)} layouts")
            
        except Exception as e:
            self.logger.error("Failed to load layouts", {"error": str(e)})
            self._layouts_cache = {}
            
    def _save_layouts(self) -> None:
        """Save layouts from cache to storage."""
        if not self._cache_dirty:
            return
            
        try:
            # Convert dict back to list for storage
            layouts_list = list(self._layouts_cache.values())
            
            # Get all data and update layouts
            data = self.store.load()
            data["layouts"] = layouts_list
            
            # Save to storage
            self.store.save(data)
            self._cache_dirty = False
            
            self.logger.debug(f"Saved {len(layouts_list)} layouts")
            
        except Exception as e:
            self.logger.error("Failed to save layouts", {"error": str(e)})
            raise LayoutError(message="Failed to save layouts", details={"error": str(e)})
            
    def create_layout(self, name: Optional[str] = None,
                     display_index: int = 0) -> Dict[str, Any]:
        """
        Create a new layout.
        
        Args:
            name: Layout name. Auto-generated if None.
            display_index: Target display index
            
        Returns:
            Created layout data
        """
        # Generate ID and name
        layout_id = f"layout_{uuid.uuid4()}"
        if not name:
            name = f"Layout {len(self._layouts_cache) + 1}"
            
        # Build layout data
        layout_data = {
            "id": layout_id,
            "name": name,
            "tile_instances": [],
            "display_settings": {
                "target_display": display_index,
                "display_info": None  # Will be populated by display manager
            },
            "settings": {
                "theme": "default",
                "overlappable": True,
                "start_with_system": False
            }
        }
        
        # Add to cache
        self._layouts_cache[layout_id] = layout_data
        self._cache_dirty = True
        
        # Save immediately for new layouts
        self._save_layouts()
        
        # Emit event
        self.event_bus.emit(EVENT_LAYOUT_CREATED, {
            "layout_id": layout_id,
            "layout_data": layout_data.copy()
        })
        
        self.logger.info(f"Created layout '{name}' ({layout_id})")
        
        return layout_data.copy()
        
    def get_layout(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a layout by ID.
        
        Args:
            layout_id: ID of the layout
            
        Returns:
            Layout data or None if not found
        """
        layout = self._layouts_cache.get(layout_id)
        return layout.copy() if layout else None
        
    def get_all_layouts(self) -> List[Dict[str, Any]]:
        """
        Get all layouts.
        
        Returns:
            List of all layout data
        """
        return [layout.copy() for layout in self._layouts_cache.values()]
        
    def update_layout(self, layout_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a layout.
        
        Args:
            layout_id: ID of the layout
            updates: Updates to apply
            
        Returns:
            Updated layout data
            
        Raises:
            LayoutError: If layout not found
        """
        if layout_id not in self._layouts_cache:
            raise LayoutError(layout_id=layout_id, message="Layout not found")
            
        # Get current layout
        layout_data = self._layouts_cache[layout_id].copy()
        
        # Apply updates (shallow merge)
        layout_data.update(updates)
        
        # Update cache
        self._layouts_cache[layout_id] = layout_data
        self._cache_dirty = True
        
        # Emit event
        self.event_bus.emit(EVENT_LAYOUT_UPDATED, {
            "layout_id": layout_id,
            "updates": updates,
            "layout_data": layout_data.copy()
        })
        
        self.logger.debug(f"Updated layout {layout_id}")
        
        return layout_data.copy()
        
    def delete_layout(self, layout_id: str) -> None:
        """
        Delete a layout.
        
        Args:
            layout_id: ID of the layout
            
        Raises:
            LayoutError: If layout not found
        """
        if layout_id not in self._layouts_cache:
            raise LayoutError(layout_id=layout_id, message="Layout not found")
            
        # Remove from cache
        del self._layouts_cache[layout_id]
        self._cache_dirty = True
        
        # Save immediately for deletions
        self._save_layouts()
        
        # Emit event
        self.event_bus.emit(EVENT_LAYOUT_DELETED, {
            "layout_id": layout_id
        })
        
        self.logger.info(f"Deleted layout {layout_id}")
        
    def add_tile_to_layout(self, layout_id: str, tile_id: str,
                          x: int, y: int, width: int, height: int) -> TileInstance:
        """
        Add a tile instance to a layout.
        
        Args:
            layout_id: Layout ID
            tile_id: Tile ID to add
            x, y: Position
            width, height: Size
            
        Returns:
            Created tile instance
            
        Raises:
            LayoutError: If layout not found
        """
        if layout_id not in self._layouts_cache:
            raise LayoutError(layout_id=layout_id, message="Layout not found")
            
        # Create instance
        instance = TileInstance(
            instance_id=f"inst_{uuid.uuid4()}",
            tile_id=tile_id,
            x=x,
            y=y,
            width=width,
            height=height
        )
        
        # Add to layout
        layout = self._layouts_cache[layout_id]
        if "tile_instances" not in layout:
            layout["tile_instances"] = []
            
        layout["tile_instances"].append(instance.to_dict())
        self._cache_dirty = True
        
        # Save immediately for structural changes
        self._save_layouts()
        
        self.logger.debug(f"Added tile {tile_id} to layout {layout_id}")
        
        return instance
        
    def remove_tile_from_layout(self, layout_id: str, instance_id: str) -> None:
        """
        Remove a tile instance from a layout.
        
        Args:
            layout_id: Layout ID
            instance_id: Instance ID to remove
            
        Raises:
            LayoutError: If layout or instance not found
        """
        if layout_id not in self._layouts_cache:
            raise LayoutError(layout_id=layout_id, message="Layout not found")
            
        layout = self._layouts_cache[layout_id]
        instances = layout.get("tile_instances", [])
        
        # Find and remove instance
        original_count = len(instances)
        layout["tile_instances"] = [
            inst for inst in instances 
            if inst.get("instance_id") != instance_id
        ]
        
        if len(layout["tile_instances"]) == original_count:
            raise LayoutError(
                layout_id=layout_id,
                message=f"Instance {instance_id} not found in layout"
            )
            
        self._cache_dirty = True
        self._save_layouts()
        
        self.logger.debug(f"Removed instance {instance_id} from layout {layout_id}")
        
    def update_tile_instance(self, layout_id: str, instance_id: str,
                           updates: Dict[str, Any]) -> None:
        """
        Update a tile instance in a layout.
        
        Args:
            layout_id: Layout ID
            instance_id: Instance ID
            updates: Updates to apply (x, y, width, height)
            
        Raises:
            LayoutError: If not found
        """
        if layout_id not in self._layouts_cache:
            raise LayoutError(layout_id=layout_id, message="Layout not found")
            
        layout = self._layouts_cache[layout_id]
        
        # Find instance
        for instance in layout.get("tile_instances", []):
            if instance.get("instance_id") == instance_id:
                instance.update(updates)
                self._cache_dirty = True
                self.logger.debug(f"Updated instance {instance_id}")
                return
                
        raise LayoutError(
            layout_id=layout_id,
            message=f"Instance {instance_id} not found"
        )
        
    def get_layout_instances(self, layout_id: str) -> List[TileInstance]:
        """
        Get all tile instances in a layout.
        
        Args:
            layout_id: Layout ID
            
        Returns:
            List of tile instances
            
        Raises:
            LayoutError: If layout not found
        """
        layout = self.get_layout(layout_id)
        if not layout:
            raise LayoutError(layout_id=layout_id, message="Layout not found")
            
        instances = []
        for inst_data in layout.get("tile_instances", []):
            try:
                instances.append(TileInstance.from_dict(inst_data))
            except (KeyError, TypeError) as e:
                self.logger.warning(f"Invalid instance data: {e}")
                
        return instances
        
    def project_layout(self, layout_id: str, display_index: Optional[int] = None) -> None:
        """
        Project a layout (emit event for UI to handle).
        
        Args:
            layout_id: Layout to project
            display_index: Target display (None = use layout's default)
            
        Raises:
            LayoutError: If layout not found
        """
        layout = self.get_layout(layout_id)
        if not layout:
            raise LayoutError(layout_id=layout_id, message="Layout not found")
            
        # Use specified display or layout's default
        if display_index is None:
            display_index = layout.get("display_settings", {}).get("target_display", 0)
            
        # Emit event
        self.event_bus.emit(EVENT_LAYOUT_PROJECTED, {
            "layout_id": layout_id,
            "display_index": display_index,
            "layout_data": layout
        })
        
        self.logger.info(f"Projected layout {layout_id} to display {display_index}")
        
    def save_pending_changes(self) -> None:
        """Save any pending changes to storage."""
        self._save_layouts()