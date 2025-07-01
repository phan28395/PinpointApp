# CLAUDE.md - PinPoint Architecture Redesign Plan

## Overview
PinPoint is a desktop application for creating floating widgets (tiles) that can be positioned anywhere on screen. This document outlines a pragmatic, step-by-step plan to refactor PinPoint from a monolithic application to a modular, extensible platform.

## 🎯 Core Principles (LEARNED FROM FIRST ATTEMPT)

### 1. Start Simple, Enhance Gradually
- Each session builds ONE thing that works
- No complex infrastructure until basics are solid
- Test infrastructure comes AFTER core functionality

### 2. Clear Dependencies
```
Layer 0: constants (no dependencies)
Layer 1: exceptions (uses constants only)
Layer 2: events (uses exceptions only)
Layer 3: logger (uses events only)
Layer 4: everything else
```

### 3. Import Structure (CRITICAL - READ THIS FIRST)
```
PROJECT ROOT: pinpoint/
WORKING DIRECTORY: Always run from pinpoint/

IMPORTS WITHIN PROJECT:
from core.events import EventBus     # ✓ CORRECT
from storage import StorageManager    # ✓ CORRECT
from pinpoint.core.events import ...  # ✗ WRONG

IMPORTS IN TESTS:
# Add at top of every test file:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Then import normally:
from core.events import EventBus
```

### 4. Testing Philosophy
- Start with 3-5 SIMPLE tests per component
- No test reports/infrastructure until Session 8
- Use plain `assert` statements first
- Complex test features are a luxury, not a necessity

## 📋 Architecture Goals (Simplified)
1. **Modular Design**: Reasonable file sizes (300-500 lines)
2. **Clear Dependencies**: No circular imports
3. **Plugin Ready**: Extensible but start simple
4. **Stable Core**: Don't break existing functionality
5. **Testable**: But don't over-engineer tests

## 🚀 Session Plan (Revised for Clarity)

### Session 1: Minimal Core Foundation
**Goal**: Create the absolute minimum working foundation

**Implementation Steps**:
- [x] Create `core/constants.py` - App constants (max 100 lines)
- [x] Create `core/exceptions.py` - Simple exceptions (max 100 lines)
- [x] Create `core/events.py` - Basic event bus (max 200 lines)
- [x] Create simple tests in `tests/test_session1_simple.py` (max 100 lines)

**Key Decisions**:
- EventBus has NO logger dependency (just print for debugging)
- Exceptions are simple classes, no fancy serialization yet
- Constants are just variables, no validation

**Test Requirements**:
```python
def test_event_bus_works():
    bus = EventBus()
    received = []
    bus.subscribe("test", lambda e: received.append(e))
    bus.emit("test", {})
    assert len(received) == 1

# That's it! 5-10 simple tests like this
```

**Deliverables**:
- Working event system
- Basic exceptions
- Simple constants
- 5-10 passing tests
- NO test reports, NO complex infrastructure

---

### Session 2: Add Logging & Storage Abstraction
**Goal**: Add logging and basic storage abstraction

**Implementation Steps**:
- [x] Create `core/logger.py` - Simple JSON logger (max 150 lines)
- [x] Create `data/base_store.py` - Abstract storage interface (max 100 lines)
- [x] Create `data/json_store.py` - JSON implementation (max 150 lines)
- [x] Update EventBus to optionally use logger
- [x] Create `tests/test_session2_simple.py` (max 150 lines)

