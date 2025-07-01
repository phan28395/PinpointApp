# tests/test_session6_simple.py
"""
Simple tests for Session 6: Design System Foundation.
Tests theme system and component registry.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from design.theme import (
    Theme, ThemeManager, get_theme_manager,
    ColorScheme, Typography, Spacing, Effects
)
from design.components import (
    ComponentType, ComponentRegistry, StyleGenerator,
    get_component_registry
)


def test_color_scheme():
    """Test ColorScheme dataclass."""
    colors = ColorScheme()
    
    # Check defaults
    assert colors.bg_primary == "#1a1a1a"
    assert colors.text_primary == "#e0e0e0"
    assert colors.accent == "#14ffec"
    
    # Test to_dict
    color_dict = colors.to_dict()
    assert "bg_primary" in color_dict
    assert len(color_dict) > 10  # Should have many colors
    
    # Test custom colors
    custom = ColorScheme(bg_primary="#ffffff", accent="#0000ff")
    assert custom.bg_primary == "#ffffff"
    assert custom.accent == "#0000ff"
    
    print("✓ ColorScheme test passed")


def test_typography_spacing_effects():
    """Test Typography, Spacing, and Effects dataclasses."""
    # Typography
    typo = Typography()
    assert typo.font_size_md == 14
    assert typo.font_weight_normal == 400
    
    # Spacing
    spacing = Spacing()
    assert spacing.unit == 8
    assert spacing.md == 24  # 3 units
    
    # Effects
    effects = Effects()
    assert effects.radius_md == 8
    assert effects.opacity_disabled == 0.5
    
    print("✓ Typography, Spacing, Effects test passed")


def test_theme_basic():
    """Test Theme class."""
    theme = Theme("test_theme")
    
    # Check name and defaults
    assert theme.name == "test_theme"
    assert theme.colors.bg_primary == "#1a1a1a"
    
    # Test get_color
    assert theme.get_color("accent") == "#14ffec"
    assert theme.get_color("invalid", "#default") == "#default"
    
    # Test get_spacing
    assert theme.get_spacing("md") == 24
    assert theme.get_spacing("invalid", 99) == 99
    
    # Test to_dict / from_dict
    data = theme.to_dict()
    assert data["name"] == "test_theme"
    assert "colors" in data
    
    theme2 = Theme.from_dict(data)
    assert theme2.name == theme.name
    assert theme2.colors.accent == theme.colors.accent
    
    print("✓ Theme basic test passed")


def test_theme_manager():
    """Test ThemeManager."""
    manager = ThemeManager()
    
    # Check built-in themes
    assert len(manager.themes) >= 3  # dark, light, high_contrast
    assert "dark" in manager.themes
    assert "light" in manager.themes
    
    # Test get/set current theme
    assert manager.get_current_theme().name == "dark"  # Default
    
    assert manager.set_current_theme("light")
    assert manager.get_current_theme().name == "light"
    
    # Test invalid theme
    assert not manager.set_current_theme("invalid_theme")
    
    # Test list themes
    themes = manager.list_themes()
    assert "dark" in themes
    assert "light" in themes
    
    print("✓ ThemeManager test passed")


def test_custom_theme_registration():
    """Test registering custom themes."""
    manager = ThemeManager()
    
    # Create custom theme
    custom_colors = ColorScheme(
        bg_primary="#123456",
        accent="#fedcba"
    )
    custom_theme = Theme("custom", colors=custom_colors)
    
    # Register it
    manager.register_theme(custom_theme)
    
    # Verify registered
    assert "custom" in manager.list_themes()
    assert manager.get_theme("custom") is not None
    assert manager.get_theme("custom").colors.bg_primary == "#123456"
    
    print("✓ Custom theme registration test passed")


def test_component_types():
    """Test ComponentType enum."""
    # Check some basic types exist
    assert ComponentType.LABEL.value == "label"
    assert ComponentType.BUTTON.value == "button"
    assert ComponentType.TILE_CONTAINER.value == "tile_container"
    
    # Check tile-specific components
    tile_components = [
        ComponentType.TILE_CONTAINER,
        ComponentType.TILE_HEADER,
        ComponentType.TILE_CONTENT,
        ComponentType.DRAG_HANDLE,
        ComponentType.CLOSE_BUTTON,
        ComponentType.PIN_BUTTON
    ]
    
    for comp in tile_components:
        assert comp.value is not None
        
    print("✓ ComponentType test passed")


def test_style_generator():
    """Test StyleGenerator."""
    generator = StyleGenerator()
    
    # Test label generation
    label_style = generator.generate_style(
        ComponentType.LABEL,
        variant="primary",
        size="lg"
    )
    assert "color:" in label_style
    assert "font-size:" in label_style
    
    # Test button generation
    button_style = generator.generate_style(
        ComponentType.BUTTON,
        variant="primary",
        size="md"
    )
    assert "QPushButton" in button_style
    assert "background-color:" in button_style
    assert ":hover" in button_style
    
    # Test custom props
    custom_style = generator.generate_style(
        ComponentType.LABEL,
        custom_props={"margin_top": "10px", "text_align": "center"}
    )
    assert "margin-top: 10px" in custom_style
    assert "text-align: center" in custom_style
    
    print("✓ StyleGenerator test passed")


def test_component_registry():
    """Test ComponentRegistry."""
    registry = ComponentRegistry()
    
    # Test getting styles
    label_style = registry.get_style(ComponentType.LABEL)
    assert len(label_style) > 0
    
    # Test tile styles
    tile_styles = registry.get_tile_styles()
    assert "container" in tile_styles
    assert "header" in tile_styles
    assert "close_button" in tile_styles
    assert len(tile_styles) >= 6
    
    # Test custom generator
    def custom_generator(variant, size, custom_props):
        return f"/* Custom {variant} {size} */"
    
    registry.register_custom_generator("custom_comp", custom_generator)
    custom_style = registry.get_style("custom_comp", variant="test")
    assert "/* Custom test" in custom_style
    
    print("✓ ComponentRegistry test passed")


def test_theme_integration():
    """Test theme and component integration."""
    # Switch theme and verify style changes
    theme_mgr = get_theme_manager()
    registry = get_component_registry()
    
    # Get button style in dark theme
    theme_mgr.set_current_theme("dark")
    dark_button = registry.get_style(ComponentType.BUTTON, variant="primary")
    
    # Switch to light theme
    theme_mgr.set_current_theme("light")
    light_button = registry.get_style(ComponentType.BUTTON, variant="primary")
    
    # Styles should be different
    assert dark_button != light_button
    
    # Light theme should have light colors
    light_theme = theme_mgr.get_current_theme()
    assert "#ffffff" in light_theme.colors.bg_primary  # White background
    
    print("✓ Theme integration test passed")


def test_global_instances():
    """Test global singleton instances."""
    theme_mgr1 = get_theme_manager()
    theme_mgr2 = get_theme_manager()
    assert theme_mgr1 is theme_mgr2
    
    registry1 = get_component_registry()
    registry2 = get_component_registry()
    assert registry1 is registry2
    
    print("✓ Global instances test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 6 tests...")
    test_color_scheme()
    test_typography_spacing_effects()
    test_theme_basic()
    test_theme_manager()
    test_custom_theme_registration()
    test_component_types()
    test_style_generator()
    test_component_registry()
    test_theme_integration()
    test_global_instances()
    print("\n✅ All Session 6 tests passed!")