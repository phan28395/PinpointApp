# tests/test_session5_simple.py
"""
Simple tests for Session 5: Layout Management.
Tests layout manager and display manager.
"""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.layout_manager import LayoutManager, TileInstance
from core.display_manager import DisplayManager, DisplayInfo, get_display_manager
from core.exceptions import LayoutError
from core.events import get_event_bus
from data.json_store import JSONStore


def test_layout_creation():
    """Test creating layouts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = LayoutManager(store)
        
        # Create layout with auto name
        layout1 = manager.create_layout()
        assert layout1["name"] == "Layout 1"
        assert "id" in layout1
        assert layout1["tile_instances"] == []
        
        # Create layout with custom name
        layout2 = manager.create_layout("My Layout", display_index=1)
        assert layout2["name"] == "My Layout"
        assert layout2["display_settings"]["target_display"] == 1
        
        # Verify saved
        loaded = store.load()
        assert len(loaded["layouts"]) == 2
        
        print("✓ Layout creation test passed")


def test_layout_operations():
    """Test layout CRUD operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = LayoutManager(store)
        
        # Create
        layout = manager.create_layout("Test Layout")
        layout_id = layout["id"]
        
        # Get
        fetched = manager.get_layout(layout_id)
        assert fetched["name"] == "Test Layout"
        
        # Update
        updated = manager.update_layout(layout_id, {"name": "Updated Layout"})
        assert updated["name"] == "Updated Layout"
        
        # Get all
        all_layouts = manager.get_all_layouts()
        assert len(all_layouts) == 1
        
        # Delete
        manager.delete_layout(layout_id)
        assert manager.get_layout(layout_id) is None
        
        print("✓ Layout operations test passed")


def test_tile_instances():
    """Test managing tile instances in layouts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = LayoutManager(store)
        
        layout = manager.create_layout("Test")
        layout_id = layout["id"]
        
        # Add tile instance
        instance = manager.add_tile_to_layout(
            layout_id, "tile_123", 100, 200, 250, 150
        )
        assert instance.tile_id == "tile_123"
        assert instance.x == 100
        assert instance.y == 200
        
        # Get instances
        instances = manager.get_layout_instances(layout_id)
        assert len(instances) == 1
        assert instances[0].instance_id == instance.instance_id
        
        # Update instance
        manager.update_tile_instance(
            layout_id, instance.instance_id, {"x": 150, "y": 250}
        )
        
        # Verify update
        instances = manager.get_layout_instances(layout_id)
        assert instances[0].x == 150
        assert instances[0].y == 250
        
        # Remove instance
        manager.remove_tile_from_layout(layout_id, instance.instance_id)
        instances = manager.get_layout_instances(layout_id)
        assert len(instances) == 0
        
        print("✓ Tile instances test passed")


def test_layout_events():
    """Test that layout manager emits events."""
    events_received = []
    
    def event_handler(event):
        events_received.append(event)
    
    # Subscribe to events
    event_bus = get_event_bus()
    event_bus.subscribe("layout.created", event_handler)
    event_bus.subscribe("layout.updated", event_handler)
    event_bus.subscribe("layout.deleted", event_handler)
    event_bus.subscribe("layout.projected", event_handler)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = LayoutManager(store)
        
        # Create
        layout = manager.create_layout("Test")
        
        # Update
        manager.update_layout(layout["id"], {"name": "Updated"})
        
        # Project
        manager.project_layout(layout["id"])
        
        # Delete
        manager.delete_layout(layout["id"])
        
    # Check events
    assert len(events_received) == 4
    event_types = [e["event"] for e in events_received]
    assert "layout.created" in event_types
    assert "layout.updated" in event_types
    assert "layout.projected" in event_types
    assert "layout.deleted" in event_types
    
    print("✓ Layout events test passed")


def test_layout_errors():
    """Test layout error handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        manager = LayoutManager(store)
        
        # Try to get non-existent layout
        assert manager.get_layout("fake_id") is None
        
        # Try to update non-existent layout
        try:
            manager.update_layout("fake_id", {"name": "Test"})
            assert False, "Should raise LayoutError"
        except LayoutError:
            pass
            
        # Try to remove non-existent instance
        layout = manager.create_layout()
        try:
            manager.remove_tile_from_layout(layout["id"], "fake_instance")
            assert False, "Should raise LayoutError"
        except LayoutError:
            pass
            
        print("✓ Layout errors test passed")


def test_tile_instance_dataclass():
    """Test TileInstance dataclass."""
    # Create instance
    instance = TileInstance(
        instance_id="inst_123",
        tile_id="tile_456",
        x=10,
        y=20,
        width=100,
        height=200
    )
    
    # To dict
    data = instance.to_dict()
    assert data["instance_id"] == "inst_123"
    assert data["x"] == 10
    
    # From dict
    instance2 = TileInstance.from_dict(data)
    assert instance2.instance_id == instance.instance_id
    assert instance2.x == instance.x
    
    print("✓ TileInstance dataclass test passed")


def test_display_manager_basics():
    """Test basic display manager functionality."""
    manager = DisplayManager()
    
    # Get displays
    displays = manager.get_displays()
    assert len(displays) >= 1  # At least one mock display
    
    # Get specific display
    display = manager.get_display(0)
    assert display is not None
    assert display.index == 0
    
    # Get primary
    primary = manager.get_primary_display()
    assert primary is not None
    assert primary.is_primary
    
    # Display count
    assert manager.get_display_count() == len(displays)
    
    print("✓ Display manager basics test passed")


def test_display_info():
    """Test DisplayInfo dataclass."""
    display = DisplayInfo(
        index=0,
        name="Test Display",
        x=0,
        y=0,
        width=1920,
        height=1080,
        is_primary=True,
        scale_factor=1.5
    )
    
    # Properties
    assert display.resolution_string == "1920x1080"
    assert "(Primary)" in display.display_name
    
    # To/from dict
    data = display.to_dict()
    display2 = DisplayInfo.from_dict(data)
    assert display2.name == display.name
    assert display2.width == display.width
    
    print("✓ DisplayInfo test passed")


def test_display_manager_operations():
    """Test display manager operations."""
    manager = DisplayManager()
    
    # Select display
    assert manager.select_display(0)
    assert manager.get_selected_display().index == 0
    
    # Invalid selection
    assert not manager.select_display(999)
    
    # Combined bounds
    bounds = manager.get_combined_bounds()
    assert len(bounds) == 4  # min_x, min_y, max_x, max_y
    
    # Display at point
    display = manager.get_display_at_point(100, 100)
    assert display is not None
    
    # No display at point
    display = manager.get_display_at_point(-1000, -1000)
    assert display is None
    
    print("✓ Display manager operations test passed")


def test_global_display_manager():
    """Test global display manager singleton."""
    manager1 = get_display_manager()
    manager2 = get_display_manager()
    
    assert manager1 is manager2
    
    print("✓ Global display manager test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 5 tests...")
    test_layout_creation()
    test_layout_operations()
    test_tile_instances()
    test_layout_events()
    test_layout_errors()
    test_tile_instance_dataclass()
    test_display_manager_basics()
    test_display_info()
    test_display_manager_operations()
    test_global_display_manager()
    print("\n✅ All Session 5 tests passed!")