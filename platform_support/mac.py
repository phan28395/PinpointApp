# platform_support/mac.py
"""
macOS-specific platform support implementation.
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


class MacPlatform(PlatformSupport):
    """macOS-specific platform implementation."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "darwin"
        
    def get_system_info(self) -> SystemInfo:
        """Get macOS system information."""
        return SystemInfo(
            platform="darwin",
            version=platform.mac_ver()[0],
            architecture=platform.machine(),
            python_version=platform.python_version()
        )
        
    def get_app_data_dir(self) -> Path:
        """Get macOS app data directory."""
        # Use ~/Library/Application Support
        return Path.home() / "Library" / "Application Support" / "PinPoint"
        
    def get_user_config_dir(self) -> Path:
        """Get macOS user config directory."""
        # Use ~/Library/Preferences
        return Path.home() / "Library" / "Preferences" / "PinPoint"
        
    def get_log_dir(self) -> Path:
        """Get macOS log directory."""
        # Use ~/Library/Logs
        return Path.home() / "Library" / "Logs" / "PinPoint"
        
    def get_displays(self) -> List[DisplayInfo]:
        """Get all displays using macOS APIs."""
        displays = []
        
        try:
            # Use system_profiler to get display info
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Parse display data
                # This is simplified - real implementation would parse properly
                display_index = 0
                for item in data.get("SPDisplaysDataType", []):
                    for display_data in item.get("spdisplays_ndrvs", []):
                        # Extract display info
                        resolution = display_data.get("_spdisplays_resolution", "1920 x 1080")
                        width, height = map(int, resolution.split(" x "))
                        
                        display = DisplayInfo(
                            index=display_index,
                            name=display_data.get("_name", f"Display {display_index + 1}"),
                            x=0,  # macOS doesn't easily provide position
                            y=0,
                            width=width,
                            height=height,
                            scale_factor=2.0 if "Retina" in resolution else 1.0,
                            is_primary=display_index == 0  # First is usually primary
                        )
                        displays.append(display)
                        display_index += 1
                        
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
        return displays[0] if displays else None
        
    def set_window_always_on_top(self, window_handle: Any, on_top: bool) -> bool:
        """Set window always on top using macOS APIs."""
        # This would require PyObjC or calling macOS APIs
        # For now, return False (not implemented)
        self.logger.warning("set_window_always_on_top not implemented for macOS")
        return False
        
    def set_window_click_through(self, window_handle: Any, click_through: bool) -> bool:
        """Set window click-through using macOS APIs."""
        # This would require PyObjC or calling macOS APIs
        # For now, return False (not implemented)
        self.logger.warning("set_window_click_through not implemented for macOS")
        return False
        
    def register_startup(self, app_path: str, app_name: str = "PinPoint") -> bool:
        """Register application in macOS startup."""
        try:
            # Create launch agent plist
            plist_name = f"com.pinpoint.{app_name}.plist"
            plist_path = Path.home() / "Library" / "LaunchAgents" / plist_name
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pinpoint.{app_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
            
            # Ensure directory exists
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write plist
            with open(plist_path, 'w') as f:
                f.write(plist_content)
                
            # Load the launch agent
            subprocess.run(["launchctl", "load", str(plist_path)], check=True)
            
            self.logger.info(f"Registered {app_name} for startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register startup: {e}")
            return False
            
    def unregister_startup(self, app_name: str = "PinPoint") -> bool:
        """Unregister application from macOS startup."""
        try:
            plist_name = f"com.pinpoint.{app_name}.plist"
            plist_path = Path.home() / "Library" / "LaunchAgents" / plist_name
            
            if plist_path.exists():
                # Unload the launch agent
                subprocess.run(["launchctl", "unload", str(plist_path)], check=True)
                
                # Remove plist file
                plist_path.unlink()
                
            self.logger.info(f"Unregistered {app_name} from startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister startup: {e}")
            return False
            
    def is_startup_registered(self, app_name: str = "PinPoint") -> bool:
        """Check if application is registered for startup."""
        plist_name = f"com.pinpoint.{app_name}.plist"
        plist_path = Path.home() / "Library" / "LaunchAgents" / plist_name
        return plist_path.exists()
        
    def show_notification(self, title: str, message: str,
                         icon_path: Optional[str] = None) -> bool:
        """Show macOS notification."""
        try:
            # Use osascript to show notification
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
            return False