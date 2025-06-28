Git version: 49d0923 (HEAD -> master) best version
# PinPoint - Current Architecture Documentation
*Save Point Version - Detailed System Analysis*

## 📋 System Overview

PinPoint is a multi-display tile management system built with PySide6 that allows users to create, edit, and project customizable tiles across multiple monitors. The application features a plugin-based architecture for extensible tile types and a sophisticated display management system.

## 🏗️ Current File Structure

```
pinpoint/
├── main.py                     # Application entry point
├── tile_manager.py             # Core business logic & coordination
├── storage.py                  # JSON-based data persistence
├── main_window.py              # Primary UI with tile library & editor
├── tray.py                     # System tray integration
├── layout_editor.py            # Visual layout editing interface
├── editor_tile_item.py         # Draggable tile items in editor
├── draggable_list_widget.py    # Custom drag-and-drop list widget
├── display_manager.py          # Multi-monitor detection & management
├── base_tile.py                # Base class for all live tiles
├── note_tile.py                # Concrete note tile implementation
├── note_editor_widget.py       # Note editing widget for studio
└── plugins/
    ├── plugin_registry.py      # Plugin discovery & management system
    └── note_plugin.py          # Note tile plugin definition
```

## 🔄 Application Flow & Lifecycle

### Startup Sequence
```
1. main.py creates QApplication
2. TileManager initializes (loads storage, initializes plugin registry)
3. MainWindow creates UI (populates libraries from TileManager)
4. SystemTray initializes with references to app, manager, main_window
5. Application shows main window and enters event loop
```

### Plugin Loading Process
```
1. PluginRegistry.initialize() called during TileManager.__init__()
2. _load_builtin_plugins() - loads ["note", "clock", "weather", "todo"]
3. _load_user_plugins() - scans ~/.pinpoint/plugins/ for .py files
4. Each plugin validates metadata and registers with registry
5. Failed plugins emit error signals but don't crash the system
```

### Data Flow Architecture
```
Storage Layer:    StorageManager ↔ JSON File (~/.pinpoint/pinpoint_data.json)
                            ↕
Business Layer:   TileManager (caching, debouncing, coordination)
                            ↕
UI Layer:         MainWindow ↔ LayoutEditor ↔ TileEditors
                            ↕
Live Layer:       Active Tiles (projected to displays)
```

## 🧩 Core Components Deep Dive

### TileManager - The Central Coordinator
**File:** `tile_manager.py`
**Role:** Business logic hub that orchestrates all operations

**Key Responsibilities:**
- **Data Management:** Maintains cached copy of all app data with dirty flagging
- **Plugin Integration:** Bridges plugin system with UI components
- **Live Tile Management:** Creates, updates, and destroys projected tiles
- **Update Coordination:** Prevents circular updates between editors and live tiles
- **Performance Optimization:** Debounces saves and content updates

**Critical Methods:**
```python
# Core tile operations
create_new_tile_definition(tile_type) -> dict
update_tile_content(tile_id, content, source=None)
update_tile_config(tile_id, config, source=None)

# Layout operations  
create_new_layout() -> dict
add_tile_to_layout(layout_id, tile_id, x, y)
project_layout(layout_id, display_index=None)

# Plugin integration
get_available_tile_types() -> dict
create_tile_editor(tile_id) -> QWidget
```

**Data Caching Strategy:**
- Loads data once into `_data_cache`
- Sets `_cache_dirty` flag on modifications
- Debounces saves with QTimer (300ms delay)
- Immediate saves for structural changes (new tiles/layouts)

**Update Prevention System:**
- `_update_in_progress` flag prevents circular updates
- `_last_update_source` tracks update origin
- Source-specific filtering in live tiles

### StorageManager - Data Persistence
**File:** `storage.py`
**Role:** Handles all file I/O operations

