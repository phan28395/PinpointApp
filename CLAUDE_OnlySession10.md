# CLAUDE.md - PinPoint Architecture Refactor Guide

## 🎯 The One Rule
**"If it works, it's good enough. If it's simple, it's even better."**

This is a PRAGMATIC refactor. We're building something that works, not something perfect.

---

## 🏗️ Architecture Layers (Dependency Order)

### Layer 0: Constants
- Just data (colors, sizes, defaults)
- No imports from our code
- Anyone can import these

### Layer 1: Exceptions  
- Custom errors for better debugging
- Can only import from Layer 0
- Keep it simple - just error classes

### Layer 2: Events
- Event bus for loose coupling  
- Can import from Layers 0-1
- This is our communication backbone

### Layer 3: Logger & Utilities
- Logger is INDEPENDENT (no event bus import!)
- Helper functions that don't fit elsewhere
- Can import from Layers 0-1 only

### Layer 4: Everything Else
- Storage, Tiles, Plugins, Layouts, UI
- Can import from Layers 0-3
- These are the "business logic" components

---

## 📁 File Structure (Simplified)
```
pinpoint/                    # PROJECT ROOT - Always work from here
├── core/                    # Core systems (Sessions 1-3)
│   ├── __init__.py
│   ├── constants.py         # Layer 0: No dependencies
│   ├── exceptions.py        # Layer 1: Uses constants
│   ├── events.py           # Layer 2: Uses exceptions
│   ├── logger.py           # Layer 3: Independent
│   ├── tile_manager.py     # Layer 4: Uses all above
│   └── layout_manager.py   # Layer 4: Uses all above
├── data/                   # Data layer (Session 2)
│   ├── __init__.py
│   ├── base_store.py
│   └── json_store.py
├── plugins/                # Plugin system (Session 4)
│   ├── __init__.py
│   ├── base.py
│   └── loader.py
├── design/                 # Design system (Session 6)
│   ├── __init__.py
│   ├── theme.py
│   └── components.py
├── platform_support/       # Platform support (Session 9)
│   ├── __init__.py
│   ├── base.py
│   ├── windows.py
│   └── mac.py
├── tests/                  # Tests (start simple!)
│   ├── __init__.py
│   ├── test_session1_simple.py   # 5-10 basic tests
│   ├── test_session2_simple.py   # etc...
│   └── base_test.py              # Added in Session 8 only!
├── existing_files...       # All current PinPoint files
└── main.py
```

---

## 🧪 Testing Philosophy

### The Golden Rule
**Test the interface, not the implementation**

### For Sessions 1-9: Simple Unit Tests
- Use basic `assert` statements
- Test the happy path
- 5-10 tests per session
- Each test < 20 lines
- Example:
```python
def test_event_subscribe():
    bus = EventBus()
    received = []
    bus.subscribe("test", lambda data: received.append(data))
    bus.emit("test", {"value": 1})
    assert len(received) == 1
    assert received[0]["value"] == 1
```

### For Session 10: Accept Reality
Integration is different. When you're testing the whole system working together:
- Tests WILL be longer (50-100 lines is OK)
- Setup WILL be more complex
- You WILL need to manage state
- **This is normal and expected!**

---

## 📋 Session Implementation Steps

### Sessions 1-5: Core Foundation
**Goal**: Build the essential pieces

### Session 1: Event System
- [x] Create event bus for component communication
- [x] No complex features - just subscribe/emit
- [x] Simple tests with assert

### Session 2: Storage & Logging  
- [x] JSON file storage with simple interface
- [x] Basic logger (no event bus dependency!)
- [x] Test file operations work

### Session 3: Tile Management
- [x] Tile manager using events and storage
- [x] Tile registry for tile types
- [x] Test CRUD operations

### Session 4: Plugin System
- [x] Basic plugin loader
- [x] Plugin interface definition
- [x] Test plugin discovery

### Session 5: Layout Management
- [x] Layout manager for tile arrangements
- [x] Display manager for monitors
- [x] Test layout operations

### Sessions 6-9: Enhancements

### Session 6: Design System
- [x] Theme management (dark/light/high-contrast)
- [x] Component style registry
- [x] Test theme switching

### Session 7: Error Handling
- [x] Error boundaries for resilience
- [x] Recovery strategies
- [x] Test error recovery

