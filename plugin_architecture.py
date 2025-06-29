# pinpoint/plugin_architecture.py
"""
Enhanced plugin architecture with security, design constraints, and freedom balance.
"""

from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import hashlib
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QObject, Signal

from .design_layer import DesignLayer
from .base_tile_refactored import BaseTile


class PluginPermission(Enum):
    """Permissions that plugins can request."""
    NETWORK_ACCESS = "network_access"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    SYSTEM_INFO = "system_info"
    CAMERA_ACCESS = "camera_access"
    MICROPHONE_ACCESS = "microphone_access"
    LOCATION_ACCESS = "location_access"
    NOTIFICATION_SEND = "notification_send"
    CLIPBOARD_ACCESS = "clipboard_access"
    INTER_PLUGIN_COMMUNICATION = "inter_plugin_communication"


class PluginCapability(Enum):
    """Capabilities that plugins can declare."""
    CUSTOM_STYLES = "custom_styles"
    BACKGROUND_TASKS = "background_tasks"
    DATA_PERSISTENCE = "data_persistence"
    CUSTOM_SETTINGS = "custom_settings"
    EXPORT_IMPORT = "export_import"
    REAL_TIME_SYNC = "real_time_sync"


@dataclass
class PluginManifest:
    """Plugin metadata and requirements."""
    # Basic info
    id: str
    name: str
    version: str
    author: str
    description: str
    website: Optional[str]
    
    # Technical requirements
    min_app_version: str
    max_app_version: Optional[str]
    
    # Permissions needed
    required_permissions: List[PluginPermission]
    optional_permissions: List[PluginPermission]
    
    # Capabilities
    capabilities: List[PluginCapability]
    
    # Design compliance
    design_compliance_level: str  # "strict", "flexible", "custom"
    custom_design_allowed: bool
    
    # Security
    signature: Optional[str]  # For verified plugins
    sandbox_level: str  # "strict", "standard", "trusted"


class DesignConstraints:
    """
    Defines what aspects of design plugins MUST follow
    and what they CAN customize.
    """
    
    @dataclass
    class RequiredElements:
        """UI elements that MUST exist in every plugin."""
        header: bool = True
        close_button: bool = True
        drag_handle: bool = True
        resize_handle: bool = True
        
    @dataclass
    class AllowedCustomization:
        """What plugins can customize."""
        content_background: bool = True
        content_text_color: bool = True
        content_fonts: bool = True
        content_spacing: bool = True
        content_borders: bool = True
        # But NOT:
        header_style: bool = False
        window_chrome: bool = False
        system_controls: bool = False
        
    @dataclass
    class DesignLimits:
        """Limits to maintain consistency."""
        max_custom_colors: int = 5
        allowed_fonts: List[str] = None  # None means use system fonts only
        min_contrast_ratio: float = 4.5  # WCAG AA compliance
        max_animation_duration: float = 1.0  # seconds
        required_border_radius: Optional[int] = None  # Force consistent corners


class PluginSandbox:
    """
    Security sandbox for plugin execution.
    Restricts what plugins can do to protect users.
    """
    
    def __init__(self, plugin_manifest: PluginManifest):
        self.manifest = plugin_manifest
        self.granted_permissions = set()
        
    def request_permission(self, permission: PluginPermission) -> bool:
        """Plugin requests a permission at runtime."""
        if permission in self.manifest.required_permissions:
            return True  # Already granted during install
            
        if permission in self.manifest.optional_permissions:
            # Ask user
            return self._ask_user_permission(permission)
            
        return False  # Not in manifest, deny
        
    def _ask_user_permission(self, permission: PluginPermission) -> bool:
        """Show permission dialog to user."""
        # Implementation would show actual dialog
        from PySide6.QtWidgets import QMessageBox
        
        result = QMessageBox.question(
            None,
            "Permission Request",
            f"Plugin '{self.manifest.name}' is requesting {permission.value} permission. Allow?",
        )
        
        if result == QMessageBox.Yes:
            self.granted_permissions.add(permission)
            return True
        return False
        
    def validate_api_call(self, api_name: str, args: tuple, kwargs: dict) -> bool:
        """Validate if plugin can make this API call."""
        # Define API -> Permission mapping
        api_permissions = {
            'network.request': PluginPermission.NETWORK_ACCESS,
            'file.read': PluginPermission.FILE_READ,
            'file.write': PluginPermission.FILE_WRITE,
            'clipboard.read': PluginPermission.CLIPBOARD_ACCESS,
        }
        
        required_permission = api_permissions.get(api_name)
        if required_permission:
            return required_permission in self.granted_permissions
            
        return True  # No permission needed


