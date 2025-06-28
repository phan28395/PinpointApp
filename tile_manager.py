# pinpoint/tile_manager.py - The "UI brain" that manages all tiles.

import uuid
from PySide6.QtCore import Signal, QObject, QTimer
from .storage import StorageManager
from .plugins.plugin_registry import get_registry
from .display_manager import get_display_manager


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
        
        # Display manager
        self.display_manager = get_display_manager()
        
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
        self._last_update_source = None
        
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
        # Store the source for filtering
        self._last_update_source = source
        
        # Get current content to check if it actually changed
        current_tile = self.get_tile_by_id(tile_id)
        if not current_tile:
            return
            
        # Skip if content hasn't actually changed
        if current_tile.get('content') == new_content:
            return
            
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
            self._last_update_source = None
        
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
        """Create a new layout with display settings."""
        app_data = self._get_cached_data()
        
        # Get current display info
        selected_display = self.display_manager.get_selected_display()
        display_index = self.display_manager.selected_display_index or 0
        
        new_layout = {
            "id": f"layout_{uuid.uuid4()}", 
            "name": f"New Layout {len(app_data.get('layouts', [])) + 1}", 
            "tile_instances": [],
            "display_settings": {
                "target_display": display_index,
                "display_info": selected_display.to_dict() if selected_display else None
            }
        }
        app_data.get("layouts", []).append(new_layout)
        self._cache_dirty = True
        self._save_cached_data()  # Immediate save for structural changes
        return new_layout
    
    def update_layout_display(self, layout_id: str, display_index: int):
        """Update the target display for a layout."""
        app_data = self._get_cached_data()
        for layout in app_data.get("layouts", []):
            if layout['id'] == layout_id:
                if "display_settings" not in layout:
                    layout["display_settings"] = {}
                    
                layout["display_settings"]["target_display"] = display_index
                
                # Store current display info for reference
                display = self.display_manager.get_display(display_index)
                if display:
                    layout["display_settings"]["display_info"] = display.to_dict()
                    
                break
                
        self._cache_dirty = True
        self._save_cached_data()

    def clear_live_tiles(self):
        # Disconnect signals before closing to prevent issues
        for tile_window in self.active_live_tiles.values():
            try:
                tile_window.tile_content_changed.disconnect()
                # Disconnect the specific update handler
                if hasattr(tile_window, '_update_handler'):
                    self.tile_updated_in_studio.disconnect(tile_window._update_handler)
                if hasattr(tile_window, 'tile_config_changed'):
                    self.tile_config_updated.disconnect(tile_window.update_display_config)
            except:
                pass
            tile_window.close()
        self.active_live_tiles.clear()

    def project_layout(self, layout_id: str, display_index: int = None):
        """Project a layout to a specific display using actual screen coordinates."""
        self.clear_live_tiles()
        layout_data = self.get_layout_by_id(layout_id)
        if not layout_data: 
            return
            
        # Determine which display to use
        if display_index is None:
            # Use layout's saved display or primary
            display_settings = layout_data.get("display_settings", {})
            display_index = display_settings.get("target_display", 0)
            
        # Select the display
        self.display_manager.select_display(display_index)
        display = self.display_manager.get_display(display_index)
        
        if not display:
            print(f"Display {display_index} not found")
            return
            
        print(f"Projecting layout '{layout_data['name']}' to {display.display_name}")
        
        # Update layout's display settings
        self.update_layout_display(layout_id, display_index)
            
        for instance in layout_data.get("tile_instances", []):
            tile_def = self.get_tile_by_id(instance['tile_id'])
            if not tile_def:
                continue
                
            # Merge tile definition with instance data
            live_tile_data = {**tile_def, **instance}
            
            # Convert editor coordinates to screen coordinates
            # Editor coordinates are relative to display, screen coordinates are absolute
            screen_x = instance['x'] + display.x
            screen_y = instance['y'] + display.y
            
            # Update position for screen placement
            live_tile_data['x'] = screen_x
            live_tile_data['y'] = screen_y
            
            # Get tile type
            tile_type = tile_def.get('type', 'note')
            
            # Create tile using plugin system
            tile_window = self.registry.create_tile(tile_type, live_tile_data)
            if not tile_window:
                print(f"Failed to create tile of type: {tile_type}")
                continue
                
            # Create a unique source identifier for this tile instance
            tile_instance_id = instance['instance_id']
            
            # Connect signals with source tracking
            tile_window.tile_content_changed.connect(
                lambda tid, content, inst_id=tile_instance_id: 
                    self.update_tile_content(tid, content, source=f"live_tile_{inst_id}")
            )
            
            # Create a filtered update function for this specific tile
            def create_update_handler(window, inst_id):
                def handler(tile_data):
                    # Only update if this wasn't from the same live tile instance
                    update_source = getattr(self, '_last_update_source', None)
                    if update_source != f"live_tile_{inst_id}":
                        window.update_display_content(tile_data)
                return handler
            
            update_handler = create_update_handler(tile_window, tile_instance_id)
            self.tile_updated_in_studio.connect(update_handler)
            
            # Store the connection for cleanup
            tile_window._update_handler = update_handler
            
            # Connect config update if supported
            if hasattr(tile_window, 'update_display_config'):
                self.tile_config_updated.connect(tile_window.update_display_config)
            
            self.active_live_tiles[instance['instance_id']] = tile_window
            tile_window.show()
            
    def project_layout_to_all_displays(self, layout_id: str):
        """Project a layout to all available displays (span mode)."""
        self.clear_live_tiles()
        layout_data = self.get_layout_by_id(layout_id)
        if not layout_data: 
            return
            
        print(f"Projecting layout '{layout_data['name']}' to all displays")
        
        # Get combined geometry of all displays
        combined_rect = self.display_manager.get_combined_geometry()
        
        for instance in layout_data.get("tile_instances", []):
            tile_def = self.get_tile_by_id(instance['tile_id'])
            if not tile_def:
                continue
                
            # Merge tile definition with instance data
            live_tile_data = {**tile_def, **instance}
            
            # For spanning mode, use absolute coordinates
            # Assuming editor shows primary display, offset by combined rect origin
            screen_x = instance['x'] + combined_rect.x()
            screen_y = instance['y'] + combined_rect.y()
            
            live_tile_data['x'] = screen_x
            live_tile_data['y'] = screen_y
            
            # Get tile type
            tile_type = tile_def.get('type', 'note')
            
            # Create tile using plugin system
            tile_window = self.registry.create_tile(tile_type, live_tile_data)
            if not tile_window:
                continue
                
            # Connect signals (same as single display)
            tile_instance_id = instance['instance_id']
            
            tile_window.tile_content_changed.connect(
                lambda tid, content, inst_id=tile_instance_id: 
                    self.update_tile_content(tid, content, source=f"live_tile_{inst_id}")
            )
            
            def create_update_handler(window, inst_id):
                def handler(tile_data):
                    update_source = getattr(self, '_last_update_source', None)
                    if update_source != f"live_tile_{inst_id}":
                        window.update_display_content(tile_data)
                return handler
            
            update_handler = create_update_handler(tile_window, tile_instance_id)
            self.tile_updated_in_studio.connect(update_handler)
            tile_window._update_handler = update_handler
            
            if hasattr(tile_window, 'update_display_config'):
                self.tile_config_updated.connect(tile_window.update_display_config)
            
            self.active_live_tiles[instance['instance_id']] = tile_window
            tile_window.show()
            
    def get_layout_display_info(self, layout_id: str) -> dict:
        """Get display information for a layout."""
        layout = self.get_layout_by_id(layout_id)
        if not layout:
            return {}
            
        display_settings = layout.get("display_settings", {})
        target_display = display_settings.get("target_display", 0)
        
        # Get current display info
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