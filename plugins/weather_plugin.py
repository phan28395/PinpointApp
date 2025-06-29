from .plugin_registry import TilePlugin, TileMetadata
from ..base_tile_refactored import BaseTile

class WeatherPlugin(TilePlugin):
    @classmethod
    def get_metadata(cls) -> TileMetadata:
        return TileMetadata(
            tile_id="weather",
            name="Weather",
            description="Display weather information",
            author="PinPoint Team",
            version="1.0.0",
            icon="🌤️",
            category="Information"
        )
    
    @classmethod
    def get_tile_class(cls):
        return BaseTile