### Session 8: Test Infrastructure
- [x] NOW we add proper test framework
- [x] Test runner with reports
- [x] Keep using for remaining sessions

### Session 9: Platform Support
- [x] Cross-platform file paths
- [x] OS-specific features
- [x] Test on current platform only

### Session 10: Integration & Polish
**Goal**: Tie everything together - KEEP IT SIMPLE!

**Implementation Steps**:
- [ ] Create `app/application.py` - Main app using all systems
- [ ] Update `main.py` to use new architecture
- [ ] Write 3-5 integration tests that verify the app works
- [ ] Create simple migration guide

**What IS Session 10**:
- A `PinPointApplication` class that initializes all components
- A few methods to coordinate between systems
- Basic lifecycle management (init, run, shutdown)
- 300-500 lines of integration code

**What IS NOT Session 10**:
- A complex orchestration framework
- Elaborate configuration system  
- Fancy dependency injection
- Perfect test coverage

**Integration Test Approach**:
Since integration tests are naturally more complex, embrace it:

```python
# tests/test_session10_simple.py (if not using test framework)
# OR tests/test_session10_integration.py (if using test framework)

def test_app_creates_tile():
    """Test that the app can create and retrieve a tile."""
    # Setup - Yes, this is more complex than unit tests
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create app
        from app import PinPointApplication
        app = PinPointApplication(config_path=Path(temp_dir))
        app.initialize()
        
        # Test
        tile_id = app.tile_manager.create_tile("note", content="Hello")
        tile = app.tile_manager.get_tile(tile_id)
        assert tile is not None
        assert tile["content"] == "Hello"
        
        # Verify it persisted
        app2 = PinPointApplication(config_path=Path(temp_dir))
        app2.initialize()
        tile2 = app2.tile_manager.get_tile(tile_id)
        assert tile2 is not None
        
    finally:
        # Cleanup - Yes, we need this
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Reset singletons if needed
        
# THAT'S OK! Integration tests are supposed to be like this!
```

---

## 🎯 Success Metrics (Realistic)
- Each session's code works and passes tests
- No circular dependencies
- Existing functionality still works
- Can add new tile types easily (by Session 6)
- Tests are maintainable and fast

---

## 🚨 Common Pitfalls to Avoid

1. **Over-architecting**: We're refactoring, not rewriting from scratch
2. **Test paralysis**: If it's too hard to test, simplify the code
3. **Scope creep**: Each session has specific goals - stick to them
4. **Premature optimization**: Make it work first, fast later
5. **Framework envy**: This is a desktop app, not a web service

### The Import Problem
Always use this pattern to avoid import errors:
```python
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now import our modules
from core.events import get_event_bus
```

---

## 💡 Design Decisions

### Why Singletons?
- Desktop app = one instance of each manager
- Simple access pattern: `get_thing()`
- Easy to reset for testing (add reset methods in Session 10)

### Why Events?
- Decouple UI from business logic
- Easy to add new features without changing core
- Natural fit for user interactions

### Why Simple Tests?
- Complex tests break easily
- Hard to understand = hard to maintain  
- We need confidence, not coverage metrics

---

## 📝 Quick Patterns

### Creating a Manager (Layer 4)
```python
class ThingManager:
    def __init__(self, store: BaseStore):
        self.store = store
        self.logger = get_logger()
        self.event_bus = get_event_bus()
        
    def create_thing(self, data):
        # Validate
        if not data.get("name"):
            raise ValidationError("Name required")
            
        # Create
        thing = {"id": str(uuid.uuid4()), **data}
        
        # Save
        self.store.set(f"thing:{thing['id']}", thing)
        
        # Notify
        self.event_bus.emit("thing:created", thing)
        
        return thing["id"]
```

### Testing a Manager
```python
def test_create_thing():
    # Setup
    store = JSONStore(":memory:")  # In-memory for tests
    manager = ThingManager(store)
    
    # Test
    thing_id = manager.create_thing({"name": "Test"})
    assert thing_id is not None
    
    # Verify
    thing = store.get(f"thing:{thing_id}")
    assert thing["name"] == "Test"
```

---

## 🎉 Remember

We're 90% done! Session 10 is just putting the pieces together. If integration tests feel complex, that's because integration IS complex. The architecture is working great - don't let test complexity discourage you.

**Done is better than perfect!**