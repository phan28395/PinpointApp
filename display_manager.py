# pinpoint/display_manager.py

from PySide6.QtCore import QObject, Signal, QRect, QPoint
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QApplication
from typing import List, Dict, Optional, Tuple


class DisplayInfo:
    """Information about a display/monitor."""
    
    def __init__(self, screen: QScreen, index: int):
        self.screen = screen
        self.index = index
        self.name = screen.name()
        self.geometry = screen.geometry()  # QRect with position and size
        self.available_geometry = screen.availableGeometry()  # Excluding taskbars
        self.physical_size = screen.physicalSize()  # Physical size in mm
        self.dpi = screen.physicalDotsPerInch()
        self.device_pixel_ratio = screen.devicePixelRatio()
        self.is_primary = screen == QApplication.primaryScreen()
        
    @property
    def width(self) -> int:
        return self.geometry.width()
        
    @property
    def height(self) -> int:
        return self.geometry.height()
        
    @property
    def x(self) -> int:
        return self.geometry.x()
        
    @property
    def y(self) -> int:
        return self.geometry.y()
        
    @property
    def resolution_string(self) -> str:
        return f"{self.width}x{self.height}"
        
    @property
    def display_name(self) -> str:
        """Returns a user-friendly name for the display, preferring the real monitor name."""
        primary_indicator = " (Primary)" if self.is_primary else ""
        
        # Use the real monitor name if the OS provides it, otherwise fall back to a generic name.
        name_to_show = self.name if self.name else f"Display {self.index + 1}"
        
        return f"{name_to_show} ({self.resolution_string}){primary_indicator}"        
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "index": self.index,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "dpi": self.dpi,
            "is_primary": self.is_primary
        }


class DisplayManager(QObject):
    """Manages display detection and coordinate transformation."""
    
    displays_changed = Signal()
    display_selected = Signal(int)  # Display index
    
    def __init__(self):
        super().__init__()
        self.displays: List[DisplayInfo] = []
        self.selected_display_index: Optional[int] = None
        self._app = QApplication.instance()
        
        # Connect to display change signals
        if self._app:
            self._app.primaryScreenChanged.connect(self._on_displays_changed)
            self._app.screenAdded.connect(self._on_displays_changed)
            self._app.screenRemoved.connect(self._on_displays_changed)
            
        # Initial detection
        self.refresh_displays()
        
    def refresh_displays(self):
        """Detect all available displays."""
        self.displays.clear()
        
        if not self._app:
            return
            
        screens = self._app.screens()
        for i, screen in enumerate(screens):
            display_info = DisplayInfo(screen, i)
            self.displays.append(display_info)
            
        # Select primary display by default
        if not self.selected_display_index and self.displays:
            for i, display in enumerate(self.displays):
                if display.is_primary:
                    self.selected_display_index = i
                    break
            else:
                self.selected_display_index = 0
                
        self.displays_changed.emit()
        
    def _on_displays_changed(self):
        """Handle display configuration changes."""
        self.refresh_displays()
        
    def get_display_count(self) -> int:
        """Get the number of available displays."""
        return len(self.displays)
        
    def get_display(self, index: int) -> Optional[DisplayInfo]:
        """Get display info by index."""
        if 0 <= index < len(self.displays):
            return self.displays[index]
        return None
        
    def get_selected_display(self) -> Optional[DisplayInfo]:
        """Get the currently selected display."""
        if self.selected_display_index is not None:
            return self.get_display(self.selected_display_index)
        return None
        
    def select_display(self, index: int):
        """Select a display by index."""
        if 0 <= index < len(self.displays):
            self.selected_display_index = index
            self.display_selected.emit(index)
            
    def get_all_displays_info(self) -> List[Dict]:
        """Get information about all displays."""
        return [display.to_dict() for display in self.displays]
        
    def get_combined_geometry(self) -> QRect:
        """Get the combined geometry of all displays."""
        if not self.displays:
            return QRect()
            
        # Find the bounding rectangle of all displays
        min_x = min(d.x for d in self.displays)
        min_y = min(d.y for d in self.displays)
        max_x = max(d.x + d.width for d in self.displays)
        max_y = max(d.y + d.height for d in self.displays)
        
        return QRect(min_x, min_y, max_x - min_x, max_y - min_y)
        
    def editor_to_screen_coords(self, editor_x: float, editor_y: float, 
                               editor_scale: float = 1.0) -> Tuple[int, int]:
        """Convert editor coordinates to screen coordinates."""
        display = self.get_selected_display()
        if not display:
            return int(editor_x), int(editor_y)
            
        # Apply scaling and offset to map to display
        screen_x = int(editor_x / editor_scale) + display.x
        screen_y = int(editor_y / editor_scale) + display.y
        
        return screen_x, screen_y
        
    def screen_to_editor_coords(self, screen_x: int, screen_y: int,
                               editor_scale: float = 1.0) -> Tuple[float, float]:
        """Convert screen coordinates to editor coordinates."""
        display = self.get_selected_display()
        if not display:
            return float(screen_x), float(screen_y)
            
        # Remove display offset and apply scaling
        editor_x = (screen_x - display.x) * editor_scale
        editor_y = (screen_y - display.y) * editor_scale
        
        return editor_x, editor_y
        
    def get_display_at_point(self, x: int, y: int) -> Optional[DisplayInfo]:
        """Find which display contains the given point."""
        point = QPoint(x, y)
        for display in self.displays:
            if display.geometry.contains(point):
                return display
        return None
        
    def calculate_editor_scale(self, editor_width: int, editor_height: int,
                              padding: int = 50) -> float:
        """Calculate scale to fit display in editor with padding."""
        display = self.get_selected_display()
        if not display:
            return 1.0
            
        # Calculate scale to fit display in editor
        available_width = editor_width - (2 * padding)
        available_height = editor_height - (2 * padding)
        
        if available_width <= 0 or available_height <= 0:
            return 1.0
            
        scale_x = available_width / display.width
        scale_y = available_height / display.height
        
        # Use the smaller scale to ensure it fits
        return min(scale_x, scale_y, 1.0)  # Don't scale up beyond 1:1
        
    def get_display_info_text(self, display_index: int) -> str:
        """Get formatted information about a display."""
        display = self.get_display(display_index)
        if not display:
            return "Unknown display"
            
        info = f"{display.display_name}\n"
        info += f"Resolution: {display.resolution_string}\n"
        info += f"Position: ({display.x}, {display.y})\n"
        info += f"DPI: {display.dpi:.0f}\n"
        info += f"Scale Factor: {display.device_pixel_ratio:.1f}x"
        
        return info


# Global instance
_display_manager = None

def get_display_manager() -> DisplayManager:
    """Get the global display manager instance."""
    global _display_manager
    if _display_manager is None:
        _display_manager = DisplayManager()
    return _display_manager