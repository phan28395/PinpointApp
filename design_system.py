# pinpoint/design_system.py - Enhanced with complete component support and theme inheritance
# Part 1: Core classes, enums, and theme system

from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class ComponentType(Enum):
    """Allowed component types for tile designs."""
    LABEL = "label"
    BUTTON = "button"
    TEXT_EDIT = "text_edit"
    LINE_EDIT = "line_edit"
    ICON = "icon"
    CONTAINER = "container"
    SPACER = "spacer"
    IMAGE = "image"
    PROGRESS = "progress"
    SLIDER = "slider"
    CHECKBOX = "checkbox"
    RADIO = "radio"  # New
    COMBO_BOX = "combo_box"  # New
    SPIN_BOX = "spin_box"  # New
    TAB_WIDGET = "tab_widget"  # New
    GROUP_BOX = "group_box"  # New


class StyleVariant(Enum):
    """Pre-defined style variants for components."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    MUTED = "muted"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TRANSPARENT = "transparent"
    GLASS = "glass"  # New: glassmorphism effect
    OUTLINED = "outlined"  # New: outlined variant


class ComponentState(Enum):
    """Component states for styling."""
    NORMAL = "normal"
    HOVER = "hover"
    ACTIVE = "active"
    PRESSED = "pressed"
    FOCUSED = "focused"
    DISABLED = "disabled"


@dataclass
class ThemeDefinition:
    """Defines a complete theme with inheritance support."""
    name: str
    parent: Optional[str] = None
    colors: Dict[str, str] = field(default_factory=dict)
    spacing: Dict[str, int] = field(default_factory=dict)
    typography: Dict[str, Any] = field(default_factory=dict)
    shadows: Dict[str, str] = field(default_factory=dict)
    radius: Dict[str, int] = field(default_factory=dict)
    
    def inherit_from(self, parent_theme: 'ThemeDefinition'):
        """Inherit values from parent theme."""
        # Colors
        for key, value in parent_theme.colors.items():
            if key not in self.colors:
                self.colors[key] = value
        # Spacing
        for key, value in parent_theme.spacing.items():
            if key not in self.spacing:
                self.spacing[key] = value
        # Typography
        for key, value in parent_theme.typography.items():
            if key not in self.typography:
                self.typography[key] = value.copy() if isinstance(value, dict) else value
        # Shadows
        for key, value in parent_theme.shadows.items():
            if key not in self.shadows:
                self.shadows[key] = value
        # Radius
        for key, value in parent_theme.radius.items():
            if key not in self.radius:
                self.radius[key] = value


@dataclass
class ResponsiveValue:
    """Represents a value that can change based on container size."""
    small: Any
    medium: Any
    large: Any
    
    def get_value(self, container_width: int) -> Any:
        """Get the appropriate value based on container width."""
        if container_width < 200:
            return self.small
        elif container_width < 400:
            return self.medium
        else:
            return self.large


@dataclass
class DesignConstraints:
    """Constraints that all tile designs must follow."""
    min_width: int = 100
    max_width: int = 600
    min_height: int = 80
    max_height: int = 800
    allowed_components: List[ComponentType] = None
    max_component_depth: int = 5
    required_components: List[str] = None
    
    def __post_init__(self):
        if self.allowed_components is None:
            self.allowed_components = list(ComponentType)
        if self.required_components is None:
            self.required_components = []


class DesignSystem:
    """
    Centralized design system for PinPoint.
    Enhanced with theme inheritance and component states.
    """
    
    # Version for compatibility checking
    VERSION = "1.1.0"  # Bumped minor version for new features
    
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
        
        'info': '#60a5fa',
        'info_hover': '#3b82f6',
        
        # UI colors
        'border_subtle': '#333333',
        'border_strong': '#555555',
        'shadow': 'rgba(0, 0, 0, 0.3)',
        
        # Transparent variants
        'overlay_light': 'rgba(255, 255, 255, 0.1)',
        'overlay_dark': 'rgba(0, 0, 0, 0.5)',
        
        # Glass morphism
        'glass_bg': 'rgba(255, 255, 255, 0.05)',
        'glass_border': 'rgba(255, 255, 255, 0.1)',
    }
    
    # Typography system
    TYPOGRAPHY = {
        'font_family': {
            'default': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
            'mono': '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace',
            'display': 'Poppins, "Helvetica Neue", Arial, sans-serif',
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
        'inset': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
    }
    
    # Animation/Transition settings
    TRANSITIONS = {
        'fast': '150ms ease-in-out',
        'normal': '250ms ease-in-out',
        'slow': '350ms ease-in-out',
        'bounce': '500ms cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth': '300ms cubic-bezier(0.4, 0, 0.2, 1)',
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
    
    # Theme registry
    _themes: Dict[str, ThemeDefinition] = {}
    _current_theme: str = "default"
    
    @classmethod
    def init_default_themes(cls):
        """Initialize built-in themes."""
        # Default dark theme
        default_theme = ThemeDefinition(
            name="default",
            colors=cls.COLORS.copy(),
            spacing=cls.SPACING.copy(),
            typography=cls.TYPOGRAPHY.copy(),
            shadows=cls.SHADOWS.copy(),
            radius=cls.RADIUS.copy()
        )
        cls.register_theme(default_theme)
        
        # Light theme (inherits from default)
        light_theme = ThemeDefinition(
            name="light",
            parent="default",
            colors={
                'bg_primary': '#ffffff',
                'bg_secondary': '#f5f5f5',
                'bg_tertiary': '#ebebeb',
                'bg_hover': '#e0e0e0',
                'text_primary': '#1a1a1a',
                'text_secondary': '#666666',
                'text_muted': '#999999',
                'text_inverse': '#ffffff',
                'border_subtle': '#e0e0e0',
                'border_strong': '#cccccc',
            }
        )
        cls.register_theme(light_theme)
        
        # Glass theme (inherits from default)
        glass_theme = ThemeDefinition(
            name="glass",
            parent="default",
            colors={
                'bg_primary': 'rgba(255, 255, 255, 0.05)',
                'bg_secondary': 'rgba(255, 255, 255, 0.08)',
                'bg_tertiary': 'rgba(255, 255, 255, 0.1)',
                'border_subtle': 'rgba(255, 255, 255, 0.2)',
                'border_strong': 'rgba(255, 255, 255, 0.3)',
            },
            shadows={
                'md': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
                'lg': '0 16px 48px 0 rgba(31, 38, 135, 0.5)',
            }
        )
        cls.register_theme(glass_theme)
    
    @classmethod
    def register_theme(cls, theme: ThemeDefinition):
        """Register a theme in the system."""
        cls._themes[theme.name] = theme
        
        # Apply inheritance if parent specified
        if theme.parent and theme.parent in cls._themes:
            parent_theme = cls._themes[theme.parent]
            theme.inherit_from(parent_theme)
    
    @classmethod
    def set_current_theme(cls, theme_name: str):
        """Set the current active theme."""
        if theme_name in cls._themes:
            cls._current_theme = theme_name
        else:
            print(f"Theme '{theme_name}' not found")
    
    @classmethod
    def get_theme_value(cls, category: str, key: str) -> Any:
        """Get a value from the current theme with fallback to default."""
        if cls._current_theme in cls._themes:
            theme = cls._themes[cls._current_theme]
            theme_category = getattr(theme, category, {})
            if key in theme_category:
                return theme_category[key]
        
        # Fallback to default values
        default_category = getattr(cls, category.upper(), {})
        return default_category.get(key)
    
    @classmethod
    def get_style(cls, component_type: str, variant: str = 'primary', 
                  state: str = 'normal', **kwargs) -> str:
        """
        Get stylesheet for a specific component type, variant, and state.
        This is the main method designers will use.
        """
        method_name = f'get_{component_type}_style'
        if hasattr(cls, method_name):
            method = getattr(cls, method_name)
            import inspect
            sig = inspect.signature(method)
            params = sig.parameters
            
            # Filter kwargs to only include parameters the method accepts
            filtered_kwargs = {}
            for key, value in kwargs.items():
                if key in params:
                    filtered_kwargs[key] = value
            
            # Add state if method accepts it
            if 'state' in params:
                filtered_kwargs['state'] = state
                    
            return method(variant, **filtered_kwargs)
        return ""
    
    @classmethod
    def get_responsive_value(cls, base_value: Union[int, str, ResponsiveValue], 
                           container_width: int) -> Any:
        """Get responsive value based on container width."""
        if isinstance(base_value, ResponsiveValue):
            return base_value.get_value(container_width)
        return base_value
    
    @classmethod
    def get_state_modifier(cls, base_style: str, state: str) -> str:
        """Get state-specific style modifiers."""
        if state == ComponentState.HOVER.value:
            return f"""
                {base_style}
                transform: translateY(-1px);
                box-shadow: {cls.SHADOWS['md']};
            """
        elif state == ComponentState.PRESSED.value:
            return f"""
                {base_style}
                transform: translateY(0);
                box-shadow: {cls.SHADOWS['sm']};
            """
        elif state == ComponentState.DISABLED.value:
            return f"""
                {base_style}
                opacity: 0.5;
                cursor: not-allowed;
            """
        return base_style
    
    # Enhanced component style methods with state support
    
    @classmethod
    def get_label_style(cls, variant: str = 'primary', size: str = 'md', 
                       state: str = 'normal') -> str:
        """Generate QLabel stylesheet."""
        color = cls.get_theme_value('colors', f'text_{variant}')
        if not color:
            color = cls.get_theme_value('colors', 'text_primary')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        base = f"""
            QLabel {{
                color: {color};
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                font-weight: {cls.TYPOGRAPHY['font_weight']['normal']};
                padding: 0;
                background-color: transparent;
            }}
        """
        
        if state == ComponentState.DISABLED.value:
            base += f"""
                QLabel:disabled {{
                    color: {cls.get_theme_value('colors', 'text_muted')};
                }}
            """
        
        return base
    
    @classmethod
    def get_button_style(cls, variant: str = 'primary', size: str = 'md', 
                        state: str = 'normal') -> str:
        """Generate QPushButton stylesheet with state support."""
        # Determine colors based on variant
        if variant == 'primary':
            bg_color = cls.get_theme_value('colors', 'accent')
            hover_color = cls.get_theme_value('colors', 'accent_hover')
            text_color = cls.get_theme_value('colors', 'text_inverse')
        elif variant == 'secondary':
            bg_color = cls.get_theme_value('colors', 'bg_tertiary')
            hover_color = cls.get_theme_value('colors', 'bg_hover')
            text_color = cls.get_theme_value('colors', 'text_primary')
        elif variant == 'transparent':
            bg_color = 'transparent'
            hover_color = cls.get_theme_value('colors', 'overlay_light')
            text_color = cls.get_theme_value('colors', 'text_primary')
        elif variant == 'glass':
            bg_color = cls.get_theme_value('colors', 'glass_bg')
            hover_color = cls.get_theme_value('colors', 'glass_border')
            text_color = cls.get_theme_value('colors', 'text_primary')
        elif variant == 'outlined':
            bg_color = 'transparent'
            hover_color = cls.get_theme_value('colors', 'overlay_light')
            text_color = cls.get_theme_value('colors', 'accent')
        else:
            bg_color = cls.get_theme_value('colors', variant) or cls.get_theme_value('colors', 'bg_tertiary')
            hover_color = cls.get_theme_value('colors', f'{variant}_hover') or cls.get_theme_value('colors', 'bg_hover')
            text_color = cls.get_theme_value('colors', 'text_primary')
        
        # Determine sizing
        padding_y = cls.SPACING['xs'] if size == 'sm' else cls.SPACING['sm']
        padding_x = cls.SPACING['sm'] if size == 'sm' else cls.SPACING['md']
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        # Build base style
        base = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: {'1px solid ' + text_color if variant == 'outlined' else 'none'};
                padding: {padding_y}px {padding_x}px;
                border-radius: {cls.RADIUS['md']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                font-weight: {cls.TYPOGRAPHY['font_weight']['medium']};
            }}
        """
        
        # Add glass effect
        if variant == 'glass':
            base += f"""
                QPushButton {{
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    border: 1px solid {cls.get_theme_value('colors', 'glass_border')};
                }}
            """
        
        # Add state styles
        base += f"""
            QPushButton:hover {{
                background-color: {hover_color};
                transform: translateY(-1px);
                box-shadow: {cls.SHADOWS['md']};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
                transform: translateY(0);
                box-shadow: {cls.SHADOWS['sm']};
            }}
            QPushButton:focus {{
                outline: none;
                box-shadow: 0 0 0 3px {cls.get_theme_value('colors', 'accent')}33;
            }}
            QPushButton:disabled {{
                background-color: {cls.get_theme_value('colors', 'bg_tertiary')};
                color: {cls.get_theme_value('colors', 'text_muted')};
                border: none;
                transform: none;
                box-shadow: none;
            }}
        """
        
        return base
    
    @classmethod
    def get_text_edit_style(cls, variant: str = 'primary', size: str = 'md', 
                           state: str = 'normal') -> str:
        """Generate QTextEdit stylesheet."""
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        if variant == 'transparent':
            bg_color = 'transparent'
            border_color = 'transparent'
            focus_border_color = cls.get_theme_value('colors', 'accent')
        elif variant == 'glass':
            bg_color = cls.get_theme_value('colors', 'glass_bg')
            border_color = cls.get_theme_value('colors', 'glass_border')
            focus_border_color = cls.get_theme_value('colors', 'accent')
        else:
            bg_color = cls.get_theme_value('colors', 'bg_secondary')
            border_color = cls.get_theme_value('colors', 'border_subtle')
            focus_border_color = cls.get_theme_value('colors', 'accent')
        
        base = f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {cls.get_theme_value('colors', 'text_primary')};
                border: 1px solid {border_color};
                border-radius: {cls.RADIUS['md']}px;
                padding: {cls.SPACING['sm']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                selection-background-color: {cls.get_theme_value('colors', 'accent_muted')};
            }}
            QTextEdit:focus {{
                border-color: {focus_border_color};
                box-shadow: 0 0 0 3px {focus_border_color}33;
            }}
            QTextEdit:disabled {{
                background-color: {cls.get_theme_value('colors', 'bg_tertiary')};
                color: {cls.get_theme_value('colors', 'text_muted')};
            }}
        """
        
        if variant == 'glass':
            base += """
                QTextEdit {
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                }
            """
        
        return base
    
    @classmethod
    def get_line_edit_style(cls, variant: str = 'primary', size: str = 'md',
                           state: str = 'normal') -> str:
        """Generate QLineEdit stylesheet."""
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        if variant == 'transparent':
            bg_color = 'transparent'
            border_style = f"border-bottom: 1px solid {cls.get_theme_value('colors', 'border_subtle')}"
            focus_border = f"border-bottom: 2px solid {cls.get_theme_value('colors', 'accent')}"
        else:
            bg_color = cls.get_theme_value('colors', 'bg_secondary')
            border_style = f"border: 1px solid {cls.get_theme_value('colors', 'border_subtle')}"
            focus_border = f"border: 1px solid {cls.get_theme_value('colors', 'accent')}"
        
        return f"""
            QLineEdit {{
                background-color: {bg_color};
                color: {cls.get_theme_value('colors', 'text_primary')};
                {border_style};
                border-radius: {cls.RADIUS['sm']}px;
                padding: {cls.SPACING['xs']}px {cls.SPACING['sm']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                selection-background-color: {cls.get_theme_value('colors', 'accent_muted')};
            }}
            QLineEdit:focus {{
                {focus_border};
                box-shadow: 0 0 0 3px {cls.get_theme_value('colors', 'accent')}33;
            }}
            QLineEdit:disabled {{
                background-color: {cls.get_theme_value('colors', 'bg_tertiary')};
                color: {cls.get_theme_value('colors', 'text_muted')};
            }}
        """
    
    @classmethod
    def get_container_style(cls, variant: str = 'primary', elevation: str = 'md') -> str:
        """Generate QFrame/QWidget container stylesheet."""
        bg_color = cls.get_theme_value('colors', f'bg_{variant}')
        if not bg_color:
            bg_color = cls.get_theme_value('colors', 'bg_secondary')
        shadow = cls.SHADOWS.get(elevation, cls.SHADOWS['md'])
        
        return f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: {cls.RADIUS['md']}px;
                border: 1px solid {cls.get_theme_value('colors', 'border_subtle')};
            }}
        """
    
    @classmethod
    def get_icon_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate icon (QLabel) stylesheet."""
        color = cls.get_theme_value('colors', f'text_{variant}')
        if not color:
            color = cls.get_theme_value('colors', 'text_primary')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        return f"""
            QLabel {{
                color: {color};
                font-size: {font_size}px;
                padding: {cls.SPACING['xs']}px;
                background-color: transparent;
            }}
        """
    
    @classmethod
    def get_progress_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QProgressBar stylesheet."""
        bar_color = cls.get_theme_value('colors', variant) or cls.get_theme_value('colors', 'accent')
        bg_color = cls.get_theme_value('colors', 'bg_tertiary')
        height = 4 if size == 'sm' else 8 if size == 'md' else 12
        
        return f"""
            QProgressBar {{
                background-color: {bg_color};
                border: none;
                border-radius: {height // 2}px;
                height: {height}px;
                text-align: center;
                color: {cls.get_theme_value('colors', 'text_primary')};
                font-size: {cls.TYPOGRAPHY['font_size']['xs']}px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: {height // 2}px;
            }}
        """
    
    @classmethod
    def get_slider_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QSlider stylesheet."""
        handle_color = cls.get_theme_value('colors', variant) or cls.get_theme_value('colors', 'accent')
        track_color = cls.get_theme_value('colors', 'bg_tertiary')
        handle_size = 12 if size == 'sm' else 16 if size == 'md' else 20
        track_height = 4 if size == 'sm' else 6 if size == 'md' else 8
        
        return f"""
            QSlider::groove:horizontal {{
                background-color: {track_color};
                height: {track_height}px;
                border-radius: {track_height // 2}px;
            }}
            QSlider::handle:horizontal {{
                background-color: {handle_color};
                border: none;
                width: {handle_size}px;
                height: {handle_size}px;
                margin: -{(handle_size - track_height) // 2}px 0;
                border-radius: {handle_size // 2}px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {cls.get_theme_value('colors', f'{variant}_hover') or handle_color};
                box-shadow: {cls.SHADOWS['md']};
            }}
            QSlider::groove:vertical {{
                background-color: {track_color};
                width: {track_height}px;
                border-radius: {track_height // 2}px;
            }}
            QSlider::handle:vertical {{
                background-color: {handle_color};
                border: none;
                width: {handle_size}px;
                height: {handle_size}px;
                margin: 0 -{(handle_size - track_height) // 2}px;
                border-radius: {handle_size // 2}px;
            }}
        """
    
    @classmethod
    def get_checkbox_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QCheckBox stylesheet."""
        check_color = cls.get_theme_value('colors', variant) or cls.get_theme_value('colors', 'accent')
        text_color = cls.get_theme_value('colors', 'text_primary')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        indicator_size = 14 if size == 'sm' else 18 if size == 'md' else 22
        
        return f"""
            QCheckBox {{
                color: {text_color};
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                spacing: {cls.SPACING['xs']}px;
            }}
            QCheckBox::indicator {{
                width: {indicator_size}px;
                height: {indicator_size}px;
                border: 2px solid {cls.get_theme_value('colors', 'border_strong')};
                border-radius: {cls.RADIUS['sm']}px;
                background-color: {cls.get_theme_value('colors', 'bg_secondary')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {check_color};
                border-color: {check_color};
                image: url(check.png);  /* Would need to provide checkmark image */
            }}
            QCheckBox::indicator:hover {{
                border-color: {cls.get_theme_value('colors', 'accent')};
            }}
            QCheckBox:disabled {{
                color: {cls.get_theme_value('colors', 'text_muted')};
            }}
        """
    
    @classmethod
    def get_combo_box_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QComboBox stylesheet."""
        bg_color = cls.get_theme_value('colors', 'bg_secondary')
        border_color = cls.get_theme_value('colors', 'border_subtle')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        return f"""
            QComboBox {{
                background-color: {bg_color};
                color: {cls.get_theme_value('colors', 'text_primary')};
                border: 1px solid {border_color};
                border-radius: {cls.RADIUS['md']}px;
                padding: {cls.SPACING['xs']}px {cls.SPACING['sm']}px;
                padding-right: {cls.SPACING['xl']}px;  /* Space for arrow */
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                min-height: {cls.SPACING['lg']}px;
            }}
            QComboBox:hover {{
                border-color: {cls.get_theme_value('colors', 'accent')};
            }}
            QComboBox:focus {{
                border-color: {cls.get_theme_value('colors', 'accent')};
                box-shadow: 0 0 0 3px {cls.get_theme_value('colors', 'accent')}33;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {cls.SPACING['lg']}px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-style: solid;
                border-width: 0 2px 2px 0;
                border-color: {cls.get_theme_value('colors', 'text_secondary')};
                width: 8px;
                height: 8px;
                transform: rotate(45deg);
                margin-top: -4px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {cls.RADIUS['md']}px;
                selection-background-color: {cls.get_theme_value('colors', 'bg_selected')};
                color: {cls.get_theme_value('colors', 'text_primary')};
                padding: {cls.SPACING['xs']}px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: {cls.SPACING['xs']}px {cls.SPACING['sm']}px;
                min-height: {cls.SPACING['lg']}px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {cls.get_theme_value('colors', 'bg_selected')};
                color: {cls.get_theme_value('colors', 'text_primary')};
            }}
        """
    
    @classmethod
    def get_radio_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QRadioButton stylesheet."""
        check_color = cls.get_theme_value('colors', variant) or cls.get_theme_value('colors', 'accent')
        text_color = cls.get_theme_value('colors', 'text_primary')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        indicator_size = 14 if size == 'sm' else 18 if size == 'md' else 22
        dot_size = 6 if size == 'sm' else 8 if size == 'md' else 10
        
        return f"""
            QRadioButton {{
                color: {text_color};
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                spacing: {cls.SPACING['xs']}px;
            }}
            QRadioButton::indicator {{
                width: {indicator_size}px;
                height: {indicator_size}px;
                border: 2px solid {cls.get_theme_value('colors', 'border_strong')};
                border-radius: {indicator_size // 2}px;
                background-color: {cls.get_theme_value('colors', 'bg_secondary')};
            }}
            QRadioButton::indicator:checked {{
                border-color: {check_color};
                background-color: {check_color};
                image: none;
            }}
            QRadioButton::indicator:checked::after {{
                content: '';
                width: {dot_size}px;
                height: {dot_size}px;
                border-radius: {dot_size // 2}px;
                background-color: white;
                position: absolute;
                top: {(indicator_size - dot_size) // 2 - 2}px;
                left: {(indicator_size - dot_size) // 2 - 2}px;
            }}
            QRadioButton::indicator:hover {{
                border-color: {cls.get_theme_value('colors', 'accent')};
            }}
            QRadioButton:disabled {{
                color: {cls.get_theme_value('colors', 'text_muted')};
            }}
        """
    
    @classmethod
    def get_spin_box_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QSpinBox stylesheet."""
        bg_color = cls.get_theme_value('colors', 'bg_secondary')
        border_color = cls.get_theme_value('colors', 'border_subtle')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        return f"""
            QSpinBox {{
                background-color: {bg_color};
                color: {cls.get_theme_value('colors', 'text_primary')};
                border: 1px solid {border_color};
                border-radius: {cls.RADIUS['md']}px;
                padding: {cls.SPACING['xs']}px {cls.SPACING['sm']}px;
                padding-right: {cls.SPACING['lg']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                min-height: {cls.SPACING['lg']}px;
            }}
            QSpinBox:hover {{
                border-color: {cls.get_theme_value('colors', 'accent')};
            }}
            QSpinBox:focus {{
                border-color: {cls.get_theme_value('colors', 'accent')};
                box-shadow: 0 0 0 3px {cls.get_theme_value('colors', 'accent')}33;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {cls.get_theme_value('colors', 'bg_tertiary')};
                border: none;
                width: {cls.SPACING['md']}px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {cls.get_theme_value('colors', 'bg_hover')};
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                image: none;
                border-style: solid;
                border-width: 0 2px 2px 0;
                border-color: {cls.get_theme_value('colors', 'text_secondary')};
                width: 6px;
                height: 6px;
            }}
            QSpinBox::up-arrow {{
                transform: rotate(-135deg);
                margin-bottom: 2px;
            }}
            QSpinBox::down-arrow {{
                transform: rotate(45deg);
                margin-top: 2px;
            }}
        """
    
    @classmethod
    def get_group_box_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QGroupBox stylesheet."""
        border_color = cls.get_theme_value('colors', 'border_subtle')
        title_color = cls.get_theme_value('colors', 'text_secondary')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        return f"""
            QGroupBox {{
                border: 1px solid {border_color};
                border-radius: {cls.RADIUS['md']}px;
                margin-top: {cls.SPACING['md']}px;
                padding-top: {cls.SPACING['sm']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
            }}
            QGroupBox::title {{
                color: {title_color};
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: {cls.SPACING['sm']}px;
                padding: 0 {cls.SPACING['xs']}px;
                background-color: {cls.get_theme_value('colors', 'bg_primary')};
                font-weight: {cls.TYPOGRAPHY['font_weight']['medium']};
            }}
        """
    
    @classmethod
    def get_tab_widget_style(cls, variant: str = 'primary', size: str = 'md') -> str:
        """Generate QTabWidget stylesheet."""
        bg_color = cls.get_theme_value('colors', 'bg_secondary')
        border_color = cls.get_theme_value('colors', 'border_subtle')
        selected_color = cls.get_theme_value('colors', 'accent')
        font_size = cls.TYPOGRAPHY['font_size'].get(size, cls.TYPOGRAPHY['font_size']['md'])
        
        return f"""
            QTabWidget::pane {{
                border: 1px solid {border_color};
                background-color: {bg_color};
                border-radius: {cls.RADIUS['md']}px;
                padding: {cls.SPACING['sm']}px;
            }}
            QTabWidget::tab-bar {{
                left: {cls.SPACING['sm']}px;
            }}
            QTabBar::tab {{
                background-color: {cls.get_theme_value('colors', 'bg_tertiary')};
                color: {cls.get_theme_value('colors', 'text_secondary')};
                padding: {cls.SPACING['xs']}px {cls.SPACING['md']}px;
                margin-right: {cls.SPACING['xs']}px;
                border-top-left-radius: {cls.RADIUS['md']}px;
                border-top-right-radius: {cls.RADIUS['md']}px;
                font-family: {cls.TYPOGRAPHY['font_family']['default']};
                font-size: {font_size}px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {bg_color};
                color: {cls.get_theme_value('colors', 'text_primary')};
                border: 1px solid {border_color};
                border-bottom: 1px solid {bg_color};
                padding-bottom: {cls.SPACING['xs'] + 1}px;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {cls.get_theme_value('colors', 'bg_hover')};
                color: {cls.get_theme_value('colors', 'text_primary')};
            }}
            QTabBar::tab:first:selected {{
                margin-left: 0;
            }}
            QTabBar::tab:last:selected {{
                margin-right: 0;
            }}
        """
    
    @classmethod
    def get_tile_base_style(cls) -> str:
        """Get the base style that all tiles must use."""
        return f"""
            /* Base tile container */
            QWidget#tileContainer {{
                background-color: {cls.get_theme_value('colors', 'bg_secondary')};
                border-radius: {cls.RADIUS['md']}px;
            }}
            
            /* Drag handle */
            QFrame#dragHandle {{
                background-color: transparent;
                border-bottom: 1px solid {cls.get_theme_value('colors', 'border_subtle')};
                min-height: {cls.SPACING['md']}px;
            }}
            QFrame#dragHandle:hover {{
                background-color: {cls.get_theme_value('colors', 'overlay_light')};
            }}
            
            /* Close button */
            QPushButton#closeButton {{
                background-color: {cls.get_theme_value('colors', 'bg_tertiary')};
                color: {cls.get_theme_value('colors', 'text_muted')};
                border-radius: {cls.RADIUS['round']}px;
                font-size: 12px;
                padding: 4px;
            }}
            QPushButton#closeButton:hover {{
                background-color: {cls.get_theme_value('colors', 'error')};
                color: white;
            }}
            
            /* Pin button */
            QPushButton#pinButton {{
                background-color: {cls.get_theme_value('colors', 'bg_tertiary')};
                color: {cls.get_theme_value('colors', 'text_muted')};
                border-radius: {cls.RADIUS['round']}px;
                font-size: 12px;
                padding: 4px;
            }}
            QPushButton#pinButton[pinned="true"] {{
                background-color: {cls.get_theme_value('colors', 'accent')};
                color: {cls.get_theme_value('colors', 'text_inverse')};
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
                    comp_errors = cls._validate_component(comp, f"components[{i}]", 0)
                    errors.extend(comp_errors)
        
        return len(errors) == 0, errors
    
    @classmethod
    def _validate_component(cls, component: Dict[str, Any], path: str, depth: int) -> List[str]:
        """Validate a single component specification."""
        errors = []
        
        # Check depth
        if depth > 5:  # Max nesting depth
            errors.append(f"{path}: Component nesting too deep (max depth: 5)")
            return errors
        
        if 'type' not in component:
            errors.append(f"{path}: Missing 'type' field")
        else:
            comp_type = component['type']
            try:
                ComponentType(comp_type)
            except ValueError:
                errors.append(f"{path}: Invalid component type '{comp_type}'")
        
        if 'id' not in component and component.get('type') != ComponentType.SPACER.value:
            errors.append(f"{path}: Missing 'id' field")
        
        # Validate container recursively
        if component.get('type') == ComponentType.CONTAINER.value and 'components' in component:
            for i, sub_comp in enumerate(component['components']):
                sub_errors = cls._validate_component(sub_comp, f"{path}.components[{i}]", depth + 1)
                errors.extend(sub_errors)
        
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
            'component_states': [cs.value for cs in ComponentState],
            'themes': list(cls._themes.keys()),
            'current_theme': cls._current_theme,
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


# Initialize default themes on module load
DesignSystem.init_default_themes()


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