**Data Format:**
```json
{
  "tiles": [
    {
      "id": "tile_uuid",
      "type": "note",
      "content": "text content",
      "width": 250,
      "height": 150,
      "font_size": 14,
      "theme": "default"
    }
  ],
  "layouts": [
    {
      "id": "layout_uuid",
      "name": "Layout Name",
      "tile_instances": [
        {
          "instance_id": "inst_uuid",
          "tile_id": "tile_uuid", 
          "x": 100,
          "y": 200,
          "width": 250,
          "height": 150
        }
      ],
      "display_settings": {
        "target_display": 0,
        "display_info": {...}
      }
    }
  ]
}
```

**Migration Logic:**
- Automatically upgrades old list-based format to new dict format
- Adds missing instance_ids to existing layouts
- Backward compatibility maintained

### MainWindow - Primary User Interface
**File:** `main_window.py`
**Role:** Main application interface with tile/layout management

**UI Structure:**
```
MainWindow
├── Toolbar (plugin refresh, open plugin folder)
├── HSplitter
    ├── Left Sidebar (300px)
    │   ├── Layout Controls (New Layout button)
    │   ├── Tile Controls (New Tile button)  
    │   ├── VSplitter
    │   │   ├── Layout Library (QListWidget)
    │   │   └── Enhanced Tile Library (TileLibraryWidget)
    │   └── Plugin Info Label
    └── Central Area (QStackedWidget - 700px)
        ├── Placeholder ("Select an item...")
        ├── LayoutEditor instances (cached)
        └── TileEditor instances (cached)
```

**Key Features:**
- **Editor Caching:** Editors persist in memory, switching via QStackedWidget
- **Enhanced Tile Library:** Category filtering, context menus, plugin metadata
- **Layout Display Info:** Shows target display for each layout
- **Real-time Updates:** Listens to tile_updated_in_studio signal for live updates

### LayoutEditor - Visual Layout Design
**File:** `layout_editor.py`
**Role:** Visual drag-and-drop interface for arranging tiles

**Component Hierarchy:**
```
LayoutEditor (QWidget)
├── Toolbar
│   ├── Display Selector (QComboBox)
│   ├── Display Info Label
│   └── Scale Info Label  
└── LayoutView (QGraphicsView)
    └── LayoutEditorScene (QGraphicsScene)
        ├── Display Visualization (boundary rectangle)
        ├── Grid Background (drawn in drawBackground)
        └── EditorTileItems (draggable tile representations)
```

**Coordinate System:**
- **Editor Coordinates:** Relative to display (0,0 = display top-left)
- **Screen Coordinates:** Absolute screen position for live tiles
- **Conversion:** `screen_pos = editor_pos + display.offset`

**Grid System:**
- 20px grid with snap-to-grid during placement
- 100px ruler lines with measurements
- Grid only drawn within display bounds

**Performance Optimizations:**
- Batched position updates with 100ms debounce timer
- Item mapping (`item_map`) for efficient updates
- Cache mode enabled on graphics items

### DisplayManager - Multi-Monitor Support
**File:** `display_manager.py`  
**Role:** Manages multiple displays and coordinate transformations

**Display Detection:**
```python
class DisplayInfo:
    screen: QScreen           # Qt screen object
    index: int               # Display index (0-based)
    geometry: QRect          # Position and size
    dpi: float              # Physical DPI
    is_primary: bool        # Primary display flag
    
    # Computed properties
    width, height: int      # Display dimensions  
    x, y: int              # Display position
    resolution_string: str  # "1920x1080" format
    display_name: str       # "Display 1: 1920x1080 (Primary)"
```

**Key Capabilities:**
- **Auto-detection:** Responds to display configuration changes
- **Coordinate Transformation:** Editor ↔ Screen coordinate conversion
- **Multi-display Geometry:** Combined bounding rectangle calculation
- **Display Validation:** Ensures tiles stay within bounds

### Plugin System Architecture

#### PluginRegistry - Plugin Management
**File:** `plugins/plugin_registry.py`
**Role:** Discovers, loads, and manages all tile plugins

**Plugin Discovery Process:**
1. **Built-in Plugins:** Hardcoded list `["note", "clock", "weather", "todo"]`
2. **User Plugins:** Scans `~/.pinpoint/plugins/` directory
3. **Module Loading:** Uses `importlib` to load Python modules
4. **Class Discovery:** Finds `TilePlugin` subclasses via `inspect`
5. **Validation:** Validates metadata and tile class inheritance
6. **Registration:** Stores in `_plugins` and `_metadata` dictionaries

