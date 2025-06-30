# PinPoint Refactoring Guide

## Project Overview
PinPoint is a desktop application for creating floating widgets (tiles) that can be positioned anywhere on screen. The current implementation needs refactoring to separate tile logic from visual design, enabling third-party designers to create custom tile appearances without touching the code.

## Architecture Goals
1. **Separation of Concerns**: Tile logic must be completely separate from visual presentation
2. **Design System**: Implement a centralized design system with consistent tokens
3. **Plugin Architecture**: Support for third-party tile types and designs
4. **Design Constraints**: Enforce rules to ensure tiles remain functional regardless of design
5. **JSON-based Designs**: Visual designs defined in JSON files that can be created without coding

## Current State Analysis
- ✅ Basic plugin system exists (plugin_registry.py)
- ✅ Design system foundation present (design_system.py)
- ✅ Tile manager supports design concepts
- ⚠️ NoteTile still has embedded UI code
- ⚠️ Design validation not fully implemented
- ⚠️ No design editor/preview system
- ⚠️ Limited design documentation

## Implementation Checklist

### Phase 1: Core Architecture Refactoring
- [ ] **1.1 Complete Logic/UI Separation for NoteTile**
  - [ ] Extract all QTextEdit creation/styling from NoteTile class
  - [ ] Move UI creation to design spec renderer in BaseTile
  - [ ] Ensure NoteTileLogic handles all business logic without Qt dependencies
  - [ ] Test that NoteTile works with both embedded and external designs
  - [ ] Document the separation pattern for other developers

- [ ] **1.2 Enhance BaseTile Design Rendering**
  - [ ] Implement full component type support (all ComponentType enum values)
  - [ ] Add layout managers (vertical, horizontal, grid, absolute)
  - [ ] Implement component property binding to tile data
  - [ ] Add event handler mapping (component actions → tile methods)
  - [ ] Create component factory with extensibility

- [ ] **1.3 Strengthen Design Constraints System**
  - [ ] Implement size constraint validation in design renderer
  - [ ] Add required component validation
  - [ ] Create component nesting depth checker
  - [ ] Implement design compatibility version checking
  - [ ] Add meaningful error messages for constraint violations

### Phase 2: Design System Enhancement
- [ ] **2.1 Expand Design System Components**
  - [ ] Add remaining component styles (combo_box, slider, progress, etc.)
  - [ ] Implement theme inheritance and overrides
  - [ ] Add responsive sizing tokens (relative units)
  - [ ] Create component state styles (hover, active, disabled, focused)
  - [ ] Document all design tokens with examples

- [ ] **2.2 Create Design Validation Framework**
  - [ ] Build comprehensive JSON schema for design specs
  - [ ] Implement schema validation with detailed error reporting
  - [ ] Add visual regression testing for designs
  - [ ] Create design linting rules
  - [ ] Build automated design documentation generator

- [ ] **2.3 Implement Dynamic Styling Engine**
  - [ ] Create style calculator for dynamic properties
  - [ ] Add support for design variables and expressions
  - [ ] Implement conditional styling based on tile state
  - [ ] Add animation/transition support
  - [ ] Create style inheritance resolver

### Phase 3: Plugin System Enhancement
- [ ] **3.1 Refactor Existing Plugins**
  - [ ] Update clock_plugin.py with proper implementation
  - [ ] Update weather_plugin.py with proper implementation
  - [ ] Update todo_plugin.py with proper implementation
  - [ ] Create at least 2 designs for each plugin type
  - [ ] Document plugin creation process

- [ ] **3.2 Plugin Discovery and Loading**
  - [ ] Implement hot-reload for plugin development
  - [ ] Add plugin dependency management
  - [ ] Create plugin marketplace infrastructure
  - [ ] Implement plugin signing/verification
  - [ ] Add plugin settings persistence

- [ ] **3.3 Design Loading and Management**
  - [ ] Implement design hot-reload for development
  - [ ] Create design preview system
  - [ ] Add design favorites/collections
  - [ ] Implement per-tile design overrides
  - [ ] Create design migration system for updates

### Phase 4: Designer Tools
- [ ] **4.1 Design Preview System**
  - [ ] Create standalone design preview window
  - [ ] Add live reload on design file changes
  - [ ] Implement mock data for preview
  - [ ] Add design validation in preview
  - [ ] Create screenshot/export functionality

