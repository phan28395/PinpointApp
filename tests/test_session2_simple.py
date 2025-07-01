# tests/test_session2_updated.py
"""
Updated tests for Session 2 components using test infrastructure.
Tests logger and storage abstraction.
"""

import sys
from pathlib import Path
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base_test import BaseTest
from core.logger import Logger, LogLevel, get_logger, configure_global_logger
from core.events import EventBus, configure_event_bus
from data.json_store import JSONStore
from core.exceptions import StorageError


class TestSession2Logger(BaseTest):
    """Test suite for Logger functionality."""
    
    def setup(self):
        """Setup for logger tests."""
        self.temp_files = []
        
    def teardown(self):
        """Cleanup temporary files."""
        for f in self.temp_files:
            if f.exists():
                f.unlink()
                
    def test_logger_basic(self):
        """Test basic logger functionality."""
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = Path(f.name)
            self.temp_files.append(log_file)
        
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
        self.assert_equal(len(lines), 4)
        
        # Check each line is valid JSON
        for line in lines:
            entry = json.loads(line)
            self.assert_in("timestamp", entry)
            self.assert_in("logger", entry)
            self.assert_in("level", entry)
            self.assert_in("message", entry)

    def test_logger_levels(self):
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
        self.assert_equal(len(entries), 2)
        self.assert_equal(entries[0]["level"], "WARNING")
        self.assert_equal(entries[1]["level"], "ERROR")

    def test_logger_with_data(self):
        """Test logging with structured data."""
        entries = []
        
        logger = Logger("test", console=False)
        
        # Collect entries
        def collect_write(entry):
            entries.append(entry)
        logger._write_entry = collect_write
        
        # Log with data
        logger.info("User action", {"user_id": 123, "action": "login"})
        
        self.assert_equal(len(entries), 1)
        self.assert_equal(entries[0]["data"]["user_id"], 123)
        self.assert_equal(entries[0]["data"]["action"], "login")

    def test_global_logger(self):
        """Test global logger singleton."""
        logger1 = get_logger()
        logger2 = get_logger()
        
        self.assert_true(logger1 is logger2)
        self.assert_equal(logger1.name, "pinpoint")
        
        # Named logger should be different
        logger3 = get_logger("custom")
        self.assert_false(logger3 is logger1)
        self.assert_equal(logger3.name, "custom")


class TestSession2Storage(BaseTest):
    """Test suite for Storage abstraction."""
    
    def setup(self):
        """Setup for storage tests."""
        self.temp_dirs = []
        
    def teardown(self):
        """Cleanup temporary directories."""
        for d in self.temp_dirs:
            if d.exists():
                shutil.rmtree(d)
                
    def create_temp_dir(self):
        """Create a temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_dirs.append(temp_dir)
        return temp_dir
        
    def test_json_store_basic(self):
        """Test basic JSON store operations."""
        temp_dir = self.create_temp_dir()
        store_path = temp_dir / "test.json"
        store = JSONStore(store_path)
        
        # Initially doesn't exist
        self.assert_false(store.exists())
        
        # Save some data
        data = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}
        store.save(data)
        
        # Now exists
        self.assert_true(store.exists())
        
        # Load data
        loaded = store.load()
        self.assert_equal(loaded, data)

    def test_json_store_methods(self):
        """Test JSON store convenience methods."""
        temp_dir = self.create_temp_dir()
        store = JSONStore(temp_dir / "test.json")
        
        # Test get/set
        store.set("name", "Alice")
        self.assert_equal(store.get("name"), "Alice")
        self.assert_equal(store.get("missing", "default"), "default")
        
        # Test keys
        store.set("age", 30)
        keys = store.keys()
        self.assert_in("name", keys)
        self.assert_in("age", keys)
        
        # Test delete
        store.delete("age")
        self.assert_not_in("age", store.keys())
        
        # Test clear
        store.clear()
        self.assert_equal(store.load(), {})

    def test_json_store_error_handling(self):
        """Test JSON store error handling."""
        temp_dir = self.create_temp_dir()
        store = JSONStore(temp_dir / "test.json")
        
        # Write invalid JSON manually
        with open(store.path, 'w') as f:
            f.write("invalid json{")
        
        # Should raise StorageError
        self.assert_raises(StorageError, store.load)

    def test_json_store_backup(self):
        """Test JSON store backup functionality."""
        temp_dir = self.create_temp_dir()
        store = JSONStore(temp_dir / "test.json")
        
        # Save some data
        store.save({"important": "data"})
        
        # Create backup
        backup_path = store.backup()
        self.assert_true(backup_path.exists())
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        self.assert_equal(backup_data, {"important": "data"})

    def test_event_bus_with_logger(self):
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
        self.assert_greater(len(entries), 1)  # At least subscribe and emit
        
        # Check for expected log messages
        log_messages = [e[1] for e in entries]
        self.assert_true(any("Subscribed" in msg for msg in log_messages))
        self.assert_true(any("Emitted" in msg for msg in log_messages))