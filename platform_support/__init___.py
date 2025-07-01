# platform_support/__init__.py
"""
Platform support module for PinPoint.
Provides OS-specific functionality abstraction.
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support.base import PlatformBase
from core.logger import get_logger


# Global platform instance
_platform_instance: Optional[PlatformBase] = None


def get_current_platform() -> PlatformBase:
    """
    Get the current platform implementation.
    
    Returns:
        Platform implementation for the current OS
        
    Raises:
        NotImplementedError: If platform is not supported
    """
    global _platform_instance
    
    if _platform_instance is None:
        logger = get_logger("platform")
        
        system = sys.platform.lower()
        
        if system.startswith('win'):
            from platform_support.windows import WindowsPlatform
            _platform_instance = WindowsPlatform()
            logger.info("Initialized Windows platform")
            
        elif system == 'darwin':
            from platform_support.mac import MacPlatform
            _platform_instance = MacPlatform()
            logger.info("Initialized macOS platform")
            
        elif system.startswith('linux'):
            from platform_support.linux import LinuxPlatform
            _platform_instance = LinuxPlatform()
            logger.info("Initialized Linux platform")
            
        else:
            raise NotImplementedError(f"Platform '{system}' is not supported")
            
        # Ensure directories exist
        _platform_instance.ensure_directories()
        
    return _platform_instance


# Convenience exports
__all__ = [
    'PlatformBase',
    'get_current_platform',
]