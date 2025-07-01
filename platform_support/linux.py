# platform_support/linux.py
"""
Linux-specific platform implementation.
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support.base import PlatformBase
from core.constants import APP_NAME


class LinuxPlatform(PlatformBase):
    """Linux-specific functionality."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "linux"
        
    def get_user_data_dir(self) -> Path:
        """Get user data directory following XDG spec."""
        # Use XDG_DATA_HOME if set, otherwise ~/.local/share
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data) / APP_NAME
        return Path.home() / ".local" / "share" / APP_NAME
        
    def get_config_dir(self) -> Path:
        """Get config directory following XDG spec."""
        # Use XDG_CONFIG_HOME if set, otherwise ~/.config
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            return Path(xdg_config) / APP_NAME
        return Path.home() / ".config" / APP_NAME
        
    def get_cache_dir(self) -> Path:
        """Get cache directory following XDG spec."""
        # Use XDG_CACHE_HOME if set, otherwise ~/.cache
        xdg_cache = os.environ.get('XDG_CACHE_HOME')
        if xdg_cache:
            return Path(xdg_cache) / APP_NAME
        return Path.home() / ".cache" / APP_NAME
        
    def get_log_dir(self) -> Path:
        """Get log directory."""
        # Put logs in data directory
        return self.get_user_data_dir() / "logs"
        
    def supports_system_tray(self) -> bool:
        """Check if system tray is supported."""
        # Check for common desktop environments that support tray
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        # Most modern DEs support system tray
        supported_desktops = [
            'gnome', 'kde', 'xfce', 'lxde', 'lxqt', 
            'mate', 'cinnamon', 'unity', 'budgie'
        ]
        
        for de in supported_desktops:
            if de in desktop:
                return True
                
        # Check if running under X11 or Wayland
        if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            return True
            
        return False
        
    def get_tray_icon_size(self) -> Tuple[int, int]:
        """Get Linux tray icon size."""
        # Most Linux DEs use 22x22 or 24x24 for tray icons
        return (22, 22)
        
    def register_startup(self, app_name: str, app_path: str) -> bool:
        """Register app for Linux startup using .desktop files."""
        try:
            # Create autostart directory if it doesn't exist
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / f"{APP_NAME.lower()}.desktop"
            
            # Create .desktop file content
            content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Comment=PinPoint Desktop Tile Manager
Exec={app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            
            # Write desktop file
            desktop_file.write_text(content)
            
            # Make it executable (some DEs require this)
            desktop_file.chmod(0o755)
            
            self.logger.info(f"Registered {app_name} for startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register startup: {e}")
            return False
            
    def unregister_startup(self, app_name: str) -> bool:
        """Unregister app from Linux startup."""
        try:
            desktop_file = Path.home() / ".config" / "autostart" / f"{APP_NAME.lower()}.desktop"
            
            if desktop_file.exists():
                desktop_file.unlink()
                
            self.logger.info(f"Unregistered {app_name} from startup")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister startup: {e}")
            return False
            
    def is_startup_registered(self, app_name: str) -> bool:
        """Check if app is registered for startup."""
        desktop_file = Path.home() / ".config" / "autostart" / f"{APP_NAME.lower()}.desktop"
        return desktop_file.exists()
        
    def supports_always_on_top(self) -> bool:
        """Most Linux window managers support always-on-top."""
        return True
        
    def supports_transparency(self) -> bool:
        """Check if transparency is supported."""
        # Most modern compositors support transparency
        # Check for common compositors
        compositors = ['compton', 'picom', 'compiz', 'kwin', 'mutter', 'xfwm4']
        
        for comp in compositors:
            try:
                result = subprocess.run(
                    ['pgrep', comp],
                    capture_output=True
                )
                if result.returncode == 0:
                    return True
            except:
                pass
                
        # Also check if running under Wayland (usually has compositing)
        if os.environ.get('WAYLAND_DISPLAY'):
            return True
            
        return False
        
    def get_screen_count(self) -> int:
        """Get number of screens."""
        try:
            # Try to use Qt if available
            from PySide6.QtWidgets import QApplication
            if QApplication.instance():
                return len(QApplication.screens())
        except ImportError:
            pass
            
        # Try xrandr
        try:
            result = subprocess.run(
                ['xrandr', '--listmonitors'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # First line contains monitor count
                first_line = result.stdout.splitlines()[0]
                if 'Monitors:' in first_line:
                    count = int(first_line.split(':')[1].strip())
                    return count
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
            
        # Try xrandr
        try:
            result = subprocess.run(
                ['xrandr'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Look for primary display or first connected display
                for line in result.stdout.splitlines():
                    if ' connected' in line and ('primary' in line or True):
                        # Extract resolution
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and part[0].isdigit():
                                dims = part.split('x')
                                if len(dims) == 2:
                                    width = int(dims[0])
                                    height = int(dims[1].split('+')[0])
                                    return (width, height)
        except:
            pass
            
        # Default fallback
        return (1920, 1080)
        
    def get_documents_dir(self) -> Path:
        """Get documents directory."""
        # Check XDG user dirs
        try:
            result = subprocess.run(
                ['xdg-user-dir', 'DOCUMENTS'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except:
            pass
            
        # Fallback
        return Path.home() / "Documents"
        
    def show_in_file_manager(self, path: Path) -> bool:
        """Show path in file manager."""
        # Try common file managers
        file_managers = [
            'xdg-open',      # Should work on most systems
            'nautilus',      # GNOME
            'dolphin',       # KDE
            'thunar',        # XFCE
            'pcmanfm',       # LXDE
            'nemo',          # Cinnamon
            'caja',          # MATE
        ]
        
        for fm in file_managers:
            try:
                if fm == 'nautilus' and path.is_file():
                    # Nautilus has special flag to select file
                    subprocess.run([fm, '--select', str(path)])
                else:
                    subprocess.run([fm, str(path)])
                return True
            except FileNotFoundError:
                continue
            except Exception as e:
                self.logger.error(f"Failed with {fm}: {e}")
                
        return False
        
    def trash_file(self, path: Path) -> bool:
        """Move file to trash."""
        # Try gio trash (GNOME)
        try:
            subprocess.run(['gio', 'trash', str(path)], check=True)
            return True
        except:
            pass
            
        # Try kioclient (KDE)
        try:
            subprocess.run(['kioclient5', 'move', str(path), 'trash:/'], check=True)
            return True
        except:
            pass
            
        # Try trash-cli
        try:
            subprocess.run(['trash-put', str(path)], check=True)
            return True
        except:
            pass
            
        # Try send2trash
        try:
            import send2trash
            send2trash.send2trash(str(path))
            return True
        except:
            pass
            
        # Last resort: move to ~/.local/share/Trash
        try:
            trash_dir = Path.home() / ".local" / "share" / "Trash" / "files"
            trash_dir.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.move(str(path), str(trash_dir / path.name))
            return True
        except Exception as e:
            self.logger.error(f"Failed to trash file: {e}")
            return False
            
    def get_modifier_key_name(self, modifier: str) -> str:
        """Get Linux-specific modifier key name."""
        modifiers = {
            "ctrl": "Ctrl",
            "alt": "Alt",
            "shift": "Shift",
            "meta": "Super"  # Super/Windows key
        }
        return modifiers.get(modifier, modifier)