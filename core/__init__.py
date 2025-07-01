# core/__init__.py
"""Core module initialization."""

from .constants import *
from .exceptions import *
from .events import EventBus, EventError, get_event_bus, configure_event_bus
from .logger import Logger, LogLevel, get_logger, configure_global_logger

__all__ = [
    # Constants
    'APP_NAME', 'APP_VERSION', 'APP_AUTHOR',
    'DEFAULT_DATA_FILE', 'USER_DATA_DIR',
    'DEFAULT_TILE_WIDTH', 'DEFAULT_TILE_HEIGHT',
    'MIN_TILE_WIDTH', 'MAX_TILE_WIDTH',
    'MIN_TILE_HEIGHT', 'MAX_TILE_HEIGHT',
    'GRID_SIZE', 'RESIZE_MARGIN',
    'SAVE_DEBOUNCE_DELAY', 'POSITION_UPDATE_DELAY', 'CONTENT_UPDATE_DELAY',
    'DEFAULT_OPACITY', 'MIN_OPACITY', 'MAX_OPACITY',
    'EVENT_TILE_CREATED', 'EVENT_TILE_UPDATED', 'EVENT_TILE_DELETED',
    'EVENT_TILE_MOVED', 'EVENT_TILE_RESIZED',
    'EVENT_LAYOUT_CREATED', 'EVENT_LAYOUT_UPDATED', 'EVENT_LAYOUT_DELETED',
    'EVENT_LAYOUT_PROJECTED',
    'PLUGIN_INTERFACE_VERSION', 'BUILTIN_PLUGINS',
    
    # Exceptions
    'PinPointError', 'TileError', 'LayoutError', 'StorageError',
    'PluginError', 'ValidationError',
    
    # Events
    'EventBus', 'EventError', 'get_event_bus', 'configure_event_bus',
    
    # Logger
    'Logger', 'LogLevel', 'get_logger', 'configure_global_logger',
]