class SecurePluginAPI:
    """
    Secure API that plugins interact with.
    All calls go through security checks.
    """
    
    def __init__(self, sandbox: PluginSandbox):
        self.sandbox = sandbox
        
    def read_file(self, path: str) -> Optional[str]:
        """Read file with permission check."""
        if not self.sandbox.validate_api_call('file.read', (path,), {}):
            raise PermissionError("Plugin lacks file read permission")
            
        # Additional validation: only allow reading from plugin's data dir
        plugin_dir = Path.home() / ".pinpoint" / "plugins" / self.sandbox.manifest.id
        requested_path = Path(path).resolve()
        
        if not str(requested_path).startswith(str(plugin_dir)):
            raise PermissionError("Plugin can only read its own data directory")
            
        return requested_path.read_text()
        
    def make_network_request(self, url: str, method: str = "GET") -> dict:
        """Make network request with permission check."""
        if not self.sandbox.validate_api_call('network.request', (url,), {}):
            raise PermissionError("Plugin lacks network access permission")
            
        # Additional validation: check URL whitelist/blacklist
        if self._is_url_blocked(url):
            raise PermissionError(f"URL {url} is blocked")
            
        # Make actual request through app's network layer
        # This ensures we can monitor/log all plugin network activity
        return self._make_safe_request(url, method)


class PluginBase(BaseTile):
    """
    Base class for all plugins.
    Enforces design constraints while allowing customization.
    """
    
    def __init__(self, tile_data: Dict[str, Any], design_layer: DesignLayer, 
                 plugin_manifest: PluginManifest):
        # Store manifest
        self.manifest = plugin_manifest
        
        # Create sandbox
        self.sandbox = PluginSandbox(plugin_manifest)
        
        # Create secure API
        self.api = SecurePluginAPI(self.sandbox)
        
        # Initialize base tile (applies core design)
        super().__init__(tile_data, design_layer)
        
        # Apply plugin's custom design if allowed
        if self.manifest.custom_design_allowed:
            self._apply_plugin_design()
            
    def _create_structure(self):
        """Override to enforce consistent structure."""
        # Call parent to create standard structure
        super()._create_structure()
        
        # Add plugin indicator if needed
        if self.design.get_value("plugins.show_indicator", True):
            self._add_plugin_indicator()
            
    def _add_plugin_indicator(self):
        """Add visual indicator that this is a plugin."""
        indicator = QLabel()
        indicator.setObjectName("plugin_indicator")
        indicator.setToolTip(f"Plugin: {self.manifest.name} v{self.manifest.version}")
        
        # Add to header
        self.header.layout().addWidget(indicator)
        
    def _apply_plugin_design(self):
        """Apply plugin's custom design within constraints."""
        plugin_design_file = (
            Path.home() / ".pinpoint" / "plugins" / 
            self.manifest.id / "design.json"
        )
        
        if not plugin_design_file.exists():
            return
            
        with open(plugin_design_file) as f:
            plugin_design = json.load(f)
            
        # Validate design against constraints
        if self._validate_plugin_design(plugin_design):
            # Apply only to content area
            self._apply_design_to_content(plugin_design)
            
    def _validate_plugin_design(self, design: dict) -> bool:
        """Ensure plugin design follows constraints."""
        constraints = DesignConstraints()
        
        # Check color count
        custom_colors = design.get('colors', {})
        if len(custom_colors) > constraints.DesignLimits.max_custom_colors:
            return False
            
        # Check contrast ratios
        if not self._check_contrast_compliance(design):
            return False
            
        # Check if trying to style prohibited elements
        if any(key in design.get('styles', {}) for key in 
               ['header', 'close_button', 'window_chrome']):
            return False
            
        return True
        
    def setup_content(self):
        """Plugins must override this to add their content."""
        raise NotImplementedError("Plugins must implement setup_content()")


class PluginRegistry:
    """
    Enhanced plugin registry with security and design validation.
    """
    
    def __init__(self, design_layer: DesignLayer):
        self.design_layer = design_layer
        self.plugins: Dict[str, PluginManifest] = {}
        self.loaded_plugins: Dict[str, type] = {}
        
    def install_plugin(self, plugin_path: Path) -> bool:
        """Install a plugin with validation."""
        # Load manifest
        manifest_file = plugin_path / "manifest.json"
        if not manifest_file.exists():
            raise ValueError("Missing manifest.json")
            
        with open(manifest_file) as f:
            manifest_data = json.load(f)
            
        manifest = PluginManifest(**manifest_data)
        
        # Validate plugin
        if not self._validate_plugin(plugin_path, manifest):
            return False
            
        # Check permissions with user
        if not self._request_install_permissions(manifest):
            return False
            
        # Copy to plugins directory
        install_path = Path.home() / ".pinpoint" / "plugins" / manifest.id
        self._install_plugin_files(plugin_path, install_path)
        
        # Register
        self.plugins[manifest.id] = manifest
        
        return True
        
    def _validate_plugin(self, path: Path, manifest: PluginManifest) -> bool:
        """Comprehensive plugin validation."""
        
        # 1. Verify signature if required
        if self._requires_signature():
            if not self._verify_signature(path, manifest):
                return False
                
        # 2. Check code safety
        if not self._scan_plugin_code(path):
            return False
            
        # 3. Validate design compliance
        if not self._validate_design_compliance(path, manifest):
            return False
            
        # 4. Check version compatibility
        if not self._check_version_compatibility(manifest):
            return False
            
        return True
        
    def _scan_plugin_code(self, path: Path) -> bool:
        """Scan plugin code for dangerous patterns."""
        dangerous_patterns = [
            'exec(',
            'eval(',
            '__import__',
            'subprocess',
            'os.system',
            'open(',  # Should use plugin API instead
            'requests.',  # Should use plugin API instead
        ]
        
        for py_file in path.glob("**/*.py"):
            content = py_file.read_text()
            for pattern in dangerous_patterns:
                if pattern in content:
                    print(f"Dangerous pattern '{pattern}' found in {py_file}")
                    return False
                    
        return True


