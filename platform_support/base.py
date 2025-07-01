# platform_support/base.py
"""
Platform abstraction base class.
Defines the interface for platform-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger
from core.events import get_event_bus


@dataclass
class SystemInfo:
    """System information."""
    platform: str  # windows, darwin, linux
    version: str
    architecture: str  # x86, x64, arm64
    python_version: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "platform": self.platform,
            "version": self.version,
            "architecture": self.architecture,
            "python_version": self.python_version
        }


@dataclass
class DisplayInfo:
    """Display information."""
    index: int
    name: str
    x: int
    y: int
    width: int
    height: int
    scale_factor: float
    is_primary: bool
    
    @property
    def resolution_string(self) -> str:
        """Get resolution as string."""
        return f"{self.width}x{self.height}"


class PlatformSupport(ABC):
    """
    Abstract base class for platform-specific functionality.
    """
    
    def __init__(self):
        """Initialize platform support."""
        self.logger = get_logger(f"platform.{self.get_platform_name()}")
        self.event_bus = get_event_bus()
        
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get platform name (windows, darwin, linux).
        
        Returns:
            Platform identifier
        """
        pass
        
    @abstractmethod
    def get_system_info(self) -> SystemInfo:
        """
        Get system information.
        
        Returns:
            System information
        """
        pass
        
    @abstractmethod
    def get_app_data_dir(self) -> Path:
        """
        Get application data directory.
        
        Returns:
            Path to app data directory
        """
        pass
        
    @abstractmethod
    def get_user_config_dir(self) -> Path:
        """
        Get user configuration directory.
        
        Returns:
            Path to user config directory
        """
        pass
        
    @abstractmethod
    def get_log_dir(self) -> Path:
        """
        Get log directory.
        
        Returns:
            Path to log directory
        """
        pass
        
    @abstractmethod
    def get_displays(self) -> List[DisplayInfo]:
        """
        Get all available displays.
        
        Returns:
            List of display information
        """
        pass
        
    @abstractmethod
    def get_primary_display(self) -> Optional[DisplayInfo]:
        """
        Get primary display.
        
        Returns:
            Primary display info or None
        """
        pass
        
    @abstractmethod
    def set_window_always_on_top(self, window_handle: Any, on_top: bool) -> bool:
        """
        Set window always on top state.
        
        Args:
            window_handle: Platform-specific window handle
            on_top: Whether to set on top
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    def set_window_click_through(self, window_handle: Any, click_through: bool) -> bool:
        """
        Set window click-through state.
        
        Args:
            window_handle: Platform-specific window handle
            click_through: Whether to make click-through
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    def register_startup(self, app_path: str, app_name: str = "PinPoint") -> bool:
        """
        Register application for startup.
        
        Args:
            app_path: Path to application executable
            app_name: Application name
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    def unregister_startup(self, app_name: str = "PinPoint") -> bool:
        """
        Unregister application from startup.
        
        Args:
            app_name: Application name
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    def is_startup_registered(self, app_name: str = "PinPoint") -> bool:
        """
        Check if application is registered for startup.
        
        Args:
            app_name: Application name
            
        Returns:
            True if registered
        """
        pass
        
    @abstractmethod
    def show_notification(self, title: str, message: str, 
                         icon_path: Optional[str] = None) -> bool:
        """
        Show system notification.
        
        Args:
            title: Notification title
            message: Notification message
            icon_path: Optional icon path
            
        Returns:
            True if successful
        """
        pass
        
    def get_window_handle_from_qt(self, qt_widget: Any) -> Any:
        """
        Get platform window handle from Qt widget.
        
        Args:
            qt_widget: Qt widget
            
        Returns:
            Platform-specific window handle
        """
        # Default implementation
        try:
            return int(qt_widget.winId())
        except Exception as e:
            self.logger.error(f"Failed to get window handle: {e}")
            return None
            
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        dirs = [
            self.get_app_data_dir(),
            self.get_user_config_dir(),
            self.get_log_dir()
        ]
        
        for dir_path in dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Ensured directory exists: {dir_path}")
            except Exception as e:
                self.logger.error(f"Failed to create directory {dir_path}: {e}")
                
    def get_default_paths(self) -> Dict[str, Path]:
        """
        Get all default paths.
        
        Returns:
            Dictionary of path names to paths
        """
        return {
            "app_data": self.get_app_data_dir(),
            "user_config": self.get_user_config_dir(),
            "logs": self.get_log_dir(),
            "data_file": self.get_app_data_dir() / "pinpoint_data.json",
            "config_file": self.get_user_config_dir() / "config.json",
            "log_file": self.get_log_dir() / "pinpoint.log"
        }