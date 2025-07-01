# platform_support/base.py
"""
Platform abstraction interface for PinPoint.
Defines the interface that platform-specific implementations must follow.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import sys
import platform

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger


class PlatformBase(ABC):
    """
    Abstract base class for platform-specific functionality.
    Each platform (Windows, Mac, Linux) implements this interface.
    """
    
    def __init__(self):
        """Initialize platform base."""
        self.logger = get_logger(f"platform.{self.get_platform_name()}")
        
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name.
        
        Returns:
            Platform name (e.g., "windows", "mac", "linux")
        """
        pass
        
    @abstractmethod
    def get_user_data_dir(self) -> Path:
        """
        Get the user data directory for the application.
        
        Returns:
            Path to user data directory
        """
        pass
        
    @abstractmethod
    def get_config_dir(self) -> Path:
        """
        Get the configuration directory.
        
        Returns:
            Path to config directory
        """
        pass
        
    @abstractmethod
    def get_cache_dir(self) -> Path:
        """
        Get the cache directory.
        
        Returns:
            Path to cache directory
        """
        pass
        
    @abstractmethod
    def get_log_dir(self) -> Path:
        """
        Get the log directory.
        
        Returns:
            Path to log directory
        """
        pass
        
    def ensure_directories(self) -> None:
        """Ensure all platform directories exist."""
        dirs = [
            self.get_user_data_dir(),
            self.get_config_dir(),
            self.get_cache_dir(),
            self.get_log_dir()
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory: {directory}")
            
    # System tray support
    @abstractmethod
    def supports_system_tray(self) -> bool:
        """
        Check if platform supports system tray.
        
        Returns:
            True if system tray is supported
        """
        pass
        
    @abstractmethod
    def get_tray_icon_size(self) -> Tuple[int, int]:
        """
        Get recommended system tray icon size.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        pass
        
    # Startup/autostart support
    @abstractmethod
    def register_startup(self, app_name: str, app_path: str) -> bool:
        """
        Register application to start at system startup.
        
        Args:
            app_name: Application name
            app_path: Path to application executable
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    def unregister_startup(self, app_name: str) -> bool:
        """
        Unregister application from system startup.
        
        Args:
            app_name: Application name
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    def is_startup_registered(self, app_name: str) -> bool:
        """
        Check if application is registered for startup.
        
        Args:
            app_name: Application name
            
        Returns:
            True if registered
        """
        pass
        
    # Window management
    @abstractmethod
    def supports_always_on_top(self) -> bool:
        """
        Check if platform supports always-on-top windows.
        
        Returns:
            True if supported
        """
        pass
        
    @abstractmethod
    def supports_transparency(self) -> bool:
        """
        Check if platform supports window transparency.
        
        Returns:
            True if supported
        """
        pass
        
    @abstractmethod
    def get_screen_count(self) -> int:
        """
        Get number of screens/monitors.
        
        Returns:
            Number of screens
        """
        pass
        
    @abstractmethod
    def get_primary_screen_size(self) -> Tuple[int, int]:
        """
        Get primary screen size.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        pass
        
    # File system
    @abstractmethod
    def get_documents_dir(self) -> Path:
        """
        Get user's documents directory.
        
        Returns:
            Path to documents directory
        """
        pass
        
    @abstractmethod
    def show_in_file_manager(self, path: Path) -> bool:
        """
        Open file manager and show the given path.
        
        Args:
            path: Path to show
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    def trash_file(self, path: Path) -> bool:
        """
        Move file to trash/recycle bin.
        
        Args:
            path: File to trash
            
        Returns:
            True if successful
        """
        pass
        
    # System info
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dictionary with system info
        """
        return {
            "platform": self.get_platform_name(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "supports_tray": self.supports_system_tray(),
            "supports_transparency": self.supports_transparency(),
            "screen_count": self.get_screen_count()
        }
        
    # Keyboard shortcuts
    def get_modifier_key_name(self, modifier: str) -> str:
        """
        Get platform-specific modifier key name.
        
        Args:
            modifier: Generic modifier ("ctrl", "alt", "shift", "meta")
            
        Returns:
            Platform-specific name
        """
        # Override in platform-specific classes if needed
        modifiers = {
            "ctrl": "Ctrl",
            "alt": "Alt",
            "shift": "Shift",
            "meta": "Win"  # Windows key, Cmd on Mac
        }
        return modifiers.get(modifier, modifier)
        
    def format_shortcut(self, modifiers: List[str], key: str) -> str:
        """
        Format keyboard shortcut for display.
        
        Args:
            modifiers: List of modifiers
            key: Key name
            
        Returns:
            Formatted shortcut string
        """
        parts = [self.get_modifier_key_name(m) for m in modifiers]
        parts.append(key.upper())
        return "+".join(parts)