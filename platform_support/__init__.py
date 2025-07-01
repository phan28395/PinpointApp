# platform_support/__init__.py
"""
Platform support module for PinPoint.
Provides cross-platform abstractions for system-specific functionality.
"""

import sys
import platform
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support.base import PlatformSupport, SystemInfo, DisplayInfo

# Import platform-specific implementations
if sys.platform == "win32":
    from platform_support.windows import WindowsPlatform
elif sys.platform == "darwin":
    from platform_support.mac import MacPlatform
elif sys.platform.startswith("linux"):
    from platform_support.linux import LinuxPlatform
else:
    # Fallback for unknown platforms
    WindowsPlatform = None
    MacPlatform = None
    LinuxPlatform = None


# Global platform instance
_global_platform: Optional[PlatformSupport] = None


def get_platform() -> PlatformSupport:
    """
    Get the platform-specific implementation.
    
    Returns:
        Platform support instance
        
    Raises:
        NotImplementedError: If platform is not supported
    """
    global _global_platform
    
    if _global_platform is None:
        # Create platform-specific instance
        if sys.platform == "win32" and WindowsPlatform:
            _global_platform = WindowsPlatform()
        elif sys.platform == "darwin" and MacPlatform:
            _global_platform = MacPlatform()
        elif sys.platform.startswith("linux") and LinuxPlatform:
            _global_platform = LinuxPlatform()
        else:
            raise NotImplementedError(f"Platform '{sys.platform}' is not supported")
            
        # Ensure directories exist
        _global_platform.ensure_directories()
        
    return _global_platform


def get_platform_name() -> str:
    """
    Get the current platform name.
    
    Returns:
        Platform name (windows, darwin, linux)
    """
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "darwin"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        return sys.platform


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def is_mac() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform.startswith("linux")


__all__ = [
    # Base classes
    'PlatformSupport', 'SystemInfo', 'DisplayInfo',
    
    # Platform implementations
    'WindowsPlatform', 'MacPlatform', 'LinuxPlatform',
    
    # Functions
    'get_platform', 'get_platform_name',
    'is_windows', 'is_mac', 'is_linux',
]