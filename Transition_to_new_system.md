# Transition Guide: Moving to the Refactored Design System

This guide helps you transition from the original PinPoint code to the refactored design-separated system.

## Running the Application

### Option 1: Run Refactored Version (Recommended)
```bash
python run.py
# or
python run.py --refactored
```

### Option 2: Run Original Version
```bash
python run.py --original
```

## Transition Strategy

### Phase 1: Parallel Development (Current)
- Keep both systems running
- Develop new features in refactored system
- Maintain critical fixes in both

### Phase 2: Gradual Migration
1. **Start with Non-Critical Components**
   - Dialogs
   - About windows
   - Settings panels

2. **Move Core Components**
   - Main window
   - System tray
   - Tile manager

3. **Migrate Tiles One by One**
   - Note tile ✅ (already done)
   - Clock tile
   - Weather tile
   - Todo tile

### Phase 3: Full Migration
- Remove original code
- Update all imports
- Clean up dependencies

## File Structure During Transition

```
pinpoint/
├── main.py                    # Original (keep for now)
├── main_refactored.py         # New version
├── main_window.py             # Original
├── main_window_refactored.py  # New version
├── base_tile.py               # Original
├── base_tile_refactored.py    # New version
├── design_layer.py            # New (required)
├── widget_factory.py          # New (required)
└── designs/                   # New design files
    ├── main.json
    └── styles/
        ├── classes.json
        └── ids.json
```

## Step-by-Step Migration for a Component

### Example: Migrating a Dialog

#### Original Code:
```python
class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QDialog { background-color: #242424; }
            QPushButton { 
                background-color: #14ffec;
                color: #1a1a1a;
                padding: 8px 16px;
            }
        """)
        self.setFixedSize(400, 300)
```

#### Step 1: Remove Styles
```python
class MyDialog(QDialog):
    def __init__(self, design_layer):
        super().__init__()
        self.design = design_layer
        self.setObjectName("my_dialog")
        # Remove setStyleSheet
        # Remove setFixedSize
```

#### Step 2: Add to Design Files
In `styles/ids.json`:
```json
{
  "my_dialog": {
    "default": "QDialog#my_dialog { background-color: #242424; }"
  }
}
```

In `main.json` under properties:
```json
{
  "properties": {
    "my_dialog": {
      "fixed_size": {"width": 400, "height": 300}
    }
  }
}
```

#### Step 3: Apply Design
```python
class MyDialog(QDialog):
    def __init__(self, design_layer):
        super().__init__()
        self.design = design_layer
        self.setObjectName("my_dialog")
        
        # Create UI...
        
        # Apply design
        self.design.apply_design(self)
```

## Testing During Transition

### 1. Visual Regression Testing
- Take screenshots of original UI
- Compare with refactored UI
- Document any intentional changes

### 2. Functionality Testing
```python
# Test both versions
def test_tile_creation():
    # Test original
    original_tile = OriginalNoteTile(data)
    assert original_tile.works()
    
    # Test refactored
    refactored_tile = NoteTile(data, design_layer)
    assert refactored_tile.works()
```

### 3. Design Live Reload Testing
1. Run refactored version
2. Open `designs/main.json`
3. Change a color value
4. Save file
5. UI should update automatically

## Common Migration Patterns

### Pattern 1: Hardcoded Colors
```python
# Before
self.setStyleSheet("background-color: #14ffec;")

# After
# Just remove it - design layer handles it
```

### Pattern 2: Fixed Sizes
```python
# Before
self.setFixedSize(250, 150)

# After
# Add to design properties, remove from code
```

### Pattern 3: Creating Widgets
```python
# Before
btn = QPushButton("Click Me")
btn.setStyleSheet("...")

# After
btn = self.factory.create_button("Click Me", "my_button")
# No styling in code
```

### Pattern 4: Icons
```python
# Before
btn = QPushButton("❌ Quit")

# After
icon_text = self.design.get_icon_text("quit")
text = self.design.get_text("menu.quit", "Quit")
btn = QPushButton(f"{icon_text} {text}")
```

## Troubleshooting

### Issue: "No design files found"
**Solution**: Run will create default files automatically

### Issue: "Widget looks unstyled"
**Solution**: 
1. Ensure widget has objectName set
2. Check if style exists in design files
3. Verify design.apply_design() is called

### Issue: "Style changes not applying"
**Solution**:
1. Check file watcher is working
2. Ensure valid JSON syntax
3. Check console for errors

## Benefits After Migration

1. **Designers can work independently**
2. **Live reload of styles**
3. **Multiple themes support**
4. **Cleaner, more maintainable code**
5. **Plugin system ready**
6. **Payment system ready**

## Rollback Plan

If issues arise:
1. Keep original files intact
2. Use `--original` flag to run old version
3. Git branch for refactored version
4. Gradual rollback of components if needed

## Getting Help

- Check example_usage.py for patterns
- Review refactored components for reference
- Use design_migration_helper.py to extract existing styles
- Document issues for team discussion