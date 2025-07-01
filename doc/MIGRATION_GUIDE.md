# PinPoint 2.0 Migration Guide

This guide helps you migrate from PinPoint 1.x to the new 2.0 architecture.

## Overview

PinPoint 2.0 introduces a complete architectural redesign with:
- Modular, event-driven architecture
- Plugin system for extensibility
- Cross-platform support
- Theming and design system
- Improved error handling
- Better testability

## Breaking Changes

### 1. File Structure
The application now uses platform-specific directories:
- **Windows**: `%APPDATA%\PinPoint` (config), `%LOCALAPPDATA%\PinPoint` (data)
- **macOS**: `~/Library/Application Support/PinPoint`
- **Linux**: `~/.config/pinpoint` (config), `~/.local/share/pinpoint` (data)

### 2. Configuration Format
Configuration is now split into multiple files:
- `config.json` - Application settings
- `tiles.json` - Tile definitions and data
- `layouts.json` - Layout configurations

### 3. Tile Definition Changes
Tiles now require registration with the tile registry:
```python
# Old way
class MyTile(QWidget):
    def __init__(self):
        super().__init__()
        # ... tile code

# New way
from core.tile_manager import get_tile_manager

class MyTile(QWidget):
    tile_type = "my_tile"
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        # ... tile code

# Register tile
tile_manager = get_tile_manager()
tile_manager.register_tile_type("my_tile", MyTile)
```

### 4. Event System
Direct method calls are replaced with events:
```python
# Old way
self.parent().update_tile(self.id, data)

# New way
from core.events import get_event_bus
event_bus = get_event_bus()
event_bus.emit("tile:updated", {"tile_id": self.id, "data": data})
```

## Migration Steps

### Step 1: Backup Your Data
Before migrating, backup your existing PinPoint data:
1. Locate your current PinPoint directory
2. Copy all `.json` files to a safe location
3. Export any custom tiles or configurations

### Step 2: Install PinPoint 2.0
1. Download the latest PinPoint 2.0 release
2. Install using the appropriate method for your platform
3. Run PinPoint 2.0 once to create the directory structure

### Step 3: Import Old Data
Use the import tool to migrate your data:
```bash
python main.py --import path/to/old/config.json
```

Or manually migrate:
1. Copy tile data to the new `tiles.json` format
2. Convert layout data to the new structure
3. Update configuration settings

### Step 4: Update Custom Tiles
If you have custom tiles:

1. **Update imports**:
   ```python
   # Old
   from tile_base import TileBase
   
   # New
   from PyQt6.QtWidgets import QWidget
   from core.events import get_event_bus
   ```

2. **Add tile registration**:
   ```python
   # In your tile file
   def register_tile():
       from core.tile_manager import get_tile_manager
       manager = get_tile_manager()
       manager.register_tile_type("my_custom_tile", MyCustomTile)
   ```

3. **Update event handling**:
   ```python
   # Subscribe to events
   event_bus = get_event_bus()
   event_bus.subscribe("tile:updated", self.on_tile_updated)
   ```

4. **Use theme system**:
   ```python
   from design.theme import get_theme_manager
   from design.components import get_component_registry
   
   theme = get_theme_manager().get_current_theme()
   registry = get_component_registry()
   
   # Apply themed styles
   style = registry.get_style("button", variant="primary")
   self.button.setStyleSheet(style)
   ```

### Step 5: Convert to Plugins (Optional)
Convert standalone tiles to plugins for better modularity:

1. Create plugin structure:
   ```
   my_plugin/
   ├── __init__.py
   ├── plugin.json
   └── tiles.py
   ```

2. Create `plugin.json`:
   ```json
   {
       "id": "my_plugin",
       "name": "My Custom Plugin",
       "version": "1.0.0",
       "author": "Your Name",
       "description": "My custom tiles",
       "entry_point": "my_plugin",
       "tiles": ["my_custom_tile"]
   }
   ```

3. Implement plugin interface:
   ```python
   from plugins.base import BasePlugin
   
   class MyPlugin(BasePlugin):
       def activate(self):
           # Register tiles
           self.register_tile("my_custom_tile", MyCustomTile)
   ```

