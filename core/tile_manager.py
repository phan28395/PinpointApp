# core/tile_manager.py
"""
Event-driven tile manager for PinPoint.
Manages tile lifecycle using events and storage abstraction.
"""

import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.constants import (
    EVENT_TILE_CREATED, EVENT_TILE_UPDATED, EVENT_TILE_DELETED,
    EVENT_TILE_MOVED, EVENT_TILE_RESIZED,
    DEFAULT_TILE_WIDTH, DEFAULT_TILE_HEIGHT
)
from core.exceptions import TileError, ValidationError
from core.events import get_event_bus
from core.logger import get_logger
from data.base_store import BaseStore
from data.json_store import JSONStore


class TileManager:
    """
    Manages tile data and operations.
    Uses events for all state changes and storage abstraction for persistence.
    """
    
    def __init__(self, store: Optional[BaseStore] = None):
        """
        Initialize tile manager.
        
        Args:
            store: Storage backend. If None, uses default JSONStore.
        """
        self.store = store or JSONStore()
        self.event_bus = get_event_bus()
        self.logger = get_logger("tile_manager")
        
        # Cache for tile data
        self._tiles_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._cache_dirty = False
        
        # Load initial data
        self._load_tiles()
        
    def _load_tiles(self) -> None:
        """Load tiles from storage into cache."""
        try:
            data = self.store.load()
            tiles_list = data.get("tiles", [])
            
            # Convert list to dict for efficient lookup
            self._tiles_cache = {}
            for tile in tiles_list:
                if "id" in tile:
                    self._tiles_cache[tile["id"]] = tile
                    
            self.logger.info(f"Loaded {len(self._tiles_cache)} tiles")
            
        except Exception as e:
            self.logger.error("Failed to load tiles", {"error": str(e)})
            self._tiles_cache = {}
            
    def _save_tiles(self) -> None:
        """Save tiles from cache to storage."""
        if not self._cache_dirty:
            return
            
        try:
            # Convert dict back to list for storage
            tiles_list = list(self._tiles_cache.values())
            
            # Get all data and update tiles
            data = self.store.load()
            data["tiles"] = tiles_list
            
            # Save to storage
            self.store.save(data)
            self._cache_dirty = False
            
            self.logger.debug(f"Saved {len(tiles_list)} tiles")
            
        except Exception as e:
            self.logger.error("Failed to save tiles", {"error": str(e)})
            raise TileError(message="Failed to save tiles", details={"error": str(e)})
            
    def create_tile(self, tile_type: str = "note", 
                   initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new tile.
        
        Args:
            tile_type: Type of tile to create
            initial_data: Optional initial data for the tile
            
        Returns:
            Created tile data
            
        Raises:
            ValidationError: If tile data is invalid
        """
        # Generate new ID
        tile_id = f"tile_{uuid.uuid4()}"
        
        # Build tile data
        tile_data = {
            "id": tile_id,
            "type": tile_type,
            "width": DEFAULT_TILE_WIDTH,
            "height": DEFAULT_TILE_HEIGHT,
            "x": 100,
            "y": 100,
            "content": ""
        }
        
        # Merge with initial data if provided
        if initial_data:
            tile_data.update(initial_data)
            
        # Validate tile data
        self._validate_tile_data(tile_data)
        
        # Add to cache
        self._tiles_cache[tile_id] = tile_data
        self._cache_dirty = True
        
        # Save immediately for new tiles
        self._save_tiles()
        
        # Emit event
        self.event_bus.emit(EVENT_TILE_CREATED, {
            "tile_id": tile_id,
            "tile_data": tile_data.copy()
        })
        
        self.logger.info(f"Created tile {tile_id}", {"type": tile_type})
        
        return tile_data.copy()
        
    def get_tile(self, tile_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tile by ID.
        
        Args:
            tile_id: ID of the tile
            
        Returns:
            Tile data or None if not found
        """
        tile = self._tiles_cache.get(tile_id)
        return tile.copy() if tile else None
        
    def get_all_tiles(self) -> List[Dict[str, Any]]:
        """
        Get all tiles.
        
        Returns:
            List of all tile data
        """
        return [tile.copy() for tile in self._tiles_cache.values()]
        
    def update_tile(self, tile_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a tile.
        
        Args:
            tile_id: ID of the tile to update
            updates: Dictionary of updates to apply
            
        Returns:
            Updated tile data
            
        Raises:
            TileError: If tile not found
            ValidationError: If updates are invalid
        """
        if tile_id not in self._tiles_cache:
            raise TileError(tile_id=tile_id, message="Tile not found")
            
        # Get current tile data
        tile_data = self._tiles_cache[tile_id].copy()
        
        # Apply updates
        tile_data.update(updates)
        
        # Validate updated data
        self._validate_tile_data(tile_data)
        
        # Update cache
        self._tiles_cache[tile_id] = tile_data
        self._cache_dirty = True
        
        # Emit event
        self.event_bus.emit(EVENT_TILE_UPDATED, {
            "tile_id": tile_id,
            "updates": updates,
            "tile_data": tile_data.copy()
        })
        
        self.logger.debug(f"Updated tile {tile_id}", {"updates": updates})
        
        # Debounced save will happen later
        return tile_data.copy()
        
    def move_tile(self, tile_id: str, x: int, y: int) -> None:
        """
        Move a tile to a new position.
        
        Args:
            tile_id: ID of the tile
            x: New X coordinate
            y: New Y coordinate
            
        Raises:
            TileError: If tile not found
        """
        if tile_id not in self._tiles_cache:
            raise TileError(tile_id=tile_id, message="Tile not found")
            
        # Update position
        self._tiles_cache[tile_id]["x"] = x
        self._tiles_cache[tile_id]["y"] = y
        self._cache_dirty = True
        
        # Emit event
        self.event_bus.emit(EVENT_TILE_MOVED, {
            "tile_id": tile_id,
            "x": x,
            "y": y
        })
        
        self.logger.debug(f"Moved tile {tile_id}", {"x": x, "y": y})
        
    def resize_tile(self, tile_id: str, width: int, height: int) -> None:
        """
        Resize a tile.
        
        Args:
            tile_id: ID of the tile
            width: New width
            height: New height
            
        Raises:
            TileError: If tile not found
            ValidationError: If dimensions invalid
        """
        if tile_id not in self._tiles_cache:
            raise TileError(tile_id=tile_id, message="Tile not found")
            
        # Validate dimensions
        from core.constants import MIN_TILE_WIDTH, MAX_TILE_WIDTH, MIN_TILE_HEIGHT, MAX_TILE_HEIGHT
        
        if not (MIN_TILE_WIDTH <= width <= MAX_TILE_WIDTH):
            raise ValidationError(
                field="width",
                message=f"Width must be between {MIN_TILE_WIDTH} and {MAX_TILE_WIDTH}"
            )
            
        if not (MIN_TILE_HEIGHT <= height <= MAX_TILE_HEIGHT):
            raise ValidationError(
                field="height", 
                message=f"Height must be between {MIN_TILE_HEIGHT} and {MAX_TILE_HEIGHT}"
            )
            
        # Update size
        self._tiles_cache[tile_id]["width"] = width
        self._tiles_cache[tile_id]["height"] = height
        self._cache_dirty = True
        
        # Emit event
        self.event_bus.emit(EVENT_TILE_RESIZED, {
            "tile_id": tile_id,
            "width": width,
            "height": height
        })
        
        self.logger.debug(f"Resized tile {tile_id}", {"width": width, "height": height})
        
    def delete_tile(self, tile_id: str) -> None:
        """
        Delete a tile.
        
        Args:
            tile_id: ID of the tile to delete
            
        Raises:
            TileError: If tile not found
        """
        if tile_id not in self._tiles_cache:
            raise TileError(tile_id=tile_id, message="Tile not found")
            
        # Remove from cache
        del self._tiles_cache[tile_id]
        self._cache_dirty = True
        
        # Save immediately for deletions
        self._save_tiles()
        
        # Emit event
        self.event_bus.emit(EVENT_TILE_DELETED, {
            "tile_id": tile_id
        })
        
        self.logger.info(f"Deleted tile {tile_id}")
        
    def save_pending_changes(self) -> None:
        """Save any pending changes to storage."""
        self._save_tiles()
        
    def _validate_tile_data(self, tile_data: Dict[str, Any]) -> None:
        """
        Validate tile data.
        
        Args:
            tile_data: Tile data to validate
            
        Raises:
            ValidationError: If data is invalid
        """
        # Required fields
        required = ["id", "type", "x", "y", "width", "height"]
        for field in required:
            if field not in tile_data:
                raise ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing"
                )
                
        # Validate dimensions
        from core.constants import MIN_TILE_WIDTH, MAX_TILE_WIDTH, MIN_TILE_HEIGHT, MAX_TILE_HEIGHT
        
        width = tile_data.get("width")
        height = tile_data.get("height")
        
        if not isinstance(width, int) or not (MIN_TILE_WIDTH <= width <= MAX_TILE_WIDTH):
            raise ValidationError(
                field="width",
                message=f"Width must be an integer between {MIN_TILE_WIDTH} and {MAX_TILE_WIDTH}"
            )
            
        if not isinstance(height, int) or not (MIN_TILE_HEIGHT <= height <= MAX_TILE_HEIGHT):
            raise ValidationError(
                field="height",
                message=f"Height must be an integer between {MIN_TILE_HEIGHT} and {MAX_TILE_HEIGHT}"
            )