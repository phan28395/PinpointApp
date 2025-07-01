# CLAUDE.md - PinPoint Architecture Redesign Plan

## Overview
PinPoint is a desktop application for creating floating widgets (tiles) that can be positioned anywhere on screen. The current implementation needs refactoring to separate tile logic from visual design, enabling third-party designers to create custom tile.
This document outlines a step-by-step plan to redesign PinPoint's architecture from a showcase application to a production-ready, extensible platform. The focus is on building a solid foundation that can be extended without major rewrites.

## Document Change Policy
This file (CLAUDE.md) should remain stable throughout development. However, changes are permitted under these conditions:
1. **Critical architectural discoveries** that make the current plan unworkable
2. **Security vulnerabilities** discovered in the planned approach
3. **Platform limitations** that require architectural adjustments
4. **Performance bottlenecks** that necessitate design changes

### How to Update This Document
If changes are necessary:
1. Document in CHANGELOG.md:
   - The exact change needed
   - Clear justification
   - Impact on future sessions
2. Update CLAUDE.md with:
   - `[UPDATED: Session X - Date]` marker
   - Brief reason in parentheses
   - The specific changes

## Architecture Goals
1. **Modular Design**: No file exceeds 500 lines
2. **Separation of Concerns**: Complete separation of logic and visual design
3. **Plugin Architecture**: Safe, extensible plugin system
4. **Performance**: Responsive with 50+ tiles
5. **Cross-Platform**: Windows/Mac primary
6. **Backward Compatibility**: Existing data and plugins continue to work
7. **Extensibility**: New features without core changes
8. **Debuggability**: Clear event flow with comprehensive logging

## Session Plan

### Session 1: Core Foundation & Event System
**Goal**: Strip down to minimal core with robust event system

**Implementation Steps**:
- ☐ Create `core/events.py` - Central event bus (max 200 lines)
- ☐ Create `core/logger.py` - Structured logging system (max 150 lines)
- ☐ Create `core/exceptions.py` - Custom exceptions with error codes (max 100 lines)
- ☐ Refactor `tile_manager.py` → `core/tile_manager.py` (max 300 lines)
- ☐ Create `core/constants.py` - All app constants (max 100 lines)

**Test Requirements**:
- Event bus message passing
- Logger output verification
- Exception handling
- Basic tile manager operations

**Deliverables**:
- Working event system
- Centralized logging
- Clean tile manager
- Test file: `tests/test_session1.py`
- Git commit: `refactor: establish core foundation with event system and logging`

---

### Session 2: Basic Plugin System
**Goal**: Implement simple, extensible plugin system

**Implementation Steps**:
- ☐ Create `plugins/base_plugin.py` - Abstract plugin interface (max 150 lines)
- ☐ Create `plugins/plugin_loader.py` - Safe dynamic loading (max 250 lines)
- ☐ Create `plugins/plugin_manifest.py` - Plugin metadata spec (max 100 lines)
- ☐ Create `plugins/plugin_api.py` - Limited API for plugins (max 200 lines)
- ☐ Update existing plugins to use new system

**Test Requirements**:
- Plugin loading/unloading
- Basic permission checking
- API access control
- Plugin manifest validation

**Deliverables**:
- Working plugin system
- Plugin API documentation
- Example plugin using new system
- Test file: `tests/test_session2.py`
- Git commit: `feat: implement basic plugin architecture`

---

### Session 3: Data Layer Separation
**Goal**: Abstract all data operations for future flexibility

**Implementation Steps**:
- ☐ Create `data/base_store.py` - Abstract data interface (max 100 lines)
- ☐ Create `data/tile_store.py` - Tile data operations (max 200 lines)
- ☐ Create `data/layout_store.py` - Layout data operations (max 200 lines)
- ☐ Create `data/settings_store.py` - Settings management (max 150 lines)
- ☐ Create `data/migrations.py` - Data migration system (max 200 lines)

**Test Requirements**:
- CRUD operations
- Data migration from current format
- Concurrent access handling
- Data validation

**Deliverables**:
- Abstracted data layer
- Working migrations
- No direct file access in other modules
- Test file: `tests/test_session3.py`
- Git commit: `refactor: separate data layer with migration support`

