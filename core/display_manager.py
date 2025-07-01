# core/display_manager.py
"""
Display manager abstraction for PinPoint.
Provides display information without Qt dependencies.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger
from core.events import get_event_bus


@dataclass
class DisplayInfo:
    """Information about a display."""
    index: int
    name: str
    x: int
    y: int
    width: int
    height: int
    is_primary: bool
    scale_factor: float = 1.0
    
    @property
    def resolution_string(self) -> str:
        """Get resolution as string."""
        return f"{self.width}x{self.height}"
        
    @property
    def display_name(self) -> str:
        """Get user-friendly display name."""
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.name} ({self.resolution_string}){primary}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "index": self.index,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "is_primary": self.is_primary,
            "scale_factor": self.scale_factor
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DisplayInfo':
        """Create from dictionary."""
        return cls(**data)


class DisplayManager:
    """
    Abstract display manager.
    Provides display information without UI framework dependencies.
    """
    
    def __init__(self):
        """Initialize display manager."""
        self.logger = get_logger("display_manager")
        self.event_bus = get_event_bus()
        self._displays: List[DisplayInfo] = []
        self._selected_index: int = 0
        
        # Initialize with mock data for now
        # Real implementation would query the OS
        self._init_mock_displays()
        
    def _init_mock_displays(self) -> None:
        """Initialize with mock display data for testing."""
        # In real implementation, this would query the OS
        self._displays = [
            DisplayInfo(
                index=0,
                name="Display 1",
                x=0,
                y=0,
                width=1920,
                height=1080,
                is_primary=True,
                scale_factor=1.0
            ),
            DisplayInfo(
                index=1,
                name="Display 2",
                x=1920,
                y=0,
                width=1920,
                height=1080,
                is_primary=False,
                scale_factor=1.0
            )
        ]
        
        self.logger.info(f"Initialized with {len(self._displays)} displays")
        
    def get_displays(self) -> List[DisplayInfo]:
        """
        Get all available displays.
        
        Returns:
            List of display information
        """
        return self._displays.copy()
        
    def get_display(self, index: int) -> Optional[DisplayInfo]:
        """
        Get a specific display by index.
        
        Args:
            index: Display index
            
        Returns:
            Display info or None
        """
        if 0 <= index < len(self._displays):
            return self._displays[index]
        return None
        
    def get_primary_display(self) -> Optional[DisplayInfo]:
        """
        Get the primary display.
        
        Returns:
            Primary display info or None
        """
        for display in self._displays:
            if display.is_primary:
                return display
        return self._displays[0] if self._displays else None
        
    def get_selected_display(self) -> Optional[DisplayInfo]:
        """
        Get the currently selected display.
        
        Returns:
            Selected display info or None
        """
        return self.get_display(self._selected_index)
        
    def select_display(self, index: int) -> bool:
        """
        Select a display.
        
        Args:
            index: Display index to select
            
        Returns:
            True if successful
        """
        if 0 <= index < len(self._displays):
            self._selected_index = index
            self.event_bus.emit("display.selected", {
                "index": index,
                "display": self._displays[index].to_dict()
            })
            return True
        return False
        
    def get_display_count(self) -> int:
        """Get number of available displays."""
        return len(self._displays)
        
    def get_combined_bounds(self) -> Tuple[int, int, int, int]:
        """
        Get the combined bounds of all displays.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        if not self._displays:
            return (0, 0, 0, 0)
            
        min_x = min(d.x for d in self._displays)
        min_y = min(d.y for d in self._displays)
        max_x = max(d.x + d.width for d in self._displays)
        max_y = max(d.y + d.height for d in self._displays)
        
        return (min_x, min_y, max_x, max_y)
        
    def get_display_at_point(self, x: int, y: int) -> Optional[DisplayInfo]:
        """
        Find which display contains a point.
        
        Args:
            x, y: Point coordinates
            
        Returns:
            Display containing the point or None
        """
        for display in self._displays:
            if (display.x <= x < display.x + display.width and
                display.y <= y < display.y + display.height):
                return display
        return None
        
    def refresh_displays(self) -> None:
        """
        Refresh display information.
        In real implementation, would re-query the OS.
        """
        # For now, just emit an event
        self.event_bus.emit("displays.refreshed", {
            "count": len(self._displays)
        })
        
        self.logger.debug("Display information refreshed")
        
    def set_displays(self, displays: List[DisplayInfo]) -> None:
        """
        Set display information (for testing or UI integration).
        
        Args:
            displays: List of display information
        """
        self._displays = displays
        
        # Reset selection if invalid
        if self._selected_index >= len(self._displays):
            self._selected_index = 0
            
        self.event_bus.emit("displays.changed", {
            "count": len(self._displays)
        })


# Global display manager instance
_global_display_manager: Optional[DisplayManager] = None


def get_display_manager() -> DisplayManager:
    """Get the global display manager instance."""
    global _global_display_manager
    if _global_display_manager is None:
        _global_display_manager = DisplayManager()
    return _global_display_manager