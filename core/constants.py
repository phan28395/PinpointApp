# core/constants.py
"""
Application constants for PinPoint.
Layer 0: No dependencies allowed.
"""

# Application info
APP_NAME = "PinPoint"
APP_VERSION = "2.0.0"
APP_AUTHOR = "PinPoint Team"

# File paths
DEFAULT_DATA_FILE = "pinpoint_data.json"
USER_DATA_DIR = ".pinpoint"

# UI Constants
DEFAULT_TILE_WIDTH = 250
DEFAULT_TILE_HEIGHT = 150
MIN_TILE_WIDTH = 100
MAX_TILE_WIDTH = 600
MIN_TILE_HEIGHT = 80
MAX_TILE_HEIGHT = 800

# Grid and positioning
GRID_SIZE = 20
RESIZE_MARGIN = 25

# Timing constants (milliseconds)
SAVE_DEBOUNCE_DELAY = 300
POSITION_UPDATE_DELAY = 100
CONTENT_UPDATE_DELAY = 300

# Display constants
DEFAULT_OPACITY = 1.0
MIN_OPACITY = 0.1
MAX_OPACITY = 1.0

# Event names
EVENT_TILE_CREATED = "tile.created"
EVENT_TILE_UPDATED = "tile.updated"
EVENT_TILE_DELETED = "tile.deleted"
EVENT_TILE_MOVED = "tile.moved"
EVENT_TILE_RESIZED = "tile.resized"
EVENT_LAYOUT_CREATED = "layout.created"
EVENT_LAYOUT_UPDATED = "layout.updated"
EVENT_LAYOUT_DELETED = "layout.deleted"
EVENT_LAYOUT_PROJECTED = "layout.projected"

# Plugin constants
PLUGIN_INTERFACE_VERSION = "1.0"
BUILTIN_PLUGINS = ["note", "clock", "weather", "todo"]