---

### Session 4: Visual Design Separation
**Goal**: Complete separation of visual design from logic

**Implementation Steps**:
- ☐ Create `design/theme_engine.py` - Theme processing (max 250 lines)
- ☐ Create `design/component_registry.py` - UI component catalog (max 200 lines)
- ☐ Create `design/style_validator.py` - Design validation (max 150 lines)
- ☐ Create `design/design_tokens.py` - Design constraints (max 100 lines)
- ☐ Refactor existing tiles to use component registry

**Test Requirements**:
- Theme application
- Component registration
- Style validation
- Design token enforcement

**Deliverables**:
- Working theme system
- Component registry with base components
- Design token system
- Test file: `tests/test_session4.py`
- Git commit: `feat: implement visual design separation`

---

### Session 5: Error Handling & Recovery
**Goal**: Robust error boundaries and recovery mechanisms

**Implementation Steps**:
- ☐ Create `core/error_boundary.py` - Error isolation (max 200 lines)
- ☐ Create `core/tile_supervisor.py` - Tile health monitoring (max 250 lines)
- ☐ Create `core/recovery.py` - Auto-recovery mechanisms (max 150 lines)
- ☐ Update tile lifecycle for error handling
- ☐ Add health checks to tile manager

**Test Requirements**:
- Error isolation between tiles
- Automatic recovery
- Health monitoring
- Graceful degradation

**Deliverables**:
- Error boundary system
- Tile supervision
- Recovery mechanisms
- Test file: `tests/test_session5.py`
- Git commit: `feat: implement error handling and recovery`

---

### Session 6: Performance Foundation
**Goal**: Basic performance monitoring and optimization

**Implementation Steps**:
- ☐ Create `performance/monitor.py` - Performance metrics (max 200 lines)
- ☐ Create `performance/lazy_loader.py` - Lazy loading system (max 150 lines)
- ☐ Create `performance/throttle.py` - Update throttling (max 150 lines)
- ☐ Add performance hooks to tile lifecycle
- ☐ Implement basic lazy loading

**Test Requirements**:
- Performance metric collection
- Lazy loading functionality
- Update throttling
- Memory usage tracking

**Deliverables**:
- Performance monitoring
- Basic optimizations
- Performance dashboard data
- Test file: `tests/test_session6.py`
- Git commit: `perf: add performance monitoring and basic optimizations`

---

### Session 7: Plugin Templates
**Goal**: Make plugin development accessible

**Implementation Steps**:
- ☐ Create `tools/plugin_templates.py` - Plugin boilerplates (max 200 lines)
- ☐ Create `tools/template_generator.py` - Template engine (max 150 lines)
- ☐ Create templates for common plugin types
- ☐ Create `docs/plugin_development.md` - Developer guide
- ☐ Create example plugins from templates

**Test Requirements**:
- Template generation
- Template validation
- Generated plugin functionality
- Documentation completeness

**Deliverables**:
- Plugin templates
- Template generator
- Developer documentation
- Example plugins
- Test file: `tests/test_session7.py`
- Git commit: `feat: add plugin development templates`

---

### Session 8: Platform Compatibility
**Goal**: Basic cross-platform support

**Implementation Steps**:
- ☐ Create `platform/platform_utils.py` - Platform detection (max 150 lines)
- ☐ Create `platform/path_utils.py` - Path handling (max 100 lines)
- ☐ Create `platform/system_tray.py` - Tray abstraction (max 200 lines)
- ☐ Update file operations for cross-platform
- ☐ Test on Windows and Mac

**Test Requirements**:
- Platform detection
- Path handling across OS
- System tray functionality
- File operations

**Deliverables**:
- Cross-platform utilities
- Working on Windows/Mac
- Platform-specific documentation
- Test file: `tests/test_session8.py`
- Git commit: `feat: add cross-platform compatibility`

---

### Session 9: Backward Compatibility
**Goal**: Ensure smooth migration from current version

**Implementation Steps**:
- ☐ Create `compat/legacy_data.py` - Old format readers (max 200 lines)
- ☐ Create `compat/migration_engine.py` - Auto-migration (max 250 lines)
- ☐ Create `compat/plugin_adapter.py` - Legacy plugin support (max 150 lines)
- ☐ Add compatibility tests with real user data
- ☐ Create migration guide

