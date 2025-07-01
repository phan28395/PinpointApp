
# core/exceptions.py
"""
Custom exceptions for PinPoint.
Layer 1: Uses constants only.
"""

from .constants import APP_NAME


class PinPointError(Exception):
    """Base exception for all PinPoint errors."""
    def __init__(self, message="", details=None):
        self.message = f"{APP_NAME} Error: {message}" if message else f"{APP_NAME} Error"
        self.details = details or {}
        super().__init__(self.message)


class TileError(PinPointError):
    """Raised when tile operations fail."""
    def __init__(self, tile_id=None, message="", details=None):
        self.tile_id = tile_id
        if tile_id:
            message = f"Tile {tile_id}: {message}"
        super().__init__(message, details)


class LayoutError(PinPointError):
    """Raised when layout operations fail."""
    def __init__(self, layout_id=None, message="", details=None):
        self.layout_id = layout_id
        if layout_id:
            message = f"Layout {layout_id}: {message}"
        super().__init__(message, details)


class StorageError(PinPointError):
    """Raised when storage operations fail."""
    pass


class PluginError(PinPointError):
    """Raised when plugin operations fail."""
    def __init__(self, plugin_id=None, message="", details=None):
        self.plugin_id = plugin_id
        if plugin_id:
            message = f"Plugin {plugin_id}: {message}"
        super().__init__(message, details)


class ValidationError(PinPointError):
    """Raised when validation fails."""
    def __init__(self, field=None, message="", details=None):
        self.field = field
        if field:
            message = f"Validation failed for {field}: {message}"
        super().__init__(message, details)
