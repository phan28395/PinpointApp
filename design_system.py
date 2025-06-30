# pinpoint/design_system.py - Centralized Design System for PinPoint

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class ComponentType(Enum):
    """Allowed component types for tile designs."""
    LABEL = "label"
    BUTTON = "button"
    TEXT_EDIT = "text_edit"
    ICON = "icon"
    CONTAINER = "container"
    SPACER = "spacer"
    IMAGE = "image"
    PROGRESS = "progress"
    SLIDER = "slider"
    CHECKBOX = "checkbox"


class StyleVariant(Enum):
    """Pre-defined style variants for components."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    MUTED = "muted"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DesignConstraints:
    """Constraints that all tile designs must follow."""
    min_width: int = 100
    max_width: int = 600
    min_height: int = 80
    max_height: int = 800
    allowed_components: List[ComponentType] = None
    max_component_depth: int = 5  # Maximum nesting level
    required_components: List[str] = None  # e.g., ['close_button', 'drag_handle']
    
    def __post_init__(self):
        if self.allowed_components is None:
            self.allowed_components = list(ComponentType)
        if self.required_components is None:
            self.required_components = ['drag_handle']


class DesignSystem:
    """
    Centralized design system for PinPoint.
    This class defines all visual constants, provides style generators,
    and enforces design consistency across the application.
    """
    
    # Version for compatibility checking
    VERSION = "1.0.0"
    
    # Grid system (8px base unit)
    GRID_UNIT = 8
    
    # Spacing scale based on grid
    SPACING = {
        'none': 0,
        'xs': GRID_UNIT,        # 8px
        'sm': GRID_UNIT * 2,    # 16px
        'md': GRID_UNIT * 3,    # 24px
        'lg': GRID_UNIT * 4,    # 32px
        'xl': GRID_UNIT * 5,    # 40px
        'xxl': GRID_UNIT * 6,   # 48px
    }
    
    # Border radius scale
    RADIUS = {
        'none': 0,
        'sm': 4,
        'md': 8,
        'lg': 12,
        'xl': 16,
        'round': 9999,  # Fully rounded
    }
    
    # Color system with semantic naming
    COLORS = {
        # Base colors
        'bg_primary': '#1a1a1a',
        'bg_secondary': '#242424',
        'bg_tertiary': '#2a2a2a',
        'bg_hover': '#303030',
        'bg_selected': '#0d7377',
        
        # Text colors
        'text_primary': '#e0e0e0',
        'text_secondary': '#999999',
        'text_muted': '#666666',
        'text_inverse': '#1a1a1a',
        
        # Semantic colors
        'accent': '#14ffec',
        'accent_hover': '#00e5d6',
        'accent_muted': '#0a9b91',
        
        'success': '#4ade80',
        'success_hover': '#22c55e',
        
        'warning': '#fbbf24',
        'warning_hover': '#f59e0b',
        
        'error': '#f87171',
        'error_hover': '#ef4444',
        
        # UI colors
        'border_subtle': '#333333',
        'border_strong': '#555555',
        'shadow': 'rgba(0, 0, 0, 0.3)',
        
        # Transparent variants
        'overlay_light': 'rgba(255, 255, 255, 0.1)',
        'overlay_dark': 'rgba(0, 0, 0, 0.5)',
    }
    
    # Typography system
    TYPOGRAPHY = {
        'font_family': {
            'default': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
            'mono': '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace',
        },
        'font_size': {
            'xs': 11,
            'sm': 13,
            'md': 14,
            'lg': 16,
            'xl': 20,
            'xxl': 24,
            'title': 32,
        },
        'font_weight': {
            'light': 300,
            'normal': 400,
            'medium': 500,
            'semibold': 600,
            'bold': 700,
        },
        'line_height': {
            'tight': 1.2,
            'normal': 1.5,
            'relaxed': 1.75,
        },
        'letter_spacing': {
            'tight': '-0.02em',
            'normal': '0',
            'wide': '0.02em',
            'wider': '0.05em',
        }
    }
    
    # Shadow system
    SHADOWS = {
        'none': 'none',
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
        'glow': f'0 0 20px {COLORS["accent_muted"]}',
    }
    
    # Animation/Transition settings
    TRANSITIONS = {
        'fast': '150ms ease-in-out',
        'normal': '250ms ease-in-out',
        'slow': '350ms ease-in-out',
    }
    
    # Z-index scale for layering
    Z_INDEX = {
        'base': 0,
        'dropdown': 1000,
        'sticky': 1100,
        'fixed': 1200,
        'modal_backdrop': 1300,
        'modal': 1400,
        'popover': 1500,
        'tooltip': 1600,
        'notification': 1700,
    }
    
    @classmethod
    def get_style(cls, component_type: str, variant: str = 'primary', **kwargs) -> str:
        """
        Get stylesheet for a specific component type and variant.
        This is the main method designers will use.
        """
        method_name = f'get_{component_type}_style'
        if hasattr(cls, method_name):
            # Get the method
            method = getattr(cls, method_name)
            # Check method signature to see what parameters it accepts
            import inspect
            sig = inspect.signature(method)
            params = sig.parameters
            
            # Filter kwargs to only include parameters the method accepts
            filtered_kwargs = {}
            for key, value in kwargs.items():
                if key in params:
                    filtered_kwargs[key] = value
                    
            return method(variant, **filtered_kwargs)
        return ""
    
    @classmethod
    def get_label_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QLabel stylesheet."""
        color = cls.COLORS.get(f'text_{variant}', cls.COLORS['text_primary'])
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        return f"""
            QLabel {{
                color: {color};
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                font-weight: {cls.TYPOGRAPHY['font_weight']['normal']};
                padding: 0;
                background-color: transparent;
            }}
        """
    
    @classmethod
    def get_button_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QPushButton stylesheet."""
        # Determine colors based on variant
        if variant == 'primary':
            bg_color = cls.COLORS['accent']
            hover_color = cls.COLORS['accent_hover']
            text_color = cls.COLORS['text_inverse']
        elif variant == 'secondary':
            bg_color = cls.COLORS['bg_tertiary']
            hover_color = cls.COLORS['bg_hover']
            text_color = cls.COLORS['text_primary']
        else:
            bg_color = cls.COLORS.get(variant, cls.COLORS['bg_tertiary'])
            hover_color = cls.COLORS.get(f'{variant}_hover', cls.COLORS['bg_hover'])
            text_color = cls.COLORS['text_primary']
        
        # Determine sizing
        padding_y = cls.SPACING['xs'] if size == 'sm' else cls.SPACING['sm']
        padding_x = cls.SPACING['sm'] if size == 'sm' else cls.SPACING['md']
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: {padding_y}px {padding_x}px;
                border-radius: {cls.RADIUS['md']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                font-weight: {cls.TYPOGRAPHY['font_weight']['medium']};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
                transform: translateY(1px);
            }}
            QPushButton:disabled {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_muted']};
            }}
        """
    
    @classmethod
    def get_text_edit_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QTextEdit stylesheet."""
        # Determine font size based on size parameter
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        # Determine colors based on variant
        if variant == 'transparent':
            bg_color = 'transparent'
            border_color = 'transparent'
            focus_border_color = cls.COLORS['accent']
        else:
            bg_color = cls.COLORS['bg_secondary']
            border_color = cls.COLORS['border_subtle']
            focus_border_color = cls.COLORS['accent']
        
        return f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {border_color};
                border-radius: {cls.RADIUS['md']}px;
                padding: {cls.SPACING['sm']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                selection-background-color: {cls.COLORS['accent_muted']};
            }}
            QTextEdit:focus {{
                border-color: {focus_border_color};
            }}
        """
    
    @classmethod
    def get_container_style(cls, variant: str = 'primary', elevation: str = 'md') -> str:
        """Generate QFrame/QWidget container stylesheet."""
        bg_color = cls.COLORS.get(f'bg_{variant}', cls.COLORS['bg_secondary'])
        shadow = cls.SHADOWS.get(elevation, cls.SHADOWS['md'])
        
        return f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: {cls.RADIUS['md']}px;
                border: 1px solid {cls.COLORS['border_subtle']};
            }}
        """
    
    @classmethod
    def get_tile_base_style(cls) -> str:
        """Get the base style that all tiles must use."""
        return f"""
            /* Base tile container */
            QWidget#tileContainer {{
                background-color: {cls.COLORS['bg_secondary']};
                border-radius: {cls.RADIUS['md']}px;
            }}
            
            /* Drag handle */
            QFrame#dragHandle {{
                background-color: transparent;
                border-bottom: 1px solid {cls.COLORS['border_subtle']};
                min-height: {cls.SPACING['md']}px;
            }}
            QFrame#dragHandle:hover {{
                background-color: {cls.COLORS['overlay_light']};
            }}
            
            /* Close button */
            QPushButton#closeButton {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_muted']};
                border-radius: {cls.RADIUS['round']}px;
                font-size: 12px;
                padding: 4px;
            }}
            QPushButton#closeButton:hover {{
                background-color: {cls.COLORS['error']};
                color: white;
            }}
            
            /* Pin button */
            QPushButton#pinButton {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_muted']};
                border-radius: {cls.RADIUS['round']}px;
                font-size: 12px;
                padding: 4px;
            }}
            QPushButton#pinButton[pinned="true"] {{
                background-color: {cls.COLORS['accent']};
                color: {cls.COLORS['text_inverse']};
            }}
        """
    
    @classmethod
    def validate_design_spec(cls, spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a design specification against constraints.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ['metadata', 'layout', 'styling']
        for field in required_fields:
            if field not in spec:
                errors.append(f"Missing required field: {field}")
        
        # Validate metadata
        if 'metadata' in spec:
            meta = spec['metadata']
            if 'name' not in meta:
                errors.append("Metadata must include 'name'")
            if 'version' not in meta:
                errors.append("Metadata must include 'version'")
            if 'compatible_with' not in meta:
                errors.append("Metadata must include 'compatible_with' design system version")
        
        # Validate layout
        if 'layout' in spec:
            layout = spec['layout']
            if 'components' not in layout:
                errors.append("Layout must include 'components' array")
            else:
                # Validate each component
                for i, comp in enumerate(layout['components']):
                    comp_errors = cls._validate_component(comp, f"components[{i}]")
                    errors.extend(comp_errors)
        
        return len(errors) == 0, errors
    
    @classmethod
    def _validate_component(cls, component: Dict[str, Any], path: str) -> List[str]:
        """Validate a single component specification."""
        errors = []
        
        if 'type' not in component:
            errors.append(f"{path}: Missing 'type' field")
        else:
            comp_type = component['type']
            try:
                ComponentType(comp_type)
            except ValueError:
                errors.append(f"{path}: Invalid component type '{comp_type}'")
        
        if 'id' not in component:
            errors.append(f"{path}: Missing 'id' field")
        
        return errors
    
    @classmethod
    def export_for_designers(cls) -> Dict[str, Any]:
        """
        Export design system constants for external designers.
        This creates a JSON-serializable version of the design system.
        """
        return {
            'version': cls.VERSION,
            'spacing': cls.SPACING,
            'colors': cls.COLORS,
            'typography': cls.TYPOGRAPHY,
            'shadows': cls.SHADOWS,
            'radius': cls.RADIUS,
            'transitions': cls.TRANSITIONS,
            'component_types': [ct.value for ct in ComponentType],
            'style_variants': [sv.value for sv in StyleVariant],
            'constraints': {
                'min_width': DesignConstraints().min_width,
                'max_width': DesignConstraints().max_width,
                'min_height': DesignConstraints().min_height,
                'max_height': DesignConstraints().max_height,
                'max_component_depth': DesignConstraints().max_component_depth,
                'allowed_components': [ct.value for ct in ComponentType],
                'required_components': DesignConstraints().required_components,
            },
        }


# Convenience functions for common use cases
def get_style(*args, **kwargs):
    """Shorthand for DesignSystem.get_style()"""
    return DesignSystem.get_style(*args, **kwargs)


def spacing(size: str) -> int:
    """Get spacing value by size name."""
    return DesignSystem.SPACING.get(size, DesignSystem.SPACING['md'])


def color(name: str) -> str:
    """Get color value by name."""
    return DesignSystem.COLORS.get(name, DesignSystem.COLORS['text_primary'])