**Test Requirements**:
- Load old data formats
- Plugin compatibility
- Data integrity after migration
- No data loss

**Deliverables**:
- Working migration system
- Legacy support
- Migration documentation
- Test file: `tests/test_session9.py`
- Git commit: `feat: add backward compatibility layer`

---

### Session 10: Integration & Polish
**Goal**: Integrate all components into cohesive system

**Implementation Steps**:
- ☐ Create `app/application.py` - Main app orchestration (max 300 lines)
- ☐ Create `app/config.py` - Configuration management (max 150 lines)
- ☐ Update `main.py` to use new architecture (max 50 lines)
- ☐ Update UI components to use new systems
- ☐ Create integration tests

**Test Requirements**:
- End-to-end workflows
- All systems integration
- Performance benchmarks
- User acceptance scenarios

**Deliverables**:
- Fully integrated application
- Configuration system
- Complete test suite
- Test file: `tests/test_integration.py`
- Git commit: `feat: complete architecture redesign integration`

---

## File Structure After Redesign
```
pinpoint/
├── core/
│   ├── __init__.py
│   ├── events.py
│   ├── logger.py
│   ├── exceptions.py
│   ├── tile_manager.py
│   ├── constants.py
│   ├── error_boundary.py
│   ├── tile_supervisor.py
│   └── recovery.py
├── plugins/
│   ├── __init__.py
│   ├── base_plugin.py
│   ├── plugin_loader.py
│   ├── plugin_manifest.py
│   └── plugin_api.py
├── data/
│   ├── __init__.py
│   ├── base_store.py
│   ├── tile_store.py
│   ├── layout_store.py
│   ├── settings_store.py
│   └── migrations.py
├── design/
│   ├── __init__.py
│   ├── theme_engine.py
│   ├── component_registry.py
│   ├── style_validator.py
│   └── design_tokens.py
├── performance/
│   ├── __init__.py
│   ├── monitor.py
│   ├── lazy_loader.py
│   └── throttle.py
├── tools/
│   ├── __init__.py
│   ├── plugin_templates.py
│   └── template_generator.py
├── platform/
│   ├── __init__.py
│   ├── platform_utils.py
│   ├── path_utils.py
│   └── system_tray.py
├── compat/
│   ├── __init__.py
│   ├── legacy_data.py
│   ├── migration_engine.py
│   └── plugin_adapter.py
├── app/
│   ├── __init__.py
│   ├── application.py
│   └── config.py
├── tests/
│   └── (test files for each session)
└── main.py
```

## Success Metrics
- No file exceeds 500 lines
- Clean separation of concerns
- All existing functionality preserved
- Plugin development time < 30 minutes
- Zero crashes from plugin failures
- Smooth migration from current version

## Session Guidelines

**Before Each Session**:
- Review the session goals
- Ensure previous session's tests pass
- Create feature branch if needed

**During Each Session**:
- Follow line count limits flexibly (if it is challenging to limit under 500 lines count then it is totally fine to exceed the limit)
- Write tests alongside implementation
- Document design decisions in code
- Keep user functionality working

**After Each Session**:
- Run all tests (current and previous)
- Test overall strategy should be simple "smoke test" that ensures nothing breaks as you progress
- Update CHANGELOG.md with:
  - Completed tasks
  - Any deviations and reasons
  - Known issues
  - Next session prep notes
- Commit with specified message
- Merge to main branch if stable

## Future Extension Points
This foundation specifically enables these future additions without major changes:
- **AI Plugin Generation**: Add AI templates to template system
- **Visual Plugin Builder**: New tool using plugin templates
- **Process Isolation**: Upgrade error boundaries to full isolation
- **Advanced Performance**: Extend monitoring with optimization
- **Linux Support**: Add to platform utils
- **Plugin Marketplace**: Add to plugin manifest and API
- **Design Marketplace**: Extend theme engine
- **Real-time Collaboration**: Hook into event system

The architecture is intentionally kept simple to allow these extensions through addition, not modification.