- [ ] **4.2 Design Editor (Basic)**
  - [ ] Create JSON editor with syntax highlighting
  - [ ] Add design token autocomplete
  - [ ] Implement component picker
  - [ ] Add property inspector
  - [ ] Create design templates

- [ ] **4.3 Visual Design Editor (Advanced)**
  - [ ] Implement drag-and-drop component placement
  - [ ] Add visual property editors
  - [ ] Create alignment/distribution tools
  - [ ] Implement component hierarchy view
  - [ ] Add undo/redo functionality

### Phase 5: Example Implementations
- [ ] **5.1 Create Example Tile Types**
  - [ ] Timer tile with countdown functionality
  - [ ] Image viewer tile with slideshow
  - [ ] System monitor tile (CPU, RAM, etc.)
  - [ ] Sticky note tile with categories
  - [ ] Calculator tile with history

- [ ] **5.2 Create Example Designs**
  - [ ] Minimalist design pack (5+ designs)
  - [ ] Glass/transparent design pack
  - [ ] Neon/cyberpunk design pack
  - [ ] Paper/skeuomorphic design pack
  - [ ] Create design showcase in main window

- [ ] **5.3 Third-party Design Examples**
  - [ ] Create external design repository structure
  - [ ] Build example third-party design pack
  - [ ] Document design submission process
  - [ ] Create design quality guidelines
  - [ ] Implement user design sharing

### Phase 6: Testing and Documentation
- [ ] **6.1 Testing Infrastructure**
  - [ ] Unit tests for logic/UI separation
  - [ ] Integration tests for design loading
  - [ ] Visual regression tests for designs
  - [ ] Performance tests for complex designs
  - [ ] Accessibility tests for all components

- [ ] **6.2 Developer Documentation**
  - [ ] Plugin development guide
  - [ ] Design creation guide
  - [ ] API reference documentation
  - [ ] Architecture diagrams
  - [ ] Example code snippets

- [ ] **6.3 Designer Documentation**
  - [ ] Design system reference
  - [ ] Component catalog with examples
  - [ ] Best practices guide
  - [ ] Troubleshooting guide
  - [ ] Video tutorials

### Phase 7: Migration and Deployment
- [ ] **7.1 Data Migration**
  - [ ] Create migration for existing tile data
  - [ ] Build design migration utilities
  - [ ] Test backward compatibility
  - [ ] Create rollback procedures
  - [ ] Document migration process

- [ ] **7.2 Release Preparation**
  - [ ] Create installer with design packs
  - [ ] Build auto-update system
  - [ ] Create design marketplace client
  - [ ] Implement telemetry (opt-in)
  - [ ] Prepare marketing materials

## Change Documentation Protocol

### IMPORTANT: After Every Code Change
When implementing any checklist item, Claude MUST provide:

1. **File Change Summary**
```markdown
### Files Changed:
- **Modified**: `filename.py` - Brief description of changes
- **Created**: `new_file.py` - Purpose of new file
- **Renamed**: `old.py` → `new.py` - Reason for rename
- **Deleted**: `removed.py` - Why it was removed
```

2. **Breaking Changes Alert**
```markdown
### Breaking Changes:
- Import path changes
- API modifications
- Data structure updates
- Required migration steps
```

3. **Update Instructions**
```markdown
### To Apply These Changes:
1. Save the provided code to [filename]
2. Update imports in [affected files]
3. Run tests to verify
4. Update the checklist item as complete
```

4. **Session Log Entry**
```markdown
### Session Log Entry:
**Date**: [Current Date]
**Phase**: [Current Phase]
**Completed**: [What was accomplished]
**Next Steps**: [What to do next]
**Notes**: [Any important observations]
```

### Example Change Documentation
After implementing Phase 1.1, Claude should provide:

```markdown
## Changes Applied - Phase 1.1

### Files Changed:
- **Modified**: `note_tile.py` - Removed UI code, now uses NoteTileLogic
- **Modified**: `base_tile.py` - Added render_design_spec() method
- **Created**: `note_tile_logic.py` - Extracted business logic
- **Modified**: `note_editor_widget.py` - Updated to use NoteTileLogic

### Breaking Changes:
- NoteTile no longer creates QTextEdit directly
- UI customization must use design specs
- Import `NoteTileLogic` for logic-only access

### To Apply These Changes:
1. Save all provided files
2. Update any custom note tile extensions
3. Test note creation and editing
4. Mark Phase 1.1 as complete in checklist

### Session Log Entry:
**Date**: 2024-XX-XX
**Phase**: 1.1 - Logic/UI Separation
**Completed**: Separated NoteTile logic from presentation
**Next Steps**: Begin Phase 1.2 - Enhance BaseTile Design Rendering
**Notes**: All tests passing, ready for design system work
```