**Plugin Capabilities System:**
```python
class TileCapabilities:
    CAN_EDIT = "can_edit"           # Has custom editor
    CAN_REFRESH = "can_refresh"     # Can refresh data
    CAN_INTEGRATE = "can_integrate" # Third-party integration
    CAN_EXPORT = "can_export"       # Can export data
    CAN_SCRIPT = "can_script"       # Supports scripting
    HAS_SETTINGS = "has_settings"   # Has configuration UI
    SUPPORTS_THEMES = "supports_themes" # Theme support
```

#### Note Plugin Implementation
**File:** `plugins/note_plugin.py`
**Role:** Complete implementation example with advanced configuration

**Configuration Schema:**
```python
config_schema = {
    "content": {"type": "string", "default": "New Note"},
    "font_size": {"type": "number", "default": 14, "min": 8, "max": 32},
    "font_family": {"type": "string", "enum": ["Arial", "Times New Roman", ...]},
    "text_color": {"type": "string", "format": "color"},
    "theme": {"type": "string", "enum": ["default", "dark", "light", ...]}
}
```

**Theme System:**
- Predefined theme presets (default, dark, light, solarized, monokai, ocean)
- Custom theme support when user modifies individual settings
- Runtime theme switching with live preview

### Tile Implementation Hierarchy

#### BaseTile - Foundation Class
**File:** `base_tile.py`
**Role:** Provides common functionality for all live tiles

**Core Features:**
- **Frameless Window:** Transparent background, always-on-top
- **Drag & Resize:** Mouse-based repositioning and resizing
- **Pin Toggle:** Always-on-top behavior control
- **Visual States:** Hover effects, resize handles, control buttons
- **Signal System:** Emits tile_content_changed, tile_moved, tile_resized

**Window Behavior:**
```python
setWindowFlags(
    Qt.WindowType.FramelessWindowHint |
    Qt.WindowType.WindowStaysOnTopHint |  # Controllable via pin toggle
    Qt.WindowType.Tool
)
```

**Interaction Modes:**
- **Moving:** Drag from title bar area
- **Resizing:** Drag from bottom-right corner (25px margin)
- **Button Controls:** Close and pin buttons (shown on hover)

#### NoteTile - Concrete Implementation
**File:** `note_tile.py`
**Role:** Text editing tile with debounced updates

**Key Features:**
- **Debounced Text Updates:** 300ms delay prevents excessive saves
- **Circular Update Prevention:** Ignores own updates from external sources
- **Cursor Preservation:** Maintains cursor position during external updates
- **Content Synchronization:** Real-time sync with studio editors

### UI Widgets & Components

#### DraggableListWidget
**File:** `draggable_list_widget.py`
**Role:** Custom QListWidget with drag-and-drop support

**MIME Type System:**
```python
TILE_ID_MIME_TYPE = "application/x-pinpoint-tile-id"
```
- Encodes tile IDs as MIME data for drag operations
- Prevents accidental drops from external applications
- Copy action (non-destructive dragging)

#### EditorTileItem  
**File:** `editor_tile_item.py`
**Role:** Visual representation of tiles in layout editor

**Rendering Features:**
- **State-based Styling:** Normal, hover, and drag visual states
- **Shadow Effects:** Depth perception with drop shadows
- **Text Display:** Truncated tile content with elision
- **Resize Handles:** Visual hint for resize capability
- **Grid Snapping:** 20px grid alignment during movement

**Performance Optimizations:**
- **Device Coordinate Caching:** Reduces redraw overhead
- **Cached Display Text:** Avoids repeated text processing
- **Boundary Constraints:** Prevents tiles from leaving display bounds

## 🔧 System Integration Points

