

# tests/test_session1_simple.py
"""
Simple tests for Session 1 core components.
No complex infrastructure - just basic asserts.
"""

import sys
from pathlib import Path
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import constants
from core.exceptions import (
    PinPointError, TileError, LayoutError, 
    StorageError, PluginError, ValidationError
)
from core.events import EventBus, EventError


def test_constants_exist():
    """Test that all expected constants are defined."""
    # Check some key constants
    assert constants.APP_NAME == "PinPoint"
    assert constants.APP_VERSION == "2.0.0"
    assert constants.DEFAULT_TILE_WIDTH == 250
    assert constants.MIN_TILE_WIDTH == 100
    assert constants.GRID_SIZE == 20
    print("✓ Constants test passed")


def test_exceptions_basic():
    """Test basic exception functionality."""
    # Test PinPointError
    try:
        raise PinPointError("Test error")
    except PinPointError as e:
        assert "PinPoint Error: Test error" in str(e)
        
    # Test TileError with tile_id
    try:
        raise TileError(tile_id="tile_123", message="Tile not found")
    except TileError as e:
        assert "Tile tile_123: Tile not found" in str(e)
        assert e.tile_id == "tile_123"
        
    print("✓ Exceptions test passed")


def test_event_bus_basic():
    """Test basic event bus functionality."""
    bus = EventBus()
    received = []
    
    # Test subscribe and emit
    def handler(event):
        received.append(event)
        
    bus.subscribe("test.event", handler)
    bus.emit("test.event", {"value": 42})
    
    assert len(received) == 1
    assert received[0]["event"] == "test.event"
    assert received[0]["data"]["value"] == 42
    print("✓ Event bus basic test passed")


def test_event_bus_multiple_subscribers():
    """Test multiple subscribers to same event."""
    bus = EventBus()
    results = []
    
    def handler1(event):
        results.append("handler1")
        
    def handler2(event):
        results.append("handler2")
        
    bus.subscribe("multi.test", handler1)
    bus.subscribe("multi.test", handler2)
    bus.emit("multi.test")
    
    assert len(results) == 2
    assert "handler1" in results
    assert "handler2" in results
    print("✓ Multiple subscribers test passed")


def test_event_bus_unsubscribe():
    """Test unsubscribe functionality."""
    bus = EventBus()
    count = 0
    
    def handler(event):
        nonlocal count
        count += 1
        
    bus.subscribe("unsub.test", handler)
    bus.emit("unsub.test")
    assert count == 1
    
    bus.unsubscribe("unsub.test", handler)
    bus.emit("unsub.test")
    assert count == 1  # Should not increase
    print("✓ Unsubscribe test passed")


def test_event_bus_error_handling():
    """Test event bus handles callback errors gracefully."""
    bus = EventBus()
    results = []
    
    def bad_handler(event):
        raise RuntimeError("Handler failed")
        
    def good_handler(event):
        results.append("success")
        
    bus.subscribe("error.test", bad_handler)
    bus.subscribe("error.test", good_handler)
    
    # Should not raise, but good handler should still run
    bus.emit("error.test")
    assert len(results) == 1
    assert results[0] == "success"
    print("✓ Error handling test passed")


def test_global_event_bus():
    """Test global event bus singleton."""
    from core.events import get_event_bus
    
    bus1 = get_event_bus()
    bus2 = get_event_bus()
    
    assert bus1 is bus2  # Should be same instance
    print("✓ Global event bus test passed")


def test_validation_error():
    """Test ValidationError with field information."""
    try:
        raise ValidationError(field="email", message="Invalid format")
    except ValidationError as e:
        assert "Validation failed for email" in str(e)
        assert e.field == "email"
    print("✓ Validation error test passed")


def test_event_error():
    """Test EventError for invalid callbacks."""
    bus = EventBus()
    
    try:
        bus.subscribe("test", "not a function")
    except EventError as e:
        assert "Callback must be callable" in str(e)
    print("✓ Event error test passed")


def test_subscriber_count():
    """Test getting subscriber count."""
    bus = EventBus()
    
    assert bus.get_subscriber_count("test.count") == 0
    
    def handler1(e): pass
    def handler2(e): pass
    
    bus.subscribe("test.count", handler1)
    bus.subscribe("test.count", handler2)
    
    assert bus.get_subscriber_count("test.count") == 2
    print("✓ Subscriber count test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 1 tests...")
    test_constants_exist()
    test_exceptions_basic()
    test_event_bus_basic()
    test_event_bus_multiple_subscribers()
    test_event_bus_unsubscribe()
    test_event_bus_error_handling()
    test_global_event_bus()
    test_validation_error()
    test_event_error()
    test_subscriber_count()
    print("\n✅ All Session 1 tests passed!")