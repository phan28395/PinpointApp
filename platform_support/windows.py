# platform_support/windows.py
"""
Windows-specific platform implementation.
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support.base import PlatformBase
from core.constants import APP_NAME


class WindowsPlatform(PlatformBase):
    """Windows-specific functionality."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "windows"
        
    def get_user_data_dir(self) -> Path:
        """Get user data directory."""
        # Use APPDATA for Windows
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / APP_NAME
        # Fallback to home directory
        return Path.home() / f".{APP_NAME.lower()}"
        
    def get_config_dir(self) -> Path:
        """Get config directory."""
        # On Windows, config goes in the same place as data
        return self.get_user_data_dir() / "config"
        
    def get_cache_dir(self) -> Path:
        """Get cache directory."""
        # Use LOCALAPPDATA for cache on Windows
        localappdata = os.environ.get('LOCALAPPDATA')
        if localappdata:
            return Path(localappdata) / APP_NAME / "cache"
        return self.get_user_data_dir() / "cache"
        
    def get_log_dir(self) -> Path:
        """Get log directory."""
        return self.get_user_data_dir() / "logs"
        
    def supports_system_tray(self) -> bool:
        """Windows supports system tray."""
        return True
        
    def get_tray_icon_size(self) -> Tuple[int, int]:
        """Get Windows tray icon size."""
        # Windows typically uses 16x16 or 24x24 for tray icons
        # We'll use 24x24 for better quality on high DPI
        return (24, 24)
        
    def register_startup(self, app_name: str, app_path: str) -> bool:
        """Register app for Windows startup."""
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            # Open or create the key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Set the value
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            
            self.logger.info(f"Registered {app_name} for startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register startup: {e}")
            return False
            
    def unregister_startup(self, app_name: str) -> bool:
        """Unregister app from Windows startup."""
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            # Open the key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Delete the value
            try:
                winreg.DeleteValue(key, app_name)
                self.logger.info(f"Unregistered {app_name} from startup")
                result = True
            except FileNotFoundError:
                # Already unregistered
                result = True
                
            winreg.CloseKey(key)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to unregister startup: {e}")
            return False
            
    def is_startup_registered(self, app_name: str) -> bool:
        """Check if app is registered for startup."""
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            # Open the key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_READ
            )
            
            # Try to read the value
            try:
                winreg.QueryValueEx(key, app_name)
                result = True
            except FileNotFoundError:
                result = False
                
            winreg.CloseKey(key)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to check startup registration: {e}")
            return False
            
    def supports_always_on_top(self) -> bool:
        """Windows supports always-on-top."""
        return True
        
    def supports_transparency(self) -> bool:
        """Windows supports transparency."""
        return True
        
    def get_screen_count(self) -> int:
        """Get number of screens."""
        try:
            # Try to use Qt if available
            from PySide6.QtWidgets import QApplication
            if QApplication.instance():
                return len(QApplication.screens())
        except ImportError:
            pass
            
        # Fallback: assume 1 screen
        return 1
        
    def get_primary_screen_size(self) -> Tuple[int, int]:
        """Get primary screen size."""
        try:
            # Try to use Qt if available
            from PySide6.QtWidgets import QApplication
            if QApplication.instance():
                screen = QApplication.primaryScreen()
                if screen:
                    size = screen.size()
                    return (size.width(), size.height())
        except ImportError:
            pass
            
        # Fallback to ctypes
        try:
            import ctypes
            user32 = ctypes.windll.user32
            return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
        except:
            # Last resort fallback
            return (1920, 1080)
            
    def get_documents_dir(self) -> Path:
        """Get documents directory."""
        # Try to get from Windows known folders
        try:
            import ctypes
            from ctypes import wintypes, windll
            
            CSIDL_PERSONAL = 5  # My Documents
            SHGFP_TYPE_CURRENT = 0
            
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            windll.shell32.SHGetFolderPathW(
                None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf
            )
            
            return Path(buf.value)
        except:
            # Fallback
            return Path.home() / "Documents"
            
    def show_in_file_manager(self, path: Path) -> bool:
        """Show path in Windows Explorer."""
        try:
            if path.is_file():
                # Select the file in Explorer
                subprocess.run(['explorer', '/select,', str(path)])
            else:
                # Open the directory
                subprocess.run(['explorer', str(path)])
            return True
        except Exception as e:
            self.logger.error(f"Failed to show in Explorer: {e}")
            return False
            
    def trash_file(self, path: Path) -> bool:
        """Move file to recycle bin."""
        try:
            # Use send2trash if available
            import send2trash
            send2trash.send2trash(str(path))
            return True
        except ImportError:
            # Try Windows-specific method
            try:
                import ctypes
                from ctypes import wintypes
                
                # SHFileOperation constants
                FO_DELETE = 3
                FOF_ALLOWUNDO = 0x40
                FOF_NOCONFIRMATION = 0x10
                
                # SHFILEOPSTRUCT
                class SHFILEOPSTRUCT(ctypes.Structure):
                    _fields_ = [
                        ("hwnd", wintypes.HWND),
                        ("wFunc", wintypes.UINT),
                        ("pFrom", wintypes.LPCWSTR),
                        ("pTo", wintypes.LPCWSTR),
                        ("fFlags", wintypes.WORD),
                        ("fAnyOperationsAborted", wintypes.BOOL),
                        ("hNameMappings", wintypes.LPVOID),
                        ("lpszProgressTitle", wintypes.LPCWSTR)
                    ]
                
                # Prepare the path (double null-terminated)
                path_str = str(path) + '\0\0'
                
                # Create the struct
                fileop = SHFILEOPSTRUCT()
                fileop.hwnd = None
                fileop.wFunc = FO_DELETE
                fileop.pFrom = path_str
                fileop.pTo = None
                fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION
                
                # Call SHFileOperation
                result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
                return result == 0
                
            except Exception as e:
                self.logger.error(f"Failed to trash file: {e}")
                return False
                
    def get_modifier_key_name(self, modifier: str) -> str:
        """Get Windows-specific modifier key name."""
        modifiers = {
            "ctrl": "Ctrl",
            "alt": "Alt", 
            "shift": "Shift",
            "meta": "Win"
        }
        return modifiers.get(modifier, modifier)