**Key Decisions**:
- Logger is independent (doesn't use EventBus)
- Storage abstraction is minimal (just load/save)
- Still no complex test infrastructure

---

### Session 3: Refactor Tile Manager
**Goal**: Clean up tile manager using events and storage abstraction

**Implementation Steps**:
- [x] Create `core/tile_manager.py` - Using events & storage (max 300 lines)
- [x] Create `core/tile_registry.py` - Track tile types (max 150 lines)
- [x] Migrate existing tile functionality
- [x] Create `tests/test_session3_simple.py`

**Key Decisions**:
- Tile manager uses events for all state changes
- No UI dependencies in core
- Keep existing tile functionality working

---

### Session 4: Basic Plugin System
**Goal**: Minimal plugin system that works

**Implementation Steps**:
- [x] Create `plugins/base.py` - Simple plugin interface (max 100 lines)
- [x] Create `plugins/loader.py` - Basic loading (max 200 lines)
- [x] Create one example plugin
- [x] Create `tests/test_session4_simple.py`

**Key Decisions**:
- Plugins are just Python classes with a specific interface
- No sandboxing yet (trust plugins)
- No hot reloading (restart required)

---

### Session 5: Layout Management
**Goal**: Clean layout system using events

**Implementation Steps**:
- [x] Create `core/layout_manager.py` - Layout logic (max 250 lines)
- [x] Create `core/display_manager.py` - Display abstraction (max 200 lines)
- [x] Migrate existing layout functionality
- [x] Create `tests/test_session5_simple.py`

---

### Session 6: Design System Foundation
**Goal**: Separate visual design from logic

**Implementation Steps**:
- [x] Create `design/theme.py` - Basic theming (max 150 lines)
- [x] Create `design/components.py` - UI component registry (max 200 lines)
- [x] Update one tile type to use themes
- [x] Create `tests/test_session6_simple.py`

---

### Session 7: Error Handling
**Goal**: Proper error boundaries and recovery

**Implementation Steps**:
- [x] Create `core/error_boundary.py` - Catch tile errors (max 150 lines)
- [x] Update tile manager with error handling
- [x] Add recovery mechanisms
- [x] Create `tests/test_session7_simple.py`

---

### Session 8: Test Infrastructure (FINALLY!)
**Goal**: NOW we add proper test infrastructure

**Implementation Steps**:
- ☐ Create `tests/base_test.py` - Test base class with reporting
- ☐ Create `tests/runner.py` - Test runner with reports
- ☐ Update all existing tests to use new infrastructure
- ☐ Generate first comprehensive test report

---

### Session 9: Platform Support
**Goal**: Basic cross-platform compatibility

**Implementation Steps**:
- ☐ Create `platform/base.py` - Platform abstraction
- ☐ Create `platform/windows.py` - Windows specifics
- ☐ Create `platform/mac.py` - Mac specifics
- ☐ Update system tray and file paths

---

### Session 10: Integration & Polish
**Goal**: Tie everything together

**Implementation Steps**:
- ☐ Create `app/application.py` - Main app using all systems
- ☐ Update `main.py` to use new architecture
- ☐ Comprehensive integration tests
- ☐ Performance benchmarks
- ☐ Migration guide for users

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
├── platform/               # Platform support (Session 9)
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

## ✅ Success Metrics (Realistic)
- Each session's code works and passes tests
- No circular dependencies
- Existing functionality still works
- Can add new tile types easily (by Session 6)
- Tests are maintainable and fast

## 🛠️ Development Guidelines

### Before Each Session:
1. Read the session goals (keep them modest)
2. Check that previous session's code works
3. Don't add "nice to have" features

### During Each Session:
1. Write the simplest code that works
2. Test as you go with simple tests
3. Don't optimize prematurely
4. If it's getting complex, stop and simplify

### After Each Session:
1. Run the simple tests
2. Verify existing functionality works
3. Commit working code
4. Don't add complex infrastructure

## 🚨 Common Pitfalls to Avoid

1. **Over-engineering Early**: Don't add logging to EventBus in Session 1
2. **Complex Test Infrastructure**: Simple asserts until Session 8
3. **Circular Dependencies**: Check dependency layers
4. **Import Confusion**: Always work from pinpoint/ directory
5. **Feature Creep**: Stick to session goals

## 📝 Document Change Policy
Changes to this document require:
1. Clear justification in CHANGELOG.md
2. Approval based on actual implementation experience
3. Updates marked with [UPDATED: Session X - Date]

## 🎓 Lessons from Session 1

### What Went Wrong:
- Too much complexity in first session
- Test infrastructure before core was stable  
- Unclear import structure
- Circular dependency (EventBus → Logger)
- Weak reference tests with bound methods

### What We Learned:
- Start simpler than you think necessary
- Test infrastructure is not core functionality
- Clear import docs save hours of debugging
- Python quirks matter (weak refs + methods)
- Perfect is the enemy of good

### Key Insight:
**Build something that works, then make it better. Don't try to build the perfect system from day one.**