## File Change Log

### Recent Changes (Last 3 Sessions)
[Keep only recent changes here for quick reference]

### Complete Change History
See `CHANGELOG.md` in the project root for full file change history.
See `SESSION_NOTES.md` for detailed session-by-session implementation notes.

## Implementation Notes

### Priority Order
1. Start with Phase 1 - Core architecture is critical
2. Phase 2 and 3 can be worked on in parallel
3. Phase 4 can begin after Phase 1 is complete
4. Phase 5 should wait until Phase 3 is done
5. Phase 6 is ongoing throughout development
6. Phase 7 is final preparation

### Key Files to Modify
1. `note_tile.py` - Remove all UI code
2. `base_tile.py` - Enhance design rendering
3. `plugin_registry.py` - Add design validation
4. `design_system.py` - Expand component library
5. Create new: `design_validator.py`, `design_renderer.py`, `design_editor.py`

### Breaking Changes
- Tile data structure will change (add design_spec field)
- Plugin API will be extended (not broken)
- Storage format will need migration
- Some custom user modifications may break

### Success Criteria
- Designers can create new tile appearances without coding
- All tile types work with any valid design
- Performance remains good with complex designs
- Third-party designs can be easily installed
- Design creation is well-documented

## Current Session Progress
- Session started: [Date]
- Last checkpoint: Initial analysis complete
- Next step: Begin Phase 1.1 - Complete Logic/UI Separation for NoteTile

## Notes for Next Session
When continuing this refactoring:
1. Check the current state of the codebase
2. Review `CHANGELOG.md` for complete file change history
3. Review `SESSION_NOTES.md` for implementation details and decisions
4. Check completed items in this checklist
5. Continue with the next unchecked item
6. Update progress after each completed task
7. Document changes in both Claude.md (recent) and CHANGELOG.md (complete)

## Instructions for Claude

### Your Responsibilities
1. **Before Making Changes**: 
   - Review the Recent Changes section below
   - Check `CHANGELOG.md` if you need older change history
   - Check `SESSION_NOTES.md` for implementation context
2. **During Implementation**: Track all file modifications
3. **After Each Change**: 
   - Provide complete change documentation (see protocol above)
   - Update the Recent Changes section in Claude.md
   - Provide entry for CHANGELOG.md
4. **End of Session**: 
   - Update Recent Changes in Claude.md
   - Provide complete session summary for CHANGELOG.md
   - Provide detailed notes for SESSION_NOTES.md

### Where to Document Changes

1. **Claude.md** (this file):
   - Recent changes (last 3 sessions)
   - Current session progress
   - Quick reference for active work

2. **CHANGELOG.md** (separate file):
   ```markdown
   # Complete file change history
   # Format: Session-by-session breakdown
   # Include: Files changed, breaking changes, migration notes
   ```

3. **SESSION_NOTES.md** (separate file):
   ```markdown
   # Detailed implementation notes
   # Format: Narrative style with context
   # Include: Decisions made, problems solved, future considerations
   ```

### Documentation Template
Always end your response with:
```markdown
---
## 📝 Change Summary for Human

### Files to Update:
[List all files that need to be saved/modified]

### Quick Apply Steps:
1. [Specific action]
2. [Specific action]
3. [Test to run]

### For CHANGELOG.md:
```
## Session [X] - [Date]
**Phase**: [Current Phase]
**Duration**: [Estimated time]

### Files Changed
- [File changes with descriptions]

### Breaking Changes
- [Any breaking changes]
```

### For SESSION_NOTES.md:
```
## Session [X] - [Date]
[Narrative description of what was accomplished, 
challenges faced, decisions made, and next steps]
```

### Checklist Update:
- [ ] Mark [specific item] as complete
- [ ] Update Recent Changes in Claude.md
- [ ] Add entry to CHANGELOG.md
- [ ] Add notes to SESSION_NOTES.md
- [ ] Commit with message: "[suggested message]"
```

This ensures consistent documentation across all Claude sessions.