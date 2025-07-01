# CHANGELOG.md - PinPoint Architecture Refactor

All notable changes to the PinPoint architecture refactor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Session 1: Minimal Core Foundation - 2025-01-07

#### Added
- **Core Module Structure**
  - `core/constants.py` - Application-wide constants with no dependencies (62 lines)
  - `core/exceptions.py` - Custom exception hierarchy (59 lines)
  - `core/events.py` - Basic event bus implementation (157 lines)
  - `core/__init__.py` - Module exports (41 lines)

- **Testing Foundation**
  - `tests/test_session1_simple.py` - Simple tests using assert statements (195 lines)
  - 10 basic test functions covering all core functionality
  - No complex test infrastructure as per guidelines

- **Key Features Implemented**
  - Event bus with subscribe/unsubscribe/emit functionality
  - Weak reference support for callbacks (with documented limitations)
  - Global event bus singleton via `get_event_bus()`
  - Exception hierarchy: PinPointError → TileError, LayoutError, StorageError, PluginError, ValidationError
  - Debug mode for EventBus (prints instead of logging)
  - Error isolation in event callbacks

#### Design Decisions
- **No Logger Dependency**: EventBus uses optional debug prints to avoid circular dependencies
- **Simple Testing**: Plain assert statements instead of test framework
- **Weak References**: Used in EventBus but won't work with bound methods directly
- **Constants Layer**: Pure data, no logic or dependencies
- **Exception Context**: Each exception type can carry relevant contextual data

#### Known Limitations
- Weak references in EventBus don't work with bound methods (e.g., `self.method`)
- No persistence for event subscriptions
- No event prioritization or ordering guarantees
- No async event support

#### Metrics
- Total lines of code: 514
- Test coverage: All public APIs tested
- Dependencies: None (Layer 0-2 complete)
- Import structure: Clean, no circular dependencies

#### Next Steps
- Session 2: Add logging and storage abstraction
- Session 3: Refactor tile manager using events
- Session 4: Basic plugin system

---

## Architecture Refactor Guidelines

### Version Numbering
- Sessions 1-5: v2.0.0-alpha.1 through v2.0.0-alpha.5
- Sessions 6-10: v2.0.0-beta.1 through v2.0.0-beta.5
- Final release: v2.0.0

### Change Categories
- **Added**: New features or modules
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

### Documentation Standards
- Document line counts for each file
- Note key design decisions
- List known limitations
- Include metrics for each session
- Reference CLAUDE.md for architectural decisions

### Review Process
- Each session's changes must be tested before documentation
- Line counts should stay within CLAUDE.md guidelines
- Dependencies must follow the defined layers
- All tests must pass before marking session complete