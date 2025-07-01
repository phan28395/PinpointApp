# design/components.py
"""
UI component registry for PinPoint.
Maps component types to style generators.
"""

from typing import Dict, Any, Callable, Optional, List
from enum import Enum
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger
from design.theme import Theme, get_theme_manager


class ComponentType(Enum):
    """Standard component types."""
    # Basic components
    LABEL = "label"
    BUTTON = "button"
    TEXT_EDIT = "text_edit"
    TEXT_DISPLAY = "text_display"
    
    # Containers
    FRAME = "frame"
    SCROLL_AREA = "scroll_area"
    GROUP_BOX = "group_box"
    
    # Input components
    LINE_EDIT = "line_edit"
    SPIN_BOX = "spin_box"
    COMBO_BOX = "combo_box"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    SLIDER = "slider"
    
    # Tile-specific
    TILE_CONTAINER = "tile_container"
    TILE_HEADER = "tile_header"
    TILE_CONTENT = "tile_content"
    DRAG_HANDLE = "drag_handle"
    CLOSE_BUTTON = "close_button"
    PIN_BUTTON = "pin_button"


class StyleGenerator:
    """Generates styles for components based on theme."""
    
    def __init__(self, theme_manager=None):
        """
        Initialize style generator.
        
        Args:
            theme_manager: Optional theme manager instance
        """
        self.theme_manager = theme_manager or get_theme_manager()
        self.logger = get_logger("style_generator")
        
    def generate_style(self, 
                      component_type: ComponentType,
                      variant: str = "default",
                      size: str = "md",
                      custom_props: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate style for a component.
        
        Args:
            component_type: Type of component
            variant: Style variant (default, primary, secondary, etc.)
            size: Size variant (xs, sm, md, lg, xl)
            custom_props: Custom properties to override
            
        Returns:
            Style string (CSS-like format)
        """
        theme = self.theme_manager.get_current_theme()
        
        # Get base style for component type
        method_name = f"_generate_{component_type.value}_style"
        if hasattr(self, method_name):
            base_style = getattr(self, method_name)(theme, variant, size)
        else:
            base_style = self._generate_default_style(theme)
            
        # Apply custom properties
        if custom_props:
            base_style = self._apply_custom_props(base_style, custom_props)
            
        return base_style
        
    def _generate_label_style(self, theme: Theme, variant: str, size: str) -> str:
        """Generate label style."""
        # Map variant to color
        color_map = {
            "default": theme.colors.text_primary,
            "primary": theme.colors.accent,
            "secondary": theme.colors.text_secondary,
            "muted": theme.colors.text_muted,
            "error": theme.colors.error,
            "success": theme.colors.success,
            "warning": theme.colors.warning
        }
        color = color_map.get(variant, theme.colors.text_primary)
        
        # Get font size
        font_size = getattr(theme.typography, f"font_size_{size}", theme.typography.font_size_md)
        
        return f"""
            color: {color};
            font-family: {theme.typography.font_family_default};
            font-size: {font_size}px;
            font-weight: {theme.typography.font_weight_normal};
            background-color: transparent;
            padding: 0;
        """
        
    def _generate_button_style(self, theme: Theme, variant: str, size: str) -> str:
        """Generate button style."""
        # Determine colors based on variant
        if variant == "primary":
            bg_color = theme.colors.accent
            hover_color = theme.colors.accent_hover
            text_color = theme.colors.text_inverse
        elif variant == "secondary":
            bg_color = theme.colors.bg_tertiary
            hover_color = theme.colors.bg_hover
            text_color = theme.colors.text_primary
        elif variant == "danger":
            bg_color = theme.colors.error
            hover_color = theme.colors.error
            text_color = theme.colors.text_inverse
        else:
            bg_color = theme.colors.bg_secondary
            hover_color = theme.colors.bg_hover
            text_color = theme.colors.text_primary
            
        # Size-based padding
        padding_map = {
            "xs": f"{theme.spacing.xs}px {theme.spacing.sm}px",
            "sm": f"{theme.spacing.xs}px {theme.spacing.sm}px",
            "md": f"{theme.spacing.sm}px {theme.spacing.md}px",
            "lg": f"{theme.spacing.sm}px {theme.spacing.lg}px",
            "xl": f"{theme.spacing.md}px {theme.spacing.xl}px"
        }
        padding = padding_map.get(size, padding_map["md"])
        
        font_size = getattr(theme.typography, f"font_size_{size}", theme.typography.font_size_md)
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: {theme.effects.radius_md}px;
                padding: {padding};
                font-family: {theme.typography.font_family_default};
                font-size: {font_size}px;
                font-weight: {theme.typography.font_weight_medium};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                opacity: {theme.effects.opacity_disabled};
            }}
        """
        
    def _generate_text_edit_style(self, theme: Theme, variant: str, size: str) -> str:
        """Generate text edit style."""
        return f"""
            QTextEdit {{
                background-color: {theme.colors.bg_secondary};
                color: {theme.colors.text_primary};
                border: 1px solid {theme.colors.border_subtle};
                border-radius: {theme.effects.radius_md}px;
                padding: {theme.spacing.sm}px;
                font-family: {theme.typography.font_family_default};
                font-size: {theme.typography.font_size_md}px;
                selection-background-color: {theme.colors.accent_muted};
            }}
            QTextEdit:focus {{
                border-color: {theme.colors.accent};
            }}
        """
        
    def _generate_tile_container_style(self, theme: Theme, variant: str, size: str) -> str:
        """Generate tile container style."""
        return f"""
            QWidget#tileContainer {{
                background-color: {theme.colors.bg_secondary};
                border-radius: {theme.effects.radius_md}px;
                border: 1px solid {theme.colors.border_subtle};
            }}
        """
        
    def _generate_drag_handle_style(self, theme: Theme, variant: str, size: str) -> str:
        """Generate drag handle style."""
        return f"""
            QFrame#dragHandle {{
                background-color: transparent;
                border-bottom: 1px solid {theme.colors.border_subtle};
                min-height: {theme.spacing.md}px;
            }}
            QFrame#dragHandle:hover {{
                background-color: {theme.colors.bg_hover};
            }}
        """
        
    def _generate_close_button_style(self, theme: Theme, variant: str, size: str) -> str:
        """Generate close button style."""
        return f"""
            QPushButton#closeButton {{
                background-color: {theme.colors.bg_tertiary};
                color: {theme.colors.text_muted};
                border-radius: {theme.effects.radius_full}px;
                font-size: 12px;
                padding: 4px;
                min-width: 20px;
                min-height: 20px;
            }}
            QPushButton#closeButton:hover {{
                background-color: {theme.colors.error};
                color: white;
            }}
        """
        
    def _generate_default_style(self, theme: Theme) -> str:
        """Generate default style for unknown components."""
        return f"""
            background-color: {theme.colors.bg_primary};
            color: {theme.colors.text_primary};
            font-family: {theme.typography.font_family_default};
            font-size: {theme.typography.font_size_md}px;
        """
        
    def _apply_custom_props(self, base_style: str, custom_props: Dict[str, Any]) -> str:
        """Apply custom properties to style."""
        # This is a simple implementation
        # In a real system, would parse and merge CSS properly
        custom_lines = []
        for prop, value in custom_props.items():
            prop_css = prop.replace('_', '-')
            custom_lines.append(f"{prop_css}: {value};")
            
        if custom_lines:
            return base_style.rstrip() + "\n" + "\n".join(custom_lines)
        return base_style


class ComponentRegistry:
    """Registry for UI components and their styles."""
    
    def __init__(self):
        """Initialize component registry."""
        self.logger = get_logger("component_registry")
        self.style_generator = StyleGenerator()
        self._custom_generators: Dict[str, Callable] = {}
        
    def get_style(self,
                  component_type: ComponentType,
                  variant: str = "default",
                  size: str = "md",
                  custom_props: Optional[Dict[str, Any]] = None) -> str:
        """
        Get style for a component.
        
        Args:
            component_type: Type of component
            variant: Style variant
            size: Size variant
            custom_props: Custom properties
            
        Returns:
            Style string
        """
        # Check for custom generator first
        type_key = component_type.value if isinstance(component_type, ComponentType) else str(component_type)
        if type_key in self._custom_generators:
            return self._custom_generators[type_key](variant, size, custom_props)
            
        # Use default generator
        return self.style_generator.generate_style(
            component_type, variant, size, custom_props
        )
        
    def register_custom_generator(self, 
                                component_type: str,
                                generator: Callable) -> None:
        """
        Register a custom style generator.
        
        Args:
            component_type: Component type name
            generator: Style generator function
        """
        self._custom_generators[component_type] = generator
        self.logger.debug(f"Registered custom generator for: {component_type}")
        
    def get_tile_styles(self) -> Dict[str, str]:
        """
        Get all styles needed for a basic tile.
        
        Returns:
            Dictionary of component_id -> style
        """
        theme = self.style_generator.theme_manager.get_current_theme()
        
        return {
            "container": self.get_style(ComponentType.TILE_CONTAINER),
            "header": self.get_style(ComponentType.TILE_HEADER),
            "content": self.get_style(ComponentType.TILE_CONTENT),
            "drag_handle": self.get_style(ComponentType.DRAG_HANDLE),
            "close_button": self.get_style(ComponentType.CLOSE_BUTTON),
            "pin_button": self.get_style(ComponentType.PIN_BUTTON),
        }


# Global component registry
_global_registry: Optional[ComponentRegistry] = None


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ComponentRegistry()
    return _global_registry