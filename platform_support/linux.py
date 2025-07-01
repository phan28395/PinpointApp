# platform_support/linux.py
"""
Linux-specific platform support implementation.
"""

import sys
import platform
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support.base import PlatformSupport, SystemInfo, DisplayInfo


class LinuxPlatform(PlatformSupport):
    """Linux-specific platform implementation."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "linux"
        
    def get_system_info(self) -> SystemInfo:
        """Get Linux system information."""
        return SystemInfo(
            platform="linux",
            version=platform.release(),
            architecture=platform.machine(),
            python_version=platform.python_version()
        )
        
    def get_app_data_dir(self) -> Path:
        """Get Linux app data directory."""
        # Follow XDG Base Directory specification
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            base_dir = Path(xdg_data)
        else:
            base_dir = Path.home() / ".local" / "share"
            
        return base_dir / "pinpoint"
        
    def get_user_config_dir(self) -> Path:
        """Get Linux user config directory."""
        # Follow XDG Base Directory specification
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            base_dir = Path(xdg_config)
        else:
            base_dir = Path.home() / ".config"
            
        return base_dir / "pinpoint"
        
    def get_log_dir(self) -> Path:
        """Get Linux log directory."""
        # Use cache directory for logs
        xdg_cache = os.environ.get('XDG_CACHE_HOME')
        if xdg_cache:
            base_dir = Path(xdg_cache)
        else:
            base_dir = Path.home() / ".cache"
            
        return base_dir / "pinpoint" / "logs"
        
    def get_displays(self) -> List[DisplayInfo]:
        """Get all displays using xrandr."""
        displays = []
        
        try:
            # Use xrandr to get display info
            result = subprocess.run(
                ["xrandr", "--query"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse xrandr output
                display_index = 0
                for line in result.stdout.splitlines():
                    if " connected" in line:
                        parts = line.split()
                        display_name = parts[0]
                        
                        # Find resolution
                        for part in parts:
                            if "x" in part and "+" in part:
                                # Format: WIDTHxHEIGHT+X+Y
                                res_pos = part.split("+")
                                resolution = res_pos[0]
                                x_pos = int(res_pos[1]) if len(res_pos) > 1 else 0
                                y_pos = int(res_pos[2]) if len(res_pos) > 2 else 0
                                
                                width, height = map(int, resolution.split("x"))
                                
                                # Check if primary
                                is_primary = "primary" in line
                                
                                display = DisplayInfo(
                                    index=display_index,
                                    name=display_name,
                                    x=x_pos,
                                    y=y_pos,
                                    width=width,
                                    height=height,
                                    scale_factor=1.0,  # Would need to query from DE
                                    is_primary=is_primary
                                )
                                displays.append(display)
                                display_index += 1
                                break
                                
        except Exception as e:
            self.logger.error(f"Failed to get displays: {e}")
            # Fallback to a default display
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
        """Set window always on top using X11."""
        # This would require python-xlib or calling X11 APIs
        # For now, return False (not implemented)
        self.logger.warning("set_window_always_on_top not implemented for Linux")
        return False
        
    def set_window_click_through(self, window_handle: Any, click_through: bool) -> bool:
        """Set window click-through using X11."""
        # This would require python-xlib or calling X11 APIs
        # For now, return False (not implemented)
        self.logger.warning("set_window_click_through not implemented for Linux")
        return False
        
    def register_startup(self, app_path: str, app_name: str = "PinPoint") -> bool:
        """Register application in Linux startup."""
        try:
            # Create desktop entry for autostart
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / f"{app_name.lower()}.desktop"
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=PinPoint Desktop Widgets
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
                
            # Make it executable
            desktop_file.chmod(0o755)
            
            self.logger.info(f"Registered {app_name} for startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register startup: {e}")
            return False
            
    def unregister_startup(self, app_name: str = "PinPoint") -> bool:
        """Unregister application from Linux startup."""
        try:
            desktop_file = Path.home() / ".config" / "autostart" / f"{app_name.lower()}.desktop"
            
            if desktop_file.exists():
                desktop_file.unlink()
                
            self.logger.info(f"Unregistered {app_name} from startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister startup: {e}")
            return False
            
    def is_startup_registered(self, app_name: str = "PinPoint") -> bool:
        """Check if application is registered for startup."""
        desktop_file = Path.home() / ".config" / "autostart" / f"{app_name.lower()}.desktop"
        return desktop_file.exists()
        
    def show_notification(self, title: str, message: str,
                         icon_path: Optional[str] = None) -> bool:
        """Show Linux notification using notify-send."""
        try:
            cmd = ["notify-send", title, message]
            if icon_path and Path(icon_path).exists():
                cmd.extend(["-i", icon_path])
                
            subprocess.run(cmd, check=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
            return False