# core/tile_manager_safe.py
"""
Updated tile manager with error handling.
This shows the pattern for adding error boundaries to existing code.
"""

import uuid
from typing import Dict, List, Optional, Any
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
from core.error_boundary import get_error_boundary, RecoveryStrategy, ErrorContext
from data.base_store import BaseStore
from data.json_store import JSONStore


class SafeTileManager:
    """
    Tile manager with error handling.
    Demonstrates how to add error boundaries to existing functionality.
    """
    
    def __init__(self, store: Optional[BaseStore] = None):
        """Initialize tile manager with error handling."""
        self.store = store or JSONStore()
        self.event_bus = get_event_bus()
        self.logger = get_logger("safe_tile_manager")
        self.error_boundary = get_error_boundary()
        
        # Cache for tile data
        self._tiles_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._cache_dirty = False
        
        # Failed operations tracking
        self._failed_tiles: Dict[str, int] = {}  # tile_id -> failure count
        self._max_failures = 3
        
        # Load initial data with error handling
        self._load_tiles_safe()
        
    def _load_tiles_safe(self) -> None:
        """Load tiles with error handling."""
        with self.error_boundary.error_context(
            component_type="tile_manager",
            operation="load_tiles",
            recovery=RecoveryStrategy.FALLBACK
        ):
            self._load_tiles()
            
    def _load_tiles(self) -> None:
        """Load tiles from storage (original implementation)."""
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
            raise
            
    @get_error_boundary().catch_errors(
        component_type="tile_manager",
        operation="save_tiles",
        recovery=RecoveryStrategy.RETRY,
        fallback_value=None
    )
    def _save_tiles(self) -> None:
        """Save tiles with error handling."""
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
            # Don't clear dirty flag on failure
            raise
            
    def create_tile(self, tile_type: str = "note", 
                   initial_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new tile with error recovery.
        
        Returns:
            Created tile data or None on failure
        """
        tile_id = f"tile_{uuid.uuid4()}"
        
        try:
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
            
        except Exception as e:
            # Handle error
            context = ErrorContext(
                error=e,
                component_type="tile",
                component_id=tile_id,
                operation="create"
            )
            
            self.error_boundary.handle_error(
                context,
                recovery=RecoveryStrategy.FALLBACK,
                fallback_value=None
            )
            
            # Clean up on failure
            if tile_id in self._tiles_cache:
                del self._tiles_cache[tile_id]
                
            return None
            
    def update_tile(self, tile_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a tile with error recovery.
        
        Returns:
            Updated tile data or None on failure
        """
        # Check if tile is disabled due to failures
        if self._is_tile_disabled(tile_id):
            self.logger.warning(f"Tile {tile_id} is disabled due to failures")
            return None
            
        with self.error_boundary.error_context(
            component_type="tile",
            component_id=tile_id,
            operation="update",
            recovery=RecoveryStrategy.FALLBACK
        ):
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
            
            # Reset failure count on success
            if tile_id in self._failed_tiles:
                del self._failed_tiles[tile_id]
                
            return tile_data.copy()
            
        # If we get here, an error occurred
        self._record_tile_failure(tile_id)
        return None
        
    def _validate_tile_data(self, tile_data: Dict[str, Any]) -> None:
        """Validate tile data with better error messages."""
        # Required fields
        required = ["id", "type", "x", "y", "width", "height"]
        missing = [field for field in required if field not in tile_data]
        
        if missing:
            raise ValidationError(
                field=", ".join(missing),
                message=f"Required fields are missing: {', '.join(missing)}"
            )
            
        # Validate dimensions
        from core.constants import MIN_TILE_WIDTH, MAX_TILE_WIDTH, MIN_TILE_HEIGHT, MAX_TILE_HEIGHT
        
        width = tile_data.get("width")
        height = tile_data.get("height")
        
        if not isinstance(width, int):
            raise ValidationError(
                field="width",
                message=f"Width must be an integer, got {type(width).__name__}"
            )
            
        if not (MIN_TILE_WIDTH <= width <= MAX_TILE_WIDTH):
            raise ValidationError(
                field="width",
                message=f"Width {width} is out of range [{MIN_TILE_WIDTH}, {MAX_TILE_WIDTH}]"
            )
            
        if not isinstance(height, int):
            raise ValidationError(
                field="height",
                message=f"Height must be an integer, got {type(height).__name__}"
            )
            
        if not (MIN_TILE_HEIGHT <= height <= MAX_TILE_HEIGHT):
            raise ValidationError(
                field="height",
                message=f"Height {height} is out of range [{MIN_TILE_HEIGHT}, {MAX_TILE_HEIGHT}]"
            )
            
    def _record_tile_failure(self, tile_id: str) -> None:
        """Record a tile failure."""
        self._failed_tiles[tile_id] = self._failed_tiles.get(tile_id, 0) + 1
        
        if self._failed_tiles[tile_id] >= self._max_failures:
            self.logger.error(f"Tile {tile_id} disabled after {self._max_failures} failures")
            self.event_bus.emit("tile.disabled", {"tile_id": tile_id})
            
    def _is_tile_disabled(self, tile_id: str) -> bool:
        """Check if a tile is disabled due to failures."""
        return self._failed_tiles.get(tile_id, 0) >= self._max_failures
        
    def reset_tile_failures(self, tile_id: str) -> None:
        """Reset failure count for a tile."""
        if tile_id in self._failed_tiles:
            del self._failed_tiles[tile_id]
            self.logger.info(f"Reset failures for tile {tile_id}")
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of tile manager."""
        total_tiles = len(self._tiles_cache) if self._tiles_cache else 0
        failed_tiles = len(self._failed_tiles)
        disabled_tiles = sum(
            1 for count in self._failed_tiles.values() 
            if count >= self._max_failures
        )
        
        return {
            "total_tiles": total_tiles,
            "failed_tiles": failed_tiles,
            "disabled_tiles": disabled_tiles,
            "cache_dirty": self._cache_dirty,
            "health": "healthy" if failed_tiles == 0 else "degraded"
        }