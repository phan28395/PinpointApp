# tests/test_session3_simple.py
"""
Simple tests for Session 3 components: Tile Manager and Registry.
No complex infrastructure - just basic asserts.
"""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tile_manager import TileManager
from core.tile_registry import TileRegistry, TileTypeInfo, get_tile_registry
from core.exceptions import TileError, ValidationError, PluginError
from core.events import get_event_bus
from data.json_store import JSONStore


def test_tile_manager_create():
    """Test creating tiles."""
    # Use temporary storage
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = TileManager(store)
        
        # Create a tile
        tile = manager.create_tile("note", {"content": "Hello"})
        
        assert tile["type"] == "note"
        assert tile["content"] == "Hello"
        assert "id" in tile
        assert tile["width"] == 250  # Default
        
        # Verify it was saved
        loaded = store.load()
        assert len(loaded["tiles"]) == 1
        
        print("✓ Tile creation test passed")


def test_tile_manager_get():
    """Test getting tiles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = TileManager(store)
        
        # Create tiles
        tile1 = manager.create_tile("note")
        tile2 = manager.create_tile("clock")
        
        # Get by ID
        fetched = manager.get_tile(tile1["id"])
        assert fetched["id"] == tile1["id"]
        
        # Get all
        all_tiles = manager.get_all_tiles()
        assert len(all_tiles) == 2
        
        # Get non-existent
        assert manager.get_tile("fake_id") is None
        
        print("✓ Tile get test passed")


def test_tile_manager_update():
    """Test updating tiles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = TileManager(store)
        
        # Create and update
        tile = manager.create_tile("note")
        updated = manager.update_tile(tile["id"], {"content": "Updated"})
        
        assert updated["content"] == "Updated"
        
        # Try invalid update
        try:
            manager.update_tile("fake_id", {"content": "Test"})
            assert False, "Should raise TileError"
        except TileError:
            pass
            
        print("✓ Tile update test passed")


def test_tile_manager_move_resize():
    """Test moving and resizing tiles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = TileManager(store)
        
        tile = manager.create_tile("note")
        
        # Move
        manager.move_tile(tile["id"], 200, 300)
        moved = manager.get_tile(tile["id"])
        assert moved["x"] == 200
        assert moved["y"] == 300
        
        # Resize
        manager.resize_tile(tile["id"], 400, 200)
        resized = manager.get_tile(tile["id"])
        assert resized["width"] == 400
        assert resized["height"] == 200
        
        # Try invalid resize
        try:
            manager.resize_tile(tile["id"], 50, 200)  # Too small
            assert False, "Should raise ValidationError"
        except ValidationError:
            pass
            
        print("✓ Tile move/resize test passed")


def test_tile_manager_delete():
    """Test deleting tiles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = TileManager(store)
        
        # Create and delete
        tile = manager.create_tile("note")
        manager.delete_tile(tile["id"])
        
        assert manager.get_tile(tile["id"]) is None
        assert len(manager.get_all_tiles()) == 0
        
        print("✓ Tile delete test passed")


def test_tile_manager_events():
    """Test that tile manager emits events."""
    events_received = []
    
    def event_handler(event):
        events_received.append(event)
    
    # Subscribe to events
    event_bus = get_event_bus()
    event_bus.subscribe("tile.created", event_handler)
    event_bus.subscribe("tile.updated", event_handler)
    event_bus.subscribe("tile.moved", event_handler)
    event_bus.subscribe("tile.deleted", event_handler)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = TileManager(store)
        
        # Create tile
        tile = manager.create_tile("note")
        
        # Update tile
        manager.update_tile(tile["id"], {"content": "Test"})
        
        # Move tile
        manager.move_tile(tile["id"], 150, 150)
        
        # Delete tile
        manager.delete_tile(tile["id"])
        
    # Check events
    assert len(events_received) == 4
    event_types = [e["event"] for e in events_received]
    assert "tile.created" in event_types
    assert "tile.updated" in event_types
    assert "tile.moved" in event_types
    assert "tile.deleted" in event_types
    
    print("✓ Tile manager events test passed")


def test_tile_registry_builtin():
    """Test built-in tile types."""
    registry = TileRegistry()
    
    # Check built-in types
    all_types = registry.get_all_types()
    assert len(all_types) == 4  # note, clock, weather, todo
    
    # Check specific type
    note_info = registry.get_type_info("note")
    assert note_info is not None
    assert note_info.name == "Text Note"
    assert note_info.icon == "📝"
    
    print("✓ Tile registry built-in test passed")


def test_tile_registry_operations():
    """Test registry operations."""
    registry = TileRegistry()
    
    # Register custom type
    custom_type = TileTypeInfo(
        tile_type="custom",
        name="Custom Tile",
        description="A custom tile",
        icon="🔧",
        category="Custom",
        default_config={},
        capabilities=["test"]
    )
    
    registry.register_type(custom_type)
    assert registry.is_valid_type("custom")
    
    # Get by category
    custom_tiles = registry.get_types_by_category("Custom")
    assert len(custom_tiles) == 1
    
    # Get categories
    categories = registry.get_categories()
    assert "Custom" in categories
    
    # Check capability
    assert registry.has_capability("custom", "test")
    assert not registry.has_capability("custom", "missing")
    
    # Unregister
    registry.unregister_type("custom")
    assert not registry.is_valid_type("custom")
    
    print("✓ Tile registry operations test passed")


def test_tile_registry_errors():
    """Test registry error handling."""
    registry = TileRegistry()
    
    # Try to register duplicate
    try:
        registry.register_type(TileTypeInfo(
            tile_type="note",  # Already exists
            name="Duplicate",
            description="",
            icon="",
            category="",
            default_config={},
            capabilities=[]
        ))
        assert False, "Should raise PluginError"
    except PluginError:
        pass
        
    print("✓ Tile registry error test passed")


def test_global_registry():
    """Test global registry singleton."""
    registry1 = get_tile_registry()
    registry2 = get_tile_registry()
    
    assert registry1 is registry2
    
    print("✓ Global registry test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 3 tests...")
    test_tile_manager_create()
    test_tile_manager_get()
    test_tile_manager_update()
    test_tile_manager_move_resize()
    test_tile_manager_delete()
    test_tile_manager_events()
    test_tile_registry_builtin()
    test_tile_registry_operations()
    test_tile_registry_errors()
    test_global_registry()
    print("\n✅ All Session 3 tests passed!")