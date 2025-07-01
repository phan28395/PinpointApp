# tests/test_session2_simple.py
"""
Simple tests for Session 2 components: Logger and Storage.
No complex infrastructure - just basic asserts.
"""

import sys
from pathlib import Path
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import Logger, LogLevel, get_logger, configure_global_logger
from core.events import EventBus, configure_event_bus
from data.json_store import JSONStore
from core.exceptions import StorageError


def test_logger_basic():
    """Test basic logger functionality."""
    # Create a temporary log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = Path(f.name)
    
    try:
        logger = Logger("test", log_file=log_file, console=False)
        
        # Log some messages
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Read log file
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Should have 4 lines (debug excluded due to default INFO level)
        assert len(lines) == 4
        
        # Check each line is valid JSON
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "logger" in entry
            assert "level" in entry
            assert "message" in entry
            
        print("✓ Logger basic test passed")
        
    finally:
        # Clean up
        if log_file.exists():
            log_file.unlink()


def test_logger_levels():
    """Test logger level filtering."""
    entries = []
    
    # Custom logger that collects entries
    logger = Logger("test", console=False, level=LogLevel.WARNING)
    
    # Override _write_entry to collect entries
    original_write = logger._write_entry
    def collect_write(entry):
        entries.append(entry)
    logger._write_entry = collect_write
    
    # Log at different levels
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    
    # Should only have warning and error
    assert len(entries) == 2
    assert entries[0]["level"] == "WARNING"
    assert entries[1]["level"] == "ERROR"
    
    print("✓ Logger levels test passed")


def test_logger_with_data():
    """Test logging with structured data."""
    entries = []
    
    logger = Logger("test", console=False)
    
    # Collect entries
    def collect_write(entry):
        entries.append(entry)
    logger._write_entry = collect_write
    
    # Log with data
    logger.info("User action", {"user_id": 123, "action": "login"})
    
    assert len(entries) == 1
    assert entries[0]["data"]["user_id"] == 123
    assert entries[0]["data"]["action"] == "login"
    
    print("✓ Logger with data test passed")


def test_global_logger():
    """Test global logger singleton."""
    logger1 = get_logger()
    logger2 = get_logger()
    
    assert logger1 is logger2
    assert logger1.name == "pinpoint"
    
    # Named logger should be different
    logger3 = get_logger("custom")
    assert logger3 is not logger1
    assert logger3.name == "custom"
    
    print("✓ Global logger test passed")


def test_json_store_basic():
    """Test basic JSON store operations."""
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        store_path = Path(temp_dir) / "test.json"
        store = JSONStore(store_path)
        
        # Initially doesn't exist
        assert not store.exists()
        
        # Save some data
        data = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}
        store.save(data)
        
        # Now exists
        assert store.exists()
        
        # Load data
        loaded = store.load()
        assert loaded == data
        
        print("✓ JSON store basic test passed")


def test_json_store_methods():
    """Test JSON store convenience methods."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        
        # Test get/set
        store.set("name", "Alice")
        assert store.get("name") == "Alice"
        assert store.get("missing", "default") == "default"
        
        # Test keys
        store.set("age", 30)
        keys = store.keys()
        assert "name" in keys
        assert "age" in keys
        
        # Test delete
        store.delete("age")
        assert "age" not in store.keys()
        
        # Test clear
        store.clear()
        assert store.load() == {}
        
        print("✓ JSON store methods test passed")


def test_json_store_error_handling():
    """Test JSON store error handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        
        # Write invalid JSON manually
        with open(store.path, 'w') as f:
            f.write("invalid json{")
        
        # Should raise StorageError
        try:
            store.load()
            assert False, "Should have raised StorageError"
        except StorageError as e:
            assert "Failed to parse JSON" in str(e)
            
        print("✓ JSON store error handling test passed")


def test_json_store_backup():
    """Test JSON store backup functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(Path(temp_dir) / "test.json")
        
        # Save some data
        store.save({"important": "data"})
        
        # Create backup
        backup_path = store.backup()
        assert backup_path.exists()
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        assert backup_data == {"important": "data"}
        
        print("✓ JSON store backup test passed")


def test_event_bus_with_logger():
    """Test EventBus with logger integration."""
    # Create a logger that collects entries
    entries = []
    
    class MockLogger:
        def debug(self, msg, data=None):
            entries.append(("debug", msg, data))
        def error(self, msg, data=None):
            entries.append(("error", msg, data))
    
    # Configure event bus with logger
    bus = configure_event_bus(debug=True, logger=MockLogger())
    
    # Subscribe and emit
    def handler(event):
        pass
    
    bus.subscribe("test.event", handler)
    bus.emit("test.event", {"value": 123})
    
    # Check logger was called
    assert len(entries) >= 2  # Subscribe and emit
    assert any("Subscribed" in e[1] for e in entries)
    assert any("Emitted" in e[1] for e in entries)
    
    print("✓ EventBus with logger test passed")


def test_logger_console_output(capsys=None):
    """Test logger console output."""
    logger = Logger("test", console=True)
    logger.info("Console test message")
    
    # Note: Can't easily capture print output in simple tests
    # This just verifies it doesn't crash
    print("✓ Logger console output test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 2 tests...")
    test_logger_basic()
    test_logger_levels()
    test_logger_with_data()
    test_global_logger()
    test_json_store_basic()
    test_json_store_methods()
    test_json_store_error_handling()
    test_json_store_backup()
    test_event_bus_with_logger()
    test_logger_console_output()
    print("\n✅ All Session 2 tests passed!")