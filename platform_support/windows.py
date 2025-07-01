# platform_support/windows.py
"""
Windows-specific platform support implementation.
"""

import sys
import platform
import os
from pathlib import Path
from typing import List, Optional, Any
import ctypes
import ctypes.wintypes
import winreg

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support.base import PlatformSupport, SystemInfo, DisplayInfo


class WindowsPlatform(PlatformSupport):
    """Windows-specific platform implementation."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "windows"
        
    def get_system_info(self) -> SystemInfo:
        """Get Windows system information."""
        return SystemInfo(
            platform="windows",
            version=platform.version(),
            architecture=platform.machine(),
            python_version=platform.python_version()
        )
        
    def get_app_data_dir(self) -> Path:
        """Get Windows app data directory."""
        # Use LOCALAPPDATA environment variable
        app_data = os.environ.get('LOCALAPPDATA')
        if not app_data:
            # Fallback to user home
            app_data = Path.home() / "AppData" / "Local"
        else:
            app_data = Path(app_data)
            
        return app_data / "PinPoint"
        
    def get_user_config_dir(self) -> Path:
        """Get Windows user config directory."""
        # Use APPDATA (roaming) for config
        config_dir = os.environ.get('APPDATA')
        if not config_dir:
            # Fallback to user home
            config_dir = Path.home() / "AppData" / "Roaming"
        else:
            config_dir = Path(config_dir)
            
        return config_dir / "PinPoint"
        
    def get_log_dir(self) -> Path:
        """Get Windows log directory."""
        # Use local app data for logs
        return self.get_app_data_dir() / "logs"
        
    def get_displays(self) -> List[DisplayInfo]:
        """Get all displays using Windows API."""
        displays = []
        
        # Define MONITORINFOEXW structure
        class MONITORINFOEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", ctypes.wintypes.RECT),
                ("rcWork", ctypes.wintypes.RECT),
                ("dwFlags", ctypes.c_ulong),
                ("szDevice", ctypes.c_wchar * 32)
            ]
        
        # Define callback for EnumDisplayMonitors
        def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            # Get monitor info
            monitor_info = MONITORINFOEXW()
            monitor_info.cbSize = ctypes.sizeof(monitor_info)
            
            if ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(monitor_info)):
                # Extract display info
                rect = monitor_info.rcMonitor
                is_primary = bool(monitor_info.dwFlags & 1)  # MONITORINFOF_PRIMARY
                
                # Get DPI for scale factor
                dpi_x = ctypes.c_uint()
                dpi_y = ctypes.c_uint()
                try:
                    # Try newer API first (Windows 8.1+)
                    ctypes.windll.shcore.GetDpiForMonitor(
                        hMonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y)
                    )
                    scale_factor = dpi_x.value / 96.0
                except:
                    # Fallback to 100% scaling
                    scale_factor = 1.0
                
                display = DisplayInfo(
                    index=len(displays),
                    name=monitor_info.szDevice.strip('\x00'),
                    x=rect.left,
                    y=rect.top,
                    width=rect.right - rect.left,
                    height=rect.bottom - rect.top,
                    scale_factor=scale_factor,
                    is_primary=is_primary
                )
                displays.append(display)
            return True
        
        # Create callback
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.wintypes.RECT),
            ctypes.c_ulong
        )
        callback = MonitorEnumProc(monitor_enum_proc)
        
        # Enumerate monitors
        ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0)
        
        # If no displays found, add a default one
        if not displays:
            self.logger.warning("No displays found, adding default display")
            displays.append(DisplayInfo(
                index=0,
                name="Display 1",
                x=0,
                y=0,
                width=1920,
                height=1080,
                scale_factor=1.0,
                is_primary=True
            ))
        
        return displays
        
    def get_primary_display(self) -> Optional[DisplayInfo]:
        """Get primary display."""
        displays = self.get_displays()
        for display in displays:
            if display.is_primary:
                return display
        return displays[0] if displays else None
        
    def set_window_always_on_top(self, window_handle: Any, on_top: bool) -> bool:
        """Set window always on top using Windows API."""
        if not isinstance(window_handle, int):
            try:
                window_handle = int(window_handle)
            except:
                self.logger.error("Invalid window handle")
                return False
                
        try:
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            
            ctypes.windll.user32.SetWindowPos(
                window_handle,
                HWND_TOPMOST if on_top else HWND_NOTOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set always on top: {e}")
            return False
            
    def set_window_click_through(self, window_handle: Any, click_through: bool) -> bool:
        """Set window click-through using Windows API."""
        if not isinstance(window_handle, int):
            try:
                window_handle = int(window_handle)
            except:
                self.logger.error("Invalid window handle")
                return False
                
        try:
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            
            # Get current style
            style = ctypes.windll.user32.GetWindowLongW(window_handle, GWL_EXSTYLE)
            
            if click_through:
                # Add layered and transparent
                style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
            else:
                # Remove transparent (keep layered for transparency)
                style &= ~WS_EX_TRANSPARENT
                
            ctypes.windll.user32.SetWindowLongW(window_handle, GWL_EXSTYLE, style)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set click-through: {e}")
            return False
            
    def register_startup(self, app_path: str, app_name: str = "PinPoint") -> bool:
        """Register application in Windows startup."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                               winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                
            self.logger.info(f"Registered {app_name} for startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register startup: {e}")
            return False
            
    def unregister_startup(self, app_name: str = "PinPoint") -> bool:
        """Unregister application from Windows startup."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                               winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, app_name)
                
            self.logger.info(f"Unregistered {app_name} from startup")
            return True
            
        except FileNotFoundError:
            # Already not registered
            return True
        except Exception as e:
            self.logger.error(f"Failed to unregister startup: {e}")
            return False
            
    def is_startup_registered(self, app_name: str = "PinPoint") -> bool:
        """Check if application is registered for startup."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                               winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, app_name)
                return True
                
        except FileNotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Failed to check startup registration: {e}")
            return False
            
    def show_notification(self, title: str, message: str,
                         icon_path: Optional[str] = None) -> bool:
        """Show Windows notification using ctypes."""
        try:
            # Simple MessageBox for now
            # In production, would use Windows Toast notifications
            ctypes.windll.user32.MessageBoxW(
                0,
                message,
                title,
                0x40  # MB_ICONINFORMATION
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
            return False