## Data Format Changes

### Old Tile Format (1.x)
```json
{
    "id": "12345",
    "type": "note",
    "x": 100,
    "y": 200,
    "width": 250,
    "height": 150,
    "data": {
        "content": "My note"
    }
}
```

### New Tile Format (2.0)
```json
{
    "id": "12345",
    "type": "note",
    "config": {
        "title": "My Note",
        "content": "My note content"
    },
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

Position is now stored in layouts:
```json
{
    "tile_instances": [{
        "id": "instance_123",
        "tile_id": "12345",
        "position": {"x": 100, "y": 200},
        "size": {"width": 250, "height": 150},
        "z_order": 0
    }]
}
```

## API Changes

### Event Bus
```python
# Subscribe to events
event_bus.subscribe("tile:created", callback)
event_bus.subscribe("layout:switched", callback)

# Emit events
event_bus.emit("custom:event", {"data": value})
```

### Storage
```python
from data.json_store import JSONStore

store = JSONStore(path)
store.set("key", value)
value = store.get("key", default)
```

### Logging
```python
from core.logger import get_logger

logger = get_logger()
logger.info("Message", data={"key": "value"})
```

### Platform Support
```python
from platform_support import get_platform

platform = get_platform()
config_dir = platform.get_config_dir()
platform.show_notification("Title", "Message")
```

## Troubleshooting

### Common Issues

1. **Import fails**: Ensure the old configuration file is valid JSON
2. **Tiles don't appear**: Check that tiles are registered with the tile manager
3. **Events not working**: Verify event names match exactly (case-sensitive)
4. **Theme not applied**: Ensure you're using the component registry for styles

### Debug Mode
Run with debug logging to diagnose issues:
```bash
python main.py --debug
```

### Getting Help
- Check the logs in the platform-specific log directory
- Review the example implementations in the codebase
- Submit issues on the project repository

## Benefits of Migration

1. **Better Performance**: Event-driven architecture reduces coupling
2. **Extensibility**: Easy to add new features via plugins
3. **Maintainability**: Cleaner code organization
4. **Cross-Platform**: Proper support for Windows, macOS, and Linux
5. **Theming**: Consistent visual design with theme support
6. **Error Recovery**: Improved error handling prevents crashes

## Example: Migrating a Custom Tile

Here's a complete example of migrating a custom countdown tile:

### Old Version (1.x)
```python
class CountdownTile(TileBase):
    def __init__(self, tile_id, data):
        super().__init__(tile_id, data)
        self.setup_ui()
        
    def setup_ui(self):
        self.label = QLabel(self.data.get("text", ""))
        self.layout.addWidget(self.label)
        
    def update_data(self, data):
        self.data = data
        self.label.setText(data.get("text", ""))
        self.save_tile()
```

### New Version (2.0)
```python
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from core.events import get_event_bus
from design.components import get_component_registry, ComponentType

class CountdownTile(QWidget):
    tile_type = "countdown"
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.tile_id = config.get("id")
        self.event_bus = get_event_bus()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Use themed styling
        registry = get_component_registry()
        
        self.label = QLabel(self.config.get("text", ""))
        self.label.setStyleSheet(
            registry.get_style(ComponentType.LABEL, size="lg")
        )
        layout.addWidget(self.label)
        
        # Subscribe to updates
        self.event_bus.subscribe(
            f"tile:update:{self.tile_id}", 
            self.on_update
        )
        
    def on_update(self, event_data):
        new_config = event_data.get("config", {})
        self.config.update(new_config)
        self.label.setText(self.config.get("text", ""))
        
    def closeEvent(self, event):
        # Emit deletion event
        self.event_bus.emit("tile:deleted", {
            "tile_id": self.tile_id
        })
        super().closeEvent(event)

# Registration function for the tile
def register():
    from core.tile_manager import get_tile_manager
    manager = get_tile_manager()
    manager.register_tile_type("countdown", CountdownTile)
```

This migration guide should help you successfully upgrade to PinPoint 2.0. The new architecture provides a solid foundation for future enhancements while maintaining the core functionality you rely on.