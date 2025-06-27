# pinpoint/tile_manager.py - The "UI brain" that manages all tiles.

import uuid
from PySide6.QtCore import Signal, QObject, QTimer
from .storage import StorageManager
from .plugin_registry import get_registry


class TileManager(QObject):
    tile_updated_in_studio = Signal(dict)
    tile_config_updated = Signal(dict)  # New signal for config updates
    
    def __init__(self):
        super().__init__()
        self.storage = StorageManager()
        self.active_live_tiles = {}
        self.shutting_down = False
        
        # Plugin registry
        self.registry = get_registry()
        
        # Cache for data to reduce file I/O
        self._data_cache = None
        self._cache_dirty = False
        
        # Debouncing setup for content updates
        self.pending_content_updates = {}
        self.pending_config_updates = {}
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._perform_pending_saves)
        self.save_timer.setSingleShot(True)
        
        # Update source tracking to prevent circular updates
        self._update_in_progress = False
        
        # Connect to plugin registry signals
        self.registry.plugin_loaded.connect(self._on_plugin_loaded)
        self.registry.plugin_error.connect(self._on_plugin_error)

    def _on_plugin_loaded(self, tile_id: str):
        """Handle plugin loaded event."""
        print(f"Plugin loaded: {tile_id}")
        
    def _on_plugin_error(self, tile_id: str, error: str):
        """Handle plugin error event."""
        print(f"Plugin error for {tile_id}: {error}")

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

    def get_all_tile_data(self) -> list:
        return self._get_cached_data().get("tiles", [])

    def get_tile_by_id(self, tile_id: str) -> dict | None:
        for tile in self.get_all_tile_data():
            if tile['id'] == tile_id:
                return tile
        return None

    def get_layout_by_id(self, layout_id: str) -> dict | None:
        for layout in self._get_cached_data().get("layouts", []):
            if layout['id'] == layout_id:
                return layout
        return None
    
    def get_available_tile_types(self) -> dict:
        """Get all available tile types from the plugin registry."""
        return self.registry.export_plugin_info()
    
    def get_tile_categories(self) -> list:
        """Get all tile categories."""
        return self.registry.get_categories()
    
    def create_new_tile_definition(self, tile_type: str = "note"):
        """Creates a new tile definition in the library."""
        print(f"TileManager: Creating new {tile_type} tile definition...")
        
        # Get plugin for this type
        plugin = self.registry.get_plugin(tile_type)
        if not plugin:
            print(f"Unknown tile type: {tile_type}")
            return None
            
        # Get default configuration from plugin
        default_config = plugin.get_default_config()
        
        # Create new tile with plugin defaults
        app_data = self._get_cached_data()
        new_tile = {
            "id": f"tile_{uuid.uuid4()}",
            "type": tile_type,
            **default_config  # Merge in all default settings
        }
        
        app_data.get("tiles", []).append(new_tile)
        self._cache_dirty = True
        self._save_cached_data()  # Immediate save for structural changes
        return new_tile

    def add_tile_to_layout(self, layout_id, tile_id, x, y):
        app_data = self._get_cached_data()
        tile_def = self.get_tile_by_id(tile_id)
        if not tile_def: 
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
                layout.get("tile_instances", []).append(new_instance)
                break
                
        self._cache_dirty = True
        self._save_cached_data()  # Immediate save for structural changes

    def update_tile_instance_position(self, layout_id, instance_id, new_x, new_y):
        app_data = self._get_cached_data()
        for layout in app_data.get("layouts", []):
            if layout['id'] == layout_id:
                for instance in layout.get("tile_instances", []):
                    if instance.get('instance_id') == instance_id:
                        instance['x'], instance['y'] = new_x, new_y
                        break
                break
                
        self._cache_dirty = True
        # Debounce position updates
        self.save_timer.stop()
        self.save_timer.start(500)  # 500ms delay for position updates

    def update_tile_content(self, tile_id: str, new_content: str, source=None):
        """Updates tile content with debouncing and circular update prevention."""
        # Prevent processing our own updates
        if self._update_in_progress:
            return
            
        # Queue the update instead of saving immediately
        self.pending_content_updates[tile_id] = new_content
        
        # Update cache immediately for responsive UI
        app_data = self._get_cached_data()
        for tile in app_data.get("tiles", []):
            if tile['id'] == tile_id:
                tile['content'] = new_content
                updated_tile_data = tile.copy()
                break
        else:
            return  # Tile not found
            
        self._cache_dirty = True
        
        # Emit signal immediately for UI updates
        self._update_in_progress = True
        try:
            self.tile_updated_in_studio.emit(updated_tile_data)
        finally:
            self._update_in_progress = False
        
        # Restart timer (debounce)
        self.save_timer.stop()
        self.save_timer.start(300)  # 300ms delay for content updates
        
    def update_tile_config(self, tile_id: str, config: dict, source=None):
        """Update tile configuration (not just content)."""
        if self._update_in_progress:
            return
            
        # Queue the config update
        self.pending_config_updates[tile_id] = config
        
        # Update cache immediately
        app_data = self._get_cached_data()
        for tile in app_data.get("tiles", []):
            if tile['id'] == tile_id:
                # Update tile with new config, preserving id and type
                tile_type = tile.get('type', 'note')
                tile.clear()
                tile.update(config)
                tile['id'] = tile_id
                tile['type'] = tile_type
                updated_tile_data = tile.copy()
                break
        else:
            return
            
        self._cache_dirty = True
        
        # Emit both signals
        self._update_in_progress = True
        try:
            self.tile_config_updated.emit(updated_tile_data)
            self.tile_updated_in_studio.emit(updated_tile_data)
        finally:
            self._update_in_progress = False
            
        # Restart timer
        self.save_timer.stop()
        self.save_timer.start(300)

    def _perform_pending_saves(self):
        """Performs all pending saves after the debounce period."""
        if self._cache_dirty:
            self._save_cached_data()
            self.pending_content_updates.clear()
            self.pending_config_updates.clear()

    def create_new_layout(self):
        app_data = self._get_cached_data()
        new_layout = {
            "id": f"layout_{uuid.uuid4()}", 
            "name": f"New Layout {len(app_data.get('layouts', [])) + 1}", 
            "tile_instances": []
        }
        app_data.get("layouts", []).append(new_layout)
        self._cache_dirty = True
        self._save_cached_data()  # Immediate save for structural changes
        return new_layout

    def clear_live_tiles(self):
        # Disconnect signals before closing to prevent issues
        for tile_window in self.active_live_tiles.values():
            try:
                tile_window.tile_content_changed.disconnect()
                self.tile_updated_in_studio.disconnect(tile_window.update_display_content)
                if hasattr(tile_window, 'tile_config_changed'):
                    self.tile_config_updated.disconnect(tile_window.update_display_config)
            except:
                pass
            tile_window.close()
        self.active_live_tiles.clear()

    def project_layout(self, layout_id: str):
        """Project a layout using the plugin system to create tiles."""
        self.clear_live_tiles()
        layout_data = self.get_layout_by_id(layout_id)
        if not layout_data: 
            return
            
        for instance in layout_data.get("tile_instances", []):
            tile_def = self.get_tile_by_id(instance['tile_id'])
            if not tile_def:
                continue
                
            # Merge tile definition with instance data
            live_tile_data = {**tile_def, **instance}
            
            # Get tile type
            tile_type = tile_def.get('type', 'note')
            
            # Create tile using plugin system
            tile_window = self.registry.create_tile(tile_type, live_tile_data)
            if not tile_window:
                print(f"Failed to create tile of type: {tile_type}")
                continue
                
            # Connect signals
            tile_window.tile_content_changed.connect(
                lambda tid, content: self.update_tile_content(tid, content, source="live_tile")
            )
            self.tile_updated_in_studio.connect(tile_window.update_display_content)
            
            # Connect config update if supported
            if hasattr(tile_window, 'update_display_config'):
                self.tile_config_updated.connect(tile_window.update_display_config)
            
            self.active_live_tiles[instance['instance_id']] = tile_window
            tile_window.show()
            
    def create_tile_editor(self, tile_id: str):
        """Create an editor for a tile using the plugin system."""
        tile_data = self.get_tile_by_id(tile_id)
        if not tile_data:
            return None
            
        tile_type = tile_data.get('type', 'note')
        return self.registry.create_editor(tile_type, tile_data, self)

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
        
    def duplicate_tile(self, tile_id: str) -> dict:
        """Create a copy of an existing tile."""
        original = self.get_tile_by_id(tile_id)
        if not original:
            return None
            
        app_data = self._get_cached_data()
        new_tile = original.copy()
        new_tile['id'] = f"tile_{uuid.uuid4()}"
        
        # Update content to indicate it's a copy
        if 'content' in new_tile:
            new_tile['content'] = f"Copy of {new_tile['content']}"
            
        app_data.get("tiles", []).append(new_tile)
        self._cache_dirty = True
        self._save_cached_data()
        return new_tile

    def on_app_quit(self):
        self.shutting_down = True
        # Save any pending changes before quitting
        self.save_timer.stop()
        self._perform_pending_saves()