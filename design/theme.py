# design/theme.py
"""
Basic theming system for PinPoint.
Defines colors, fonts, and visual properties.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger


@dataclass
class ColorScheme:
    """Color scheme for a theme."""
    # Background colors
    bg_primary: str = "#1a1a1a"
    bg_secondary: str = "#242424"
    bg_tertiary: str = "#2a2a2a"
    bg_hover: str = "#303030"
    bg_selected: str = "#0d7377"
    
    # Text colors
    text_primary: str = "#e0e0e0"
    text_secondary: str = "#999999"
    text_muted: str = "#666666"
    text_inverse: str = "#1a1a1a"
    
    # Accent colors
    accent: str = "#14ffec"
    accent_hover: str = "#00e5d6"
    accent_muted: str = "#0a9b91"
    
    # Semantic colors
    success: str = "#4ade80"
    warning: str = "#fbbf24"
    error: str = "#f87171"
    info: str = "#60a5fa"
    
    # UI colors
    border_subtle: str = "#333333"
    border_strong: str = "#555555"
    shadow: str = "rgba(0, 0, 0, 0.3)"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


@dataclass
class Typography:
    """Typography settings for a theme."""
    # Font families
    font_family_default: str = "Arial, sans-serif"
    font_family_mono: str = "Consolas, monospace"
    
    # Font sizes (in pixels)
    font_size_xs: int = 11
    font_size_sm: int = 13
    font_size_md: int = 14
    font_size_lg: int = 16
    font_size_xl: int = 20
    font_size_xxl: int = 24
    
    # Font weights
    font_weight_light: int = 300
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_bold: int = 700
    
    # Line heights
    line_height_tight: float = 1.2
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.75
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


@dataclass  
class Spacing:
    """Spacing values for a theme."""
    # Base unit
    unit: int = 8
    
    # Spacing scale
    xs: int = 8   # 1 unit
    sm: int = 16  # 2 units
    md: int = 24  # 3 units
    lg: int = 32  # 4 units
    xl: int = 40  # 5 units
    xxl: int = 48 # 6 units
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


@dataclass
class Effects:
    """Visual effects for a theme."""
    # Border radius
    radius_sm: int = 4
    radius_md: int = 8
    radius_lg: int = 12
    radius_xl: int = 16
    radius_full: int = 9999
    
    # Shadows
    shadow_sm: str = "0 1px 2px rgba(0, 0, 0, 0.05)"
    shadow_md: str = "0 4px 6px rgba(0, 0, 0, 0.1)"
    shadow_lg: str = "0 10px 15px rgba(0, 0, 0, 0.1)"
    shadow_xl: str = "0 20px 25px rgba(0, 0, 0, 0.1)"
    
    # Transitions
    transition_fast: str = "150ms ease-in-out"
    transition_normal: str = "250ms ease-in-out"
    transition_slow: str = "350ms ease-in-out"
    
    # Opacity
    opacity_disabled: float = 0.5
    opacity_hover: float = 0.8
    opacity_backdrop: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


class Theme:
    """Complete theme definition."""
    
    def __init__(self, 
                 name: str,
                 colors: Optional[ColorScheme] = None,
                 typography: Optional[Typography] = None,
                 spacing: Optional[Spacing] = None,
                 effects: Optional[Effects] = None):
        """
        Initialize theme.
        
        Args:
            name: Theme name
            colors: Color scheme
            typography: Typography settings
            spacing: Spacing values
            effects: Visual effects
        """
        self.name = name
        self.colors = colors or ColorScheme()
        self.typography = typography or Typography()
        self.spacing = spacing or Spacing()
        self.effects = effects or Effects()
        self.logger = get_logger(f"theme.{name}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary."""
        return {
            "name": self.name,
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "effects": self.effects.to_dict()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """Create theme from dictionary."""
        return cls(
            name=data["name"],
            colors=ColorScheme(**data.get("colors", {})),
            typography=Typography(**data.get("typography", {})),
            spacing=Spacing(**data.get("spacing", {})),
            effects=Effects(**data.get("effects", {}))
        )
        
    def get_color(self, color_name: str, default: str = "#000000") -> str:
        """
        Get a color value by name.
        
        Args:
            color_name: Name of the color
            default: Default if not found
            
        Returns:
            Color value
        """
        return getattr(self.colors, color_name, default)
        
    def get_spacing(self, size: str, default: int = 8) -> int:
        """
        Get a spacing value by size.
        
        Args:
            size: Size name (xs, sm, md, etc.)
            default: Default if not found
            
        Returns:
            Spacing value in pixels
        """
        return getattr(self.spacing, size, default)


class ThemeManager:
    """Manages available themes."""
    
    def __init__(self):
        """Initialize theme manager."""
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None
        self.logger = get_logger("theme_manager")
        
        # Register built-in themes
        self._register_builtin_themes()
        
    def _register_builtin_themes(self):
        """Register built-in themes."""
        # Dark theme (default)
        self.register_theme(Theme("dark"))
        
        # Light theme
        light_colors = ColorScheme(
            bg_primary="#ffffff",
            bg_secondary="#f5f5f5",
            bg_tertiary="#eeeeee",
            bg_hover="#e0e0e0",
            bg_selected="#1976d2",
            text_primary="#212121",
            text_secondary="#666666",
            text_muted="#999999",
            text_inverse="#ffffff",
            accent="#1976d2",
            accent_hover="#1565c0",
            accent_muted="#90caf9",
            border_subtle="#e0e0e0",
            border_strong="#bdbdbd",
            shadow="rgba(0, 0, 0, 0.1)"
        )
        self.register_theme(Theme("light", colors=light_colors))
        
        # High contrast theme
        contrast_colors = ColorScheme(
            bg_primary="#000000",
            bg_secondary="#111111",
            bg_tertiary="#222222",
            bg_hover="#333333",
            bg_selected="#ffffff",
            text_primary="#ffffff",
            text_secondary="#dddddd",
            text_muted="#aaaaaa",
            text_inverse="#000000",
            accent="#ffff00",
            accent_hover="#ffdd00",
            accent_muted="#999900",
            border_subtle="#444444",
            border_strong="#888888",
            shadow="rgba(255, 255, 255, 0.2)"
        )
        self.register_theme(Theme("high_contrast", colors=contrast_colors))
        
        # Set default theme
        self.current_theme = self.themes["dark"]
        self.logger.info(f"Registered {len(self.themes)} built-in themes")
        
    def register_theme(self, theme: Theme) -> None:
        """
        Register a theme.
        
        Args:
            theme: Theme to register
        """
        self.themes[theme.name] = theme
        self.logger.debug(f"Registered theme: {theme.name}")
        
    def get_theme(self, name: str) -> Optional[Theme]:
        """
        Get a theme by name.
        
        Args:
            name: Theme name
            
        Returns:
            Theme or None
        """
        return self.themes.get(name)
        
    def set_current_theme(self, name: str) -> bool:
        """
        Set the current theme.
        
        Args:
            name: Theme name
            
        Returns:
            True if successful
        """
        theme = self.get_theme(name)
        if theme:
            self.current_theme = theme
            self.logger.info(f"Set current theme to: {name}")
            return True
        return False
        
    def get_current_theme(self) -> Theme:
        """
        Get the current theme.
        
        Returns:
            Current theme (never None)
        """
        return self.current_theme or self.themes["dark"]
        
    def list_themes(self) -> list[str]:
        """
        List available theme names.
        
        Returns:
            List of theme names
        """
        return list(self.themes.keys())


# Global theme manager
_global_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _global_theme_manager
    if _global_theme_manager is None:
        _global_theme_manager = ThemeManager()
    return _global_theme_manager