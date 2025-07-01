# platform_support/mac.py
"""
macOS-specific platform implementation.
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple
import sys
import plistlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support.base import PlatformBase
from core.constants import APP_NAME


class MacPlatform(PlatformBase):
    """macOS-specific functionality."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "mac"
        
    def get_user_data_dir(self) -> Path:
        """Get user data directory."""
        # macOS: ~/Library/Application Support/AppName
        return Path.home() / "Library" / "Application Support" / APP_NAME
        
    def get_config_dir(self) -> Path:
        """Get config directory."""
        # macOS: ~/Library/Preferences/AppName
        return Path.home() / "Library" / "Preferences" / APP_NAME
        
    def get_cache_dir(self) -> Path:
        """Get cache directory."""
        # macOS: ~/Library/Caches/AppName
        return Path.home() / "Library" / "Caches" / APP_NAME
        
    def get_log_dir(self) -> Path:
        """Get log directory."""
        # macOS: ~/Library/Logs/AppName
        return Path.home() / "Library" / "Logs" / APP_NAME
        
    def supports_system_tray(self) -> bool:
        """macOS supports menu bar (system tray equivalent)."""
        return True
        
    def get_tray_icon_size(self) -> Tuple[int, int]:
        """Get macOS menu bar icon size."""
        # macOS menu bar icons are typically 18x18 or 22x22
        # Use 22x22 for better appearance
        return (22, 22)
        
    def register_startup(self, app_name: str, app_path: str) -> bool:
        """Register app for macOS startup using LaunchAgents."""
        try:
            # Create LaunchAgent plist
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(exist_ok=True)
            
            plist_path = launch_agents_dir / f"com.{APP_NAME.lower()}.{app_name}.plist"
            
            # Create plist content
            plist_dict = {
                "Label": f"com.{APP_NAME.lower()}.{app_name}",
                "ProgramArguments": [app_path],
                "RunAtLoad": True,
                "KeepAlive": False,
                "LaunchOnlyOnce": True
            }
            
            # Write plist file
            with open(plist_path, 'wb') as f:
                plistlib.dump(plist_dict, f)
                
            # Load the launch agent
            subprocess.run(['launchctl', 'load', str(plist_path)], check=True)
            
            self.logger.info(f"Registered {app_name} for startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register startup: {e}")
            return False
            
    def unregister_startup(self, app_name: str) -> bool:
        """Unregister app from macOS startup."""
        try:
            plist_path = (Path.home() / "Library" / "LaunchAgents" / 
                         f"com.{APP_NAME.lower()}.{app_name}.plist")
            
            if plist_path.exists():
                # Unload the launch agent
                subprocess.run(['launchctl', 'unload', str(plist_path)], check=True)
                
                # Remove the plist file
                plist_path.unlink()
                
            self.logger.info(f"Unregistered {app_name} from startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister startup: {e}")
            return False
            
    def is_startup_registered(self, app_name: str) -> bool:
        """Check if app is registered for startup."""
        plist_path = (Path.home() / "Library" / "LaunchAgents" / 
                     f"com.{APP_NAME.lower()}.{app_name}.plist")
        return plist_path.exists()
        
    def supports_always_on_top(self) -> bool:
        """macOS supports always-on-top windows."""
        return True
        
    def supports_transparency(self) -> bool:
        """macOS supports transparency."""
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
            
        # Try using system_profiler
        try:
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType', '-json'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                # Count displays in the data
                # This is simplified - actual parsing would be more complex
                return 1
        except:
            pass
            
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
            
        # Fallback: use system_profiler
        try:
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Parse output for resolution
                for line in result.stdout.splitlines():
                    if 'Resolution:' in line:
                        # Extract resolution (e.g., "2560 x 1440")
                        parts = line.split('Resolution:')[1].strip().split('x')
                        if len(parts) == 2:
                            width = int(parts[0].strip().split()[0])
                            height = int(parts[1].strip().split()[0])
                            return (width, height)
        except:
            pass
            
        # Default fallback
        return (1920, 1080)
        
    def get_documents_dir(self) -> Path:
        """Get documents directory."""
        return Path.home() / "Documents"
        
    def show_in_file_manager(self, path: Path) -> bool:
        """Show path in Finder."""
        try:
            if path.is_file():
                # Reveal file in Finder
                subprocess.run(['open', '-R', str(path)])
            else:
                # Open directory
                subprocess.run(['open', str(path)])
            return True
        except Exception as e:
            self.logger.error(f"Failed to show in Finder: {e}")
            return False
            
    def trash_file(self, path: Path) -> bool:
        """Move file to Trash."""
        try:
            # Try using osascript (AppleScript)
            script = f'''
            tell application "Finder"
                move POSIX file "{str(path)}" to trash
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Failed to trash file: {e}")
            
            # Try send2trash as fallback
            try:
                import send2trash
                send2trash.send2trash(str(path))
                return True
            except:
                return False
                
    def get_modifier_key_name(self, modifier: str) -> str:
        """Get macOS-specific modifier key name."""
        modifiers = {
            "ctrl": "⌃",  # Control
            "alt": "⌥",   # Option
            "shift": "⇧",  # Shift
            "meta": "⌘"   # Command
        }
        return modifiers.get(modifier, modifier)