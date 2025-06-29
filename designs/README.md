# PinPoint Design System Documentation

Welcome to the PinPoint Design System! This document explains how to create and modify designs for PinPoint without touching any application code.

## Overview

As a designer, you have complete control over:
- **Colors** - Every color in the application
- **Typography** - Fonts, sizes, weights
- **Spacing** - Margins, padding, gaps
- **Layout** - How components are arranged
- **Animations** - Transitions and effects
- **Icons** - All icons and symbols
- **Text** - All UI text and labels
- **Component Styles** - How every widget looks

You **cannot** control:
- What happens when buttons are clicked
- How data is processed
- Application logic or behavior
- Adding new functional components

## File Structure

```
designs/
├── main.json              # Main design configuration
├── styles/
│   ├── global.qss        # Global application styles
│   ├── classes.json      # Styles for widget types
│   └── ids.json          # Styles for specific widgets
├── layouts/
│   ├── main_window.json  # Main window layout
│   ├── tile_base.json    # Base tile layout
│   └── dialogs.json      # Dialog layouts
├── assets/
│   ├── icons/            # Icon files (SVG/PNG)
│   ├── fonts/            # Custom fonts
│   └── images/           # Other images
└── components.json       # Reusable component templates
```

## Quick Start

### 1. Changing Colors

Edit `main.json` and modify the `constants.colors` section:

```json
{
  "constants": {
    "colors": {
      "bg_primary": "#1a1a1a",      // Main background
      "text_primary": "#e0e0e0",    // Main text color
      "accent": "#14ffec",          // Accent color
      // ... more colors
    }
  }
}
```

### 2. Changing Widget Styles

Edit `styles/classes.json` to change how widget types look:

```json
{
  "QPushButton": {
    "default": "QPushButton { background-color: #2a2a2a; color: #e0e0e0; border-radius: 4px; padding: 8px 16px; }"
  }
}
```

### 3. Changing Specific Widget Styles

Edit `styles/ids.json` to style specific widgets:

```json
{
  "main_sidebar": {
    "default": "QWidget#main_sidebar { background-color: #1a1a1a; width: 80px; }"
  }
}
```

### 4. Changing Icons

Icons can be text-based (emoji) or image files:

```json
{
  "assets": {
    "icons": {
      "close": "text:✕",                    // Text icon
      "settings": "assets/icons/gear.svg"   // Image icon
    }
  }
}
```

### 5. Changing Layout

Edit layout files in `layouts/` directory:

```json
{
  "type": "horizontal",
  "spacing": 10,
  "margins": [20, 20, 20, 20],
  "children": [
    {
      "id": "sidebar",
      "properties": {
        "fixed_width": 250
      }
    }
  ]
}
```

## Widget Properties

You can control these properties for any widget:

- **size** - `{"width": 100, "height": 50}`
- **min_size** - Minimum size
- **max_size** - Maximum size
- **fixed_size** - Fixed size (can't be resized)
- **position** - `{"x": 10, "y": 20}`
- **margins** - `[top, right, bottom, left]`
- **spacing** - Space between child widgets
- **visible** - Show/hide widget
- **enabled** - Enable/disable widget
- **tooltip** - Hover tooltip text
- **font** - `{"family": "Arial", "size": 14, "weight": 700}`

## Style Syntax

We use Qt StyleSheet (QSS) syntax, which is similar to CSS:

```css
QPushButton {
  background-color: #14ffec;
  color: #1a1a1a;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
}

QPushButton:hover {
  background-color: #00e5d6;
}

QPushButton:pressed {
  background-color: #0a9b91;
}

QPushButton:disabled {
  background-color: #333333;
  color: #666666;
}
```

### Supported Pseudo-States

- `:hover` - Mouse over
- `:pressed` - Being clicked
- `:checked` - Toggled on
- `:unchecked` - Toggled off
- `:disabled` - Not interactive
- `:focus` - Has keyboard focus
- `:selected` - Selected item

## Live Reload

Your changes are automatically applied when you save files. The application watches for changes and updates the UI instantly.

## Widget Types Reference

### Common Widgets

- **QWidget** - Generic container
- **QPushButton** - Clickable button
- **QLabel** - Text label
- **QTextEdit** - Multi-line text editor
- **QLineEdit** - Single-line text input
- **QComboBox** - Dropdown menu
- **QCheckBox** - Checkbox
- **QRadioButton** - Radio button
- **QSlider** - Slider control
- **QProgressBar** - Progress indicator
- **QListWidget** - List of items
- **QTreeWidget** - Tree of items
- **QMenu** - Context/dropdown menu
- **QFrame** - Container with border

### PinPoint-Specific IDs

- **main_window** - Main application window
- **main_sidebar** - Left sidebar
- **editor_btn**, **library_btn**, etc. - Sidebar buttons
- **tile_container_note** - Note tile container
- **tile_drag_handle** - Tile drag area
- **tile_close_button** - Tile close button
- **central_content_stack** - Main content area

## Best Practices

1. **Use Constants** - Define colors and sizes in `constants` section and reference them
2. **Mobile First** - Design for smallest size first
3. **Test States** - Check hover, pressed, disabled states
4. **Maintain Contrast** - Ensure text is readable
5. **Consistent Spacing** - Use the spacing scale (xs, sm, md, lg, xl)
6. **Smooth Transitions** - Add transitions for better UX

## Examples

### Example 1: Dark Theme

```json
{
  "constants": {
    "colors": {
      "bg_primary": "#0a0a0a",
      "bg_secondary": "#1a1a1a",
      "text_primary": "#ffffff",
      "accent": "#00ff00"
    }
  }
}
```

### Example 2: Larger Sidebar

```json
{
  "properties": {
    "main_sidebar": {
      "fixed_size": {
        "width": 200,
        "height": -1
      }
    }
  }
}
```

### Example 3: Rounded Buttons

```json
{
  "QPushButton": {
    "default": "QPushButton { border-radius: 20px; padding: 12px 24px; }"
  }
}
```

## Testing Your Design

1. Save your changes
2. The application will automatically reload
3. Test all states (hover, click, etc.)
4. Try different window sizes
5. Check all tile types
6. Test with real content

## Limitations

- You cannot add new widgets or buttons
- You cannot change what widgets do
- You cannot access user data
- You cannot modify application behavior
- Maximum widget size is limited by screen
- Some properties may be overridden by functionality needs

## Need Help?

- Check existing designs for examples
- Use the Qt documentation for style properties
- Test incrementally - change one thing at a time
- Use the browser developer tools to inspect styles

Remember: You have complete control over how PinPoint looks, but not how it works. This separation ensures your designs work correctly with all current and future functionality.