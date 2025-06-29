from .plugin_registry import TilePlugin, TileMetadata
from ..base_tile import BaseTile

class ClockPlugin(TilePlugin):
    @classmethod
    def get_metadata(cls) -> TileMetadata:
        return TileMetadata(
            tile_id="clock",
            name="Clock",
            description="Display current time",
            author="PinPoint Team",
            version="1.0.0",
            icon="🕐",
            category="Utility"
        )
    
    @classmethod
    def get_tile_class(cls):
        # Return BaseTile as placeholder
        return BaseTile