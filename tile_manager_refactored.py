# pinpoint/tile_manager_refactored.py
"""
Refactored tile manager that passes design layer to all components.
Focuses on functionality and data management, no visual styling.
"""

import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from PySide6.QtCore import Signal, QObject, QTimer
from PySide6.QtWidgets import QWidget

from .storage import StorageManager
from .plugins.plugin_registry import get_registry
from .display_manager import get_display_manager
from .design_layer import DesignLayer


class TileManager(QObject):
    """
    Tile manager that coordinates tiles, layouts, and plugins.
    All visual aspects are handled by the design layer.
    """
    
    # Signals for data changes only
    tile_updated_in_studio = Signal(dict)
    tile_config_updated = Signal(dict)
    tile_design_changed = Signal(str, str)  # tile_id, design_id
    layout_design_changed = Signal(str, dict)  # layout_id, design_settings
    
    def __init__(self, design_layer: DesignLayer):
        super().__init__()
        self.design = design_layer
        self.storage = StorageManager()
        self.active_live_tiles = {}
        self.shutting_down = False
        
        # Plugin and display managers
        self.registry = get_registry()
        self.display_manager = get_display_manager()
        
        # Cache for data
        self._data_cache = None
        self._cache_dirty = False
        
        # Debouncing for saves
        self.pending_content_updates = {}
        self.pending_config_updates = {}
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._perform_pending_saves)
        self.save_timer.setSingleShot(True)
        
        # Update tracking
        self._update_in_progress = False
        self._last_update_source = None
        
        # Connect to registry signals
        self.registry.plugin_loaded.connect(self._on_plugin_loaded)
        self.registry.plugin_error.connect(self._on_plugin_error)
        
    def _get_cached_data(self):
        """Returns cached data, loading from storage if necessary."""
        if self._data_cache is None:
            self._data_cache = self.storage.load_data()
        return self._data_cache
    
    def _save_cached_data(self):
        """Saves the cached data to storage."""
        if self._data_cache is not None and self._cache_dirty:
            self.storage.save_data(self._data_cache)
            self._cache_dirty = False
            
    # Core data access methods
    def get_all_tile_data(self) -> List[Dict[str, Any]]:
        """Get all tile definitions."""
        return self._get_cached_data().get("tiles", [])
        
    def get_tile_by_id(self, tile_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tile by ID."""
        for tile in self.get_all_tile_data():
            if tile['id'] == tile_id:
                return tile
        return None
        
    def get_layout_by_id(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific layout by ID."""
        for layout in self._get_cached_data().get("layouts", []):
            if layout['id'] == layout_id:
                return layout
        return None
        
    def get_layout_display_info(self, layout_id: str) -> dict:
        """Get display information for a layout."""
        layout = self.get_layout_by_id(layout_id)
        if not layout:
            return {}
            
        display_settings = layout.get("display_settings", {})
        target_display = display_settings.get("target_display", 0)
        
        display = self.display_manager.get_display(target_display)
        if display:
            return {
                "target_display": target_display,
                "display_name": display.display_name,
                "resolution": display.resolution_string,
                "saved_info": display_settings.get("display_info")
            }
        else:
            return {
                "target_display": target_display,
                "display_name": "Unknown",
                "saved_info": display_settings.get("display_info")
            }
            
    # Tile creation and management
    def create_new_tile_definition(self, tile_type: str = "note"):
        """Creates a new tile definition."""
        print(f"Creating new {tile_type} tile...")
        
        plugin = self.registry.get_plugin(tile_type)
        if not plugin:
            print(f"Unknown tile type: {tile_type}")
            return None
            
        # Get default configuration
        default_config = plugin.get_default_config()
        
        # Create new tile
        app_data = self._get_cached_data()
        new_tile = {
            "id": f"tile_{uuid.uuid4()}",
            "type": tile_type,
            **default_config
        }
        
        app_data.get("tiles", []).append(new_tile)
        self._cache_dirty = True
        self._save_cached_data()
        return new_tile
        
    def duplicate_tile(self, tile_id: str) -> Optional[Dict[str, Any]]:
        """Create a copy of an existing tile."""
        original = self.get_tile_by_id(tile_id)
        if not original:
            return None
            
        app_data = self._get_cached_data()
        new_tile = original.copy()
        new_tile['id'] = f"tile_{uuid.uuid4()}"
        
        # Update content to indicate it's a copy
        if 'content' in new_tile:
            content = new_tile['content']
            if content:
                new_tile['content'] = f"Copy of {content}"
            else:
                new_tile['content'] = "Copy of tile"
                
        app_data.get("tiles", []).append(new_tile)
        self._cache_dirty = True
        self._save_cached_data()
        return new_tile
        
    def delete_tile(self, tile_id: str):
        """Delete a tile definition and all its instances."""
        app_data = self._get_cached_data()
        
        # Remove tile definition
        app_data['tiles'] = [t for t in app_data.get('tiles', []) if t['id'] != tile_id]
        
        # Remove instances from all layouts
        for layout in app_data.get('layouts', []):
            layout['tile_instances'] = [
                inst for inst in layout.get('tile_instances', [])
                if inst['tile_id'] != tile_id
            ]
            
        self._cache_dirty = True
        self._save_cached_data()
        
    def update_tile_content(self, tile_id: str, new_content: str, source=None):
        """Updates tile content with debouncing."""
        self._last_update_source = source
        
        current_tile = self.get_tile_by_id(tile_id)
        if not current_tile:
            return
            
        if current_tile.get('content') == new_content:
            return
            
        if self._update_in_progress:
            return
            
        self.pending_content_updates[tile_id] = new_content
        
        app_data = self._get_cached_data()
        for tile in app_data.get("tiles", []):
            if tile['id'] == tile_id:
                tile['content'] = new_content
                updated_tile_data = tile.copy()
                break
        else:
            return
            
        self._cache_dirty = True
        
        self._update_in_progress = True
        try:
            self.tile_updated_in_studio.emit(updated_tile_data)
        finally:
            self._update_in_progress = False
            self._last_update_source = None
        
        self.save_timer.stop()
        self.save_timer.start(300)
        
    def update_tile_config(self, tile_id: str, config_data: dict):
        """Update tile configuration."""
        app_data = self._get_cached_data()
        for tile in app_data.get("tiles", []):
            if tile['id'] == tile_id:
                tile.update(config_data)
                self._cache_dirty = True
                self.tile_config_updated.emit(tile.copy())
                break
                
        self._save_cached_data()
        
    # Layout management
    def create_new_layout(self, name: Optional[str] = None):
        """Create a new layout."""
        app_data = self._get_cached_data()
        
        selected_display = self.display_manager.get_selected_display()
        display_index = self.display_manager.selected_display_index or 0
        
        layout_count = len(app_data.get('layouts', []))
        new_layout = {
            "id": f"layout_{uuid.uuid4()}",
            "name": name or f"New Layout {layout_count + 1}",
            "tile_instances": [],
            "display_settings": {
                "target_display": display_index,
                "display_info": selected_display.to_dict() if selected_display else None
            }
        }
        
        app_data.get("layouts", []).append(new_layout)
        self._cache_dirty = True
        self._save_cached_data()
        return new_layout
        
    def update_layout_display(self, layout_id: str, display_index: int):
        """Update the target display for a layout."""
        app_data = self._get_cached_data()
        for layout in app_data.get("layouts", []):
            if layout['id'] == layout_id:
                if "display_settings" not in layout:
                    layout["display_settings"] = {}
                    
                layout["display_settings"]["target_display"] = display_index
                
                display = self.display_manager.get_display(display_index)
                if display:
                    layout["display_settings"]["display_info"] = display.to_dict()
                    
                break
                
        self._cache_dirty = True
        self._save_cached_data()
        
    def add_tile_to_layout(self, layout_id: str, tile_id: str, x: int, y: int):
        """Add a tile instance to a layout."""
        app_data = self._get_cached_data()
        tile_def = self.get_tile_by_id(tile_id)
        if not tile_def:
            print(f"Tile {tile_id} not found")
            return
            
        for layout in app_data.get("layouts", []):
            if layout['id'] == layout_id:
                new_instance = {
                    "instance_id": f"inst_{uuid.uuid4()}",
                    "tile_id": tile_id,
                    "x": x,
                    "y": y,
                    "width": tile_def.get("width", 250),
                    "height": tile_def.get("height", 150)
                }
                
                if "tile_instances" not in layout:
                    layout["tile_instances"] = []
                layout["tile_instances"].append(new_instance)
                
                print(f"Added tile {tile_id} to layout {layout_id} at ({x}, {y})")
                break
        else:
            print(f"Layout {layout_id} not found")
            return
            
        self._cache_dirty = True
        self._save_cached_data()
        
    def update_tile_instance_position(self, layout_id: str, instance_id: str, new_x: int, new_y: int):
        """Update the position of a tile instance."""
        app_data = self._get_cached_data()
        for layout in app_data.get("layouts", []):
            if layout['id'] == layout_id:
                for instance in layout.get("tile_instances", []):
                    if instance.get('instance_id') == instance_id:
                        instance['x'] = new_x
                        instance['y'] = new_y
                        break
                break
                
        self._cache_dirty = True
        self.save_timer.stop()
        self.save_timer.start(500)
        
    def update_tile_instance_size(self, layout_id: str, instance_id: str, new_width: int, new_height: int):
        """Update the size of a tile instance."""
        app_data = self._get_cached_data()
        for layout in app_data.get("layouts", []):
            if layout['id'] == layout_id:
                for instance in layout.get("tile_instances", []):
                    if instance.get('instance_id') == instance_id:
                        instance['width'] = new_width
                        instance['height'] = new_height
                        break
                break
                
        self._cache_dirty = True
        self.save_timer.stop()
        self.save_timer.start(500)
        
    # Tile projection
    def project_layout(self, layout_id: str, display_index: int = None):
        """Project a layout to display."""
        self.clear_live_tiles()
        layout_data = self.get_layout_by_id(layout_id)
        if not layout_data:
            return
            
        if display_index is None:
            display_settings = layout_data.get("display_settings", {})
            display_index = display_settings.get("target_display", 0)
            
        self.display_manager.select_display(display_index)
        display = self.display_manager.get_display(display_index)
        
        if not display:
            print(f"Display {display_index} not found")
            return
            
        print(f"Projecting layout '{layout_data['name']}' to {display.display_name}")
        
        self.update_layout_display(layout_id, display_index)
        
        for instance in layout_data.get("tile_instances", []):
            self._project_tile_instance(instance, display)
            
    def _project_tile_instance(self, instance: Dict[str, Any], display):
        """Project a single tile instance."""
        tile_def = self.get_tile_by_id(instance['tile_id'])
        if not tile_def:
            return
            
        # Merge tile definition with instance data
        live_tile_data = {**tile_def, **instance}
        
        # Convert coordinates
        screen_x = instance['x'] + display.x
        screen_y = instance['y'] + display.y
        
        live_tile_data['x'] = screen_x
        live_tile_data['y'] = screen_y
        
        # Get tile type
        tile_type = tile_def.get('type', 'note')
        
        # Create tile with design layer
        tile_window = self._create_tile_with_design(tile_type, live_tile_data)
        if not tile_window:
            print(f"Failed to create tile of type: {tile_type}")
            return
            
        # Connect signals
        self._connect_tile_signals(tile_window, instance['instance_id'])
        
        # Store reference
        self.active_live_tiles[instance['instance_id']] = tile_window
        tile_window.show()
        
    def _create_tile_with_design(self, tile_type: str, tile_data: dict) -> Optional[QWidget]:
        """Create a tile with design layer support."""
        # Import here to avoid circular imports
        from .base_tile_refactored import BaseTile
        from .note_tile_refactored import NoteTile
        
        # Map of tile types to classes (this would come from plugin registry)
        tile_classes = {
            'note': NoteTile,
            # Add more tile types here
        }
        
        tile_class = tile_classes.get(tile_type)
        if not tile_class:
            print(f"Unknown tile type: {tile_type}")
            return None
            
        try:
            # Create tile with design layer
            tile_widget = tile_class(tile_data, self.design)
            return tile_widget
        except Exception as e:
            print(f"Error creating tile: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def _connect_tile_signals(self, tile_window, instance_id: str):
        """Connect tile signals for synchronization."""
        tile_window.tile_content_changed.connect(
            lambda tid, content: self.update_tile_content(
                tid, content, source=f"live_tile_{instance_id}"
            )
        )
        
        def create_update_handler(window, inst_id):
            def handler(tile_data):
                update_source = getattr(self, '_last_update_source', None)
                if update_source != f"live_tile_{inst_id}":
                    window.update_display_content(tile_data)
            return handler
        
        update_handler = create_update_handler(tile_window, instance_id)
        self.tile_updated_in_studio.connect(update_handler)
        tile_window._update_handler = update_handler
        
        if hasattr(tile_window, 'update_display_config'):
            self.tile_config_updated.connect(tile_window.update_display_config)
            
    def create_tile_editor(self, tile_id: str) -> Optional[QWidget]:
        """Create an editor for a tile."""
        tile_data = self.get_tile_by_id(tile_id)
        if not tile_data:
            return None
            
        tile_type = tile_data.get('type', 'note')
        
        # Import here to avoid circular imports
        from .note_editor_widget import NoteEditorWidget
        
        # Map of tile types to editor classes
        editor_classes = {
            'note': NoteEditorWidget,
            # Add more editor types here
        }
        
        editor_class = editor_classes.get(tile_type)
        if not editor_class:
            print(f"No editor available for tile type: {tile_type}")
            return None
            
        try:
            return editor_class(tile_data, self)
        except Exception as e:
            print(f"Error creating editor: {e}")
            return None
            
    def clear_live_tiles(self):
        """Clear all active live tiles."""
        for tile_window in self.active_live_tiles.values():
            try:
                # Disconnect signals
                tile_window.tile_content_changed.disconnect()
                if hasattr(tile_window, '_update_handler'):
                    self.tile_updated_in_studio.disconnect(tile_window._update_handler)
                if hasattr(tile_window, 'tile_config_changed'):
                    self.tile_config_updated.disconnect(tile_window.update_display_config)
            except:
                pass
            tile_window.close()
        self.active_live_tiles.clear()
        
    def on_app_quit(self):
        """Handle application quit."""
        self.shutting_down = True
        self.save_timer.stop()
        self._perform_pending_saves()
        
    def _perform_pending_saves(self):
        """Perform all pending saves."""
        if self._cache_dirty:
            self._save_cached_data()
            self.pending_content_updates.clear()
            self.pending_config_updates.clear()
            
    def _on_plugin_loaded(self, plugin_id: str):
        """Handle plugin loaded event."""
        print(f"Plugin loaded: {plugin_id}")
        
    def _on_plugin_error(self, plugin_id: str, error: str):
        """Handle plugin error event."""
        print(f"Plugin error for {plugin_id}: {error}")