### Signal-Slot Communication Matrix
```
TileManager Signals:
├── tile_updated_in_studio → NoteTile.update_display_content()
├── tile_updated_in_studio → NoteEditorWidget.on_external_update()
├── tile_updated_in_studio → MainWindow.on_tile_data_changed()
├── tile_config_updated → ConfigurableNoteTile.update_display_content()
└── tile_config_updated → MainWindow.on_tile_config_changed()

Live Tile Signals:
├── tile_content_changed → TileManager.update_tile_content()
├── tile_moved → TileManager.update_tile_instance_position()
└── tile_resized → TileManager.update_tile_instance_position()

Display Manager Signals:
├── displays_changed → LayoutEditor._on_displays_changed()
└── display_selected → LayoutEditor._on_display_selected()

Plugin Registry Signals:
├── plugin_loaded → TileManager._on_plugin_loaded()
└── plugin_error → TileManager._on_plugin_error()
```

### Data Flow Patterns

#### Tile Content Updates
```
1. User types in NoteTile
2. NoteTile.on_content_changed() (debounced 300ms)
3. NoteTile emits tile_content_changed(tile_id, content)
4. TileManager.update_tile_content(tile_id, content, source="live_tile_X")
5. TileManager updates cache and emits tile_updated_in_studio(tile_data)
6. NoteEditorWidget.on_external_update() receives update
7. Checks source != "editor" to prevent circular updates
8. Updates editor content while preserving cursor position
```

#### Layout Projection  
```
1. User right-clicks layout → selects "Project to Display N"
2. MainWindow.project_to_display(layout_id, display_index)
3. TileManager.project_layout(layout_id, display_index)
4. TileManager.clear_live_tiles() - cleanup existing tiles
5. For each tile_instance in layout:
   a. Get tile_definition from storage
   b. Convert editor coords to screen coords  
   c. Use PluginRegistry.create_tile() to instantiate
   d. Connect tile signals to TileManager
   e. Store in active_live_tiles dict
   f. Show tile on screen
```

## 🎯 Performance Characteristics

### Memory Management
- **Editor Caching:** UI editors persist in QStackedWidget for fast switching
- **Data Caching:** Single in-memory copy with dirty flagging
- **Live Tile Management:** Active tiles stored in dict for efficient cleanup
- **Plugin Loading:** Plugins loaded once at startup and cached

### I/O Optimization  
- **Debounced Saves:** 300ms delay for content, 500ms for positions
- **Batch Operations:** Multiple position updates batched together
- **Immediate Saves:** Structural changes (new tiles/layouts) saved immediately
- **Migration Caching:** Data format upgrades happen once and persist

### UI Responsiveness
- **Non-blocking Operations:** All file I/O happens on main thread but is debounced
- **Efficient Updates:** Only affected UI elements refresh on data changes
- **Graphics Optimization:** Device coordinate caching, background caching
- **Signal Filtering:** Source tracking prevents unnecessary update cycles

## 🐛 Error Handling Strategy

### Plugin System Resilience
- Failed plugin loads don't crash the application
- Error signals allow UI to show plugin status
- Graceful fallback when plugins are unavailable
- User plugin directory created automatically

### Data Integrity
- Automatic data format migration with fallback
- Default empty structure if file is corrupted
- Validation during tile creation and configuration
- UUID generation prevents ID collisions

### UI Error Recovery
- Safe editor switching with error boundaries
- Display detection handles monitor changes gracefully
- Layout editor constrains tiles to valid bounds
- Tile positioning validation prevents off-screen placement

## 🔮 Extension Points

### Plugin Development
- Well-defined TilePlugin base class with metadata system
- Configuration schema for automatic UI generation
- Theme system integration for consistent styling
- Capability flags for feature discovery

### New Tile Types
1. Inherit from TilePlugin
2. Define metadata with schema
3. Implement tile class (inherits BaseTile)
4. Optional: custom editor widget
5. Place in plugins/ directory or ~/.pinpoint/plugins/

### Display System Extensions  
- DisplayManager supports any Qt screen configuration
- Coordinate transformation system handles complex setups
- Display-specific settings stored per layout
- Spanning mode for multi-display layouts

This architecture represents a mature, extensible desktop application with professional-grade multi-display support and a sophisticated plugin system. The codebase demonstrates strong separation of concerns, performance optimization, and robust error handling suitable for production use.