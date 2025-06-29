from .plugin_registry import TilePlugin, TileMetadata
from ..base_tile_refactored import BaseTile

class TodoPlugin(TilePlugin):
    @classmethod
    def get_metadata(cls) -> TileMetadata:
        return TileMetadata(
            tile_id="todo",
            name="Todo List",
            description="Manage your tasks",
            author="PinPoint Team",
            version="1.0.0",
            icon="✅",
            category="Productivity"
        )
    
    @classmethod
    def get_tile_class(cls):
        return BaseTile