class PluginMarketplace:
    """
    UI for browsing and installing plugins.
    """
    
    def __init__(self, registry: PluginRegistry, design_layer: DesignLayer):
        self.registry = registry
        self.design = design_layer
        
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """Get list of available plugins from marketplace."""
        # This would connect to your plugin marketplace API
        return [
            {
                "id": "weather-tile",
                "name": "Weather Tile",
                "author": "Community Dev",
                "description": "Shows weather information",
                "version": "1.0.0",
                "downloads": 1523,
                "rating": 4.5,
                "verified": True,
                "screenshots": ["weather1.png", "weather2.png"],
                "permissions": ["network_access", "location_access"],
            }
        ]
        
    def install_from_marketplace(self, plugin_id: str):
        """Download and install plugin from marketplace."""
        # Download plugin package
        plugin_data = self._download_plugin(plugin_id)
        
        # Verify checksum
        if not self._verify_checksum(plugin_data):
            raise ValueError("Plugin checksum verification failed")
            
        # Extract and install
        plugin_path = self._extract_plugin(plugin_data)
        return self.registry.install_plugin(plugin_path)


# Example Plugin Implementation
class ExampleWeatherPlugin(PluginBase):
    """Example of how a plugin would be implemented."""
    
    def setup_content(self):
        """Set up the weather plugin content."""
        # Create weather display widgets
        self.temp_label = QLabel("Loading...")
        self.temp_label.setObjectName("weather_temperature")
        
        self.condition_label = QLabel("")
        self.condition_label.setObjectName("weather_condition")
        
        # Add to content area (which is styled by our design system)
        self.content_layout.addWidget(self.temp_label)
        self.content_layout.addWidget(self.condition_label)
        
        # Use secure API to fetch weather
        self._fetch_weather()
        
    def _fetch_weather(self):
        """Fetch weather using secure API."""
        try:
            # This goes through permission checks
            data = self.api.make_network_request(
                "https://api.weather.com/...",
                method="GET"
            )
            
            self.temp_label.setText(f"{data['temperature']}°")
            self.condition_label.setText(data['condition'])
            
        except PermissionError:
            self.temp_label.setText("No network permission")


# Plugin Development Kit (PDK)
class PluginDevelopmentKit:
    """
    Tools for plugin developers to ensure compatibility.
    """
    
    @staticmethod
    def validate_plugin(plugin_path: Path) -> List[str]:
        """Validate a plugin before submission."""
        errors = []
        
        # Check manifest
        manifest_file = plugin_path / "manifest.json"
        if not manifest_file.exists():
            errors.append("Missing manifest.json")
            
        # Check required files
        if not (plugin_path / "__init__.py").exists():
            errors.append("Missing __init__.py")
            
        # Validate code
        # ... more validation
        
        return errors
        
    @staticmethod
    def create_plugin_template(name: str, output_path: Path):
        """Create a plugin template for developers."""
        template = {
            "manifest.json": {
                "id": f"com.example.{name.lower()}",
                "name": name,
                "version": "1.0.0",
                "author": "Your Name",
                "description": "Plugin description",
                "min_app_version": "1.0.0",
                "required_permissions": [],
                "optional_permissions": [],
                "capabilities": ["custom_styles"],
                "design_compliance_level": "strict",
                "custom_design_allowed": True,
                "sandbox_level": "standard"
            },
            "__init__.py": f'''
from pinpoint.plugin_architecture import PluginBase

class {name}Plugin(PluginBase):
    """Your plugin implementation."""
    
    def setup_content(self):
        """Set up your plugin's content."""
        # Add your widgets here
        label = self.factory.create_label("Hello from {name}!")
        self.content_layout.addWidget(label)
''',
            "design.json": {
                "content_styles": {
                    "background": "#f0f0f0",
                    "text_color": "#333333",
                    "font_size": 14
                }
            }
        }
        
        # Create files
        for filename, content in template.items():
            file_path = output_path / filename
            if isinstance(content, dict):
                file_path.write_text(json.dumps(content, indent=2))
            else:
                file_path.write_text(content)