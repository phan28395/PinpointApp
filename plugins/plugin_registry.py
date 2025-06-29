# pinpoint/plugin_registry.py - Refactored to support separate logic and design

import importlib
import inspect
import json
from pathlib import Path
from typing import Dict, Type, Any, List, Optional, Tuple
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget
from ..base_tile import BaseTile
from ..design_system import DesignSystem, DesignConstraints


class TileCapabilities:
    """Defines what a tile type can do."""
    CAN_EDIT = "can_edit"
    CAN_REFRESH = "can_refresh"
    CAN_INTEGRATE = "can_integrate"
    CAN_EXPORT = "can_export"
    CAN_SCRIPT = "can_script"
    HAS_SETTINGS = "has_settings"
    SUPPORTS_THEMES = "supports_themes"
    SUPPORTS_CUSTOM_DESIGN = "supports_custom_design"  # New capability
    REQUIRES_BACKEND = "requires_backend"  # New capability


class TileMetadata:
    """Enhanced metadata about a tile type."""
    def __init__(self, 
                 tile_id: str,
                 name: str,
                 description: str,
                 author: str,
                 version: str,
                 icon: Optional[str] = None,
                 category: str = "General",
                 capabilities: List[str] = None,
                 config_schema: Dict[str, Any] = None,
                 design_constraints: Optional[DesignConstraints] = None,  # New
                 default_design: Optional[str] = None):  # New: name of default design
        self.tile_id = tile_id
        self.name = name
        self.description = description
        self.author = author
        self.version = version
        self.icon = icon
        self.category = category
        self.capabilities = capabilities or []
        self.config_schema = config_schema or {}
        self.design_constraints = design_constraints or DesignConstraints()
        self.default_design = default_design


class TileDesign:
    """Represents a visual design for a tile type."""
    
    def __init__(self, design_id: str, tile_type: str, spec: Dict[str, Any]):
        self.design_id = design_id
        self.tile_type = tile_type
        self.spec = spec
        self.metadata = spec.get('metadata', {})
        
    @property
    def name(self) -> str:
        return self.metadata.get('name', 'Unnamed Design')
        
    @property
    def author(self) -> str:
        return self.metadata.get('author', 'Unknown')
        
    @property
    def version(self) -> str:
        return self.metadata.get('version', '1.0.0')
        
    @property
    def compatible_with(self) -> str:
        return self.metadata.get('compatible_with', '1.0.0')
        
    def is_compatible(self) -> bool:
        """Check if this design is compatible with current design system."""
        # Simple version check for now
        design_version = DesignSystem.VERSION
        return self.compatible_with <= design_version
        
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the design specification."""
        return DesignSystem.validate_design_spec(self.spec)


class TilePlugin:
    """Enhanced base class for tile plugins with design support."""
    
    @classmethod
    def get_metadata(cls) -> TileMetadata:
        """Return metadata about this tile type."""
        raise NotImplementedError("Plugins must implement get_metadata()")
    
    @classmethod
    def get_tile_class(cls) -> Type[BaseTile]:
        """Return the tile widget class."""
        raise NotImplementedError("Plugins must implement get_tile_class()")
    
    @classmethod
    def get_logic_class(cls):
        """Return the tile logic class (optional, for separation of concerns)."""
        return None
    
    @classmethod
    def get_editor_class(cls):
        """Return the editor widget class, if any."""
        return None
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Return default configuration for new tiles of this type."""
        return {
            "width": 250,
            "height": 150,
            "opacity": 1.0,
            "theme": "default"
        }
    
    @classmethod
    def get_builtin_designs(cls) -> List[Dict[str, Any]]:
        """Return built-in design specifications for this tile type."""
        return []
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """Validate a configuration against the schema."""
        schema = cls.get_metadata().config_schema
        if not schema:
            return True
            
        for key, spec in schema.items():
            if spec.get("required", False) and key not in config:
                return False
                
            if key in config:
                value = config[key]
                expected_type = spec.get("type")
                
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                    
        return True


class DesignRegistry:
    """Manages tile designs separately from tile logic."""
    
    def __init__(self):
        self._designs: Dict[str, Dict[str, TileDesign]] = {}  # tile_type -> design_id -> design
        self._design_paths: List[Path] = []
        
    def add_design_path(self, path: Path):
        """Add a path to search for design files."""
        if path.exists() and path.is_dir():
            self._design_paths.append(path)
            
    def register_design(self, design: TileDesign) -> bool:
        """Register a design for a tile type."""
        # Validate first
        is_valid, errors = design.validate()
        if not is_valid:
            print(f"Invalid design {design.design_id}: {errors}")
            return False
            
        # Check compatibility
        if not design.is_compatible():
            print(f"Design {design.design_id} is not compatible with design system v{DesignSystem.VERSION}")
            return False
            
        # Register
        if design.tile_type not in self._designs:
            self._designs[design.tile_type] = {}
            
        self._designs[design.tile_type][design.design_id] = design
        return True
        
    def load_designs_from_path(self, path: Path):
        """Load all design files from a directory."""
        for design_file in path.glob("*.json"):
            try:
                with open(design_file, 'r') as f:
                    spec = json.load(f)
                    
                # Extract tile type from filename or spec
                tile_type = spec.get('tile_type', design_file.stem.split('_')[0])
                design_id = design_file.stem
                
                design = TileDesign(design_id, tile_type, spec)
                self.register_design(design)
                
            except Exception as e:
                print(f"Failed to load design from {design_file}: {e}")
                
    def get_designs_for_tile(self, tile_type: str) -> List[TileDesign]:
        """Get all available designs for a tile type."""
        return list(self._designs.get(tile_type, {}).values())
        
    def get_design(self, tile_type: str, design_id: str) -> Optional[TileDesign]:
        """Get a specific design."""
        return self._designs.get(tile_type, {}).get(design_id)


class PluginRegistry(QObject):
    """Enhanced plugin registry with design support."""
    
    plugin_loaded = Signal(str)  # tile_id
    plugin_error = Signal(str, str)  # tile_id, error_message
    design_loaded = Signal(str, str)  # tile_type, design_id
    
    def __init__(self):
        super().__init__()
        self._plugins: Dict[str, TilePlugin] = {}
        self._metadata: Dict[str, TileMetadata] = {}
        self._design_registry = DesignRegistry()
        self._builtin_plugins: List[str] = ["note", "clock", "weather", "todo"]
        
    def initialize(self):
        """Initialize the registry and load all plugins and designs."""
        # Load built-in plugins
        self._load_builtin_plugins()
        
        # Load user plugins
        self._load_user_plugins()
        
        # Load designs
        self._load_designs()
        
    def _load_builtin_plugins(self):
        """Load plugins that ship with the application."""
        for plugin_name in self._builtin_plugins:
            try:
                module_name = f"pinpoint.plugins.{plugin_name}_plugin"
                self._load_plugin_module(module_name, builtin=True)
            except Exception as e:
                print(f"Failed to load builtin plugin {plugin_name}: {e}")
                self.plugin_error.emit(plugin_name, str(e))
                
    def _load_user_plugins(self):
        """Load user-created plugins from the plugins directory."""
        user_plugin_dir = Path.home() / ".pinpoint" / "plugins"
        user_plugin_dir.mkdir(parents=True, exist_ok=True)
        
        import sys
        if str(user_plugin_dir) not in sys.path:
            sys.path.insert(0, str(user_plugin_dir))
        
        for plugin_file in user_plugin_dir.glob("*.py"):
            if plugin_file.stem.startswith("_"):
                continue
                
            try:
                module_name = plugin_file.stem
                self._load_plugin_module(module_name, builtin=False)
            except Exception as e:
                print(f"Failed to load user plugin {plugin_file}: {e}")
                self.plugin_error.emit(plugin_file.stem, str(e))
                
    def _load_plugin_module(self, module_name: str, builtin: bool = False):
        """Load a single plugin module."""
        module = importlib.import_module(module_name)
        
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, TilePlugin) and 
                obj is not TilePlugin):
                
                try:
                    # Get metadata
                    metadata = obj.get_metadata()
                    
                    # Validate the plugin
                    tile_class = obj.get_tile_class()
                    if not issubclass(tile_class, BaseTile):
                        raise ValueError(f"Tile class must inherit from BaseTile")
                    
                    # Register the plugin
                    self._plugins[metadata.tile_id] = obj
                    self._metadata[metadata.tile_id] = metadata
                    
                    # Register built-in designs
                    for design_spec in obj.get_builtin_designs():
                        design_id = design_spec.get('metadata', {}).get('id', f"{metadata.tile_id}_default")
                        design = TileDesign(design_id, metadata.tile_id, design_spec)
                        self._design_registry.register_design(design)
                    
                    print(f"Loaded plugin: {metadata.name} v{metadata.version}")
                    self.plugin_loaded.emit(metadata.tile_id)
                    
                except Exception as e:
                    print(f"Failed to register plugin {name}: {e}")
                    self.plugin_error.emit(name, str(e))
                    
    def _load_designs(self):
        """Load all design files from design directories."""
        # Built-in designs directory
        builtin_designs = Path(__file__).parent / "designs"
        if builtin_designs.exists():
            self._design_registry.add_design_path(builtin_designs)
            self._design_registry.load_designs_from_path(builtin_designs)
            
        # User designs directory
        user_designs = Path.home() / ".pinpoint" / "designs"
        user_designs.mkdir(parents=True, exist_ok=True)
        self._design_registry.add_design_path(user_designs)
        self._design_registry.load_designs_from_path(user_designs)
        
    def get_plugin(self, tile_id: str) -> Optional[TilePlugin]:
        """Get a plugin by its ID."""
        return self._plugins.get(tile_id)
        
    def get_metadata(self, tile_id: str) -> Optional[TileMetadata]:
        """Get metadata for a plugin."""
        return self._metadata.get(tile_id)
        
    def get_all_metadata(self) -> Dict[str, TileMetadata]:
        """Get metadata for all registered plugins."""
        return self._metadata.copy()
        
    def get_plugins_by_category(self, category: str) -> List[TileMetadata]:
        """Get all plugins in a specific category."""
        return [
            meta for meta in self._metadata.values() 
            if meta.category == category
        ]
        
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        categories = set()
        for meta in self._metadata.values():
            categories.add(meta.category)
        return sorted(list(categories))
        
    def get_designs_for_tile(self, tile_type: str) -> List[TileDesign]:
        """Get all available designs for a tile type."""
        return self._design_registry.get_designs_for_tile(tile_type)
        
    def get_design(self, tile_type: str, design_id: str) -> Optional[TileDesign]:
        """Get a specific design for a tile type."""
        return self._design_registry.get_design(tile_type, design_id)
        
    def create_tile(self, tile_type: str, instance_data: dict, design_id: Optional[str] = None) -> Optional[BaseTile]:
        """Create a tile instance with optional design specification."""
        # Use tile_type parameter instead of tile_id for clarity
        plugin = self.get_plugin(tile_type)
        if not plugin:
            print(f"Plugin not found: {tile_type}")
            return None
            
        try:
            tile_class = plugin.get_tile_class()
            
            # Merge default config with instance data
            default_config = plugin.get_default_config()
            tile_data = {**default_config, **instance_data}
            
            # Ensure type is set correctly
            tile_data['type'] = tile_type
            
            # Add design spec if specified
            if design_id:
                design = self.get_design(tile_type, design_id)
                if design:
                    tile_data['design_spec'] = design.spec
            elif plugin.get_metadata().default_design:
                # Use default design if specified
                default_design = self.get_design(tile_type, plugin.get_metadata().default_design)
                if default_design:
                    tile_data['design_spec'] = default_design.spec
            
            # Validate configuration
            if not plugin.validate_config(tile_data):
                print(f"Invalid configuration for tile {tile_type}")
                return None
            
            # Debug: print tile data
            print(f"Creating {tile_type} tile with content: '{tile_data.get('content', '')[:50]}'")
                
            # Create the tile
            return tile_class(tile_data)
            
        except Exception as e:
            print(f"Failed to create tile {tile_type}: {e}")
            import traceback
            traceback.print_exc()
            self.plugin_error.emit(tile_type, str(e))
            return None
    
    def create_editor(self, tile_type: str, tile_data: dict, manager) -> Optional[QWidget]:
        """Create an editor widget for a tile type."""
        plugin = self.get_plugin(tile_type)
        if not plugin:
            print(f"Plugin not found for type: {tile_type}")
            return None
            
        editor_class = plugin.get_editor_class()
        if not editor_class:
            print(f"No editor available for tile type: {tile_type}")
            return None
            
        try:
            return editor_class(tile_data, manager)
        except Exception as e:
            print(f"Failed to create editor for {tile_type}: {e}")
            self.plugin_error.emit(tile_type, str(e))
            return None
            
    def create_tile_preview(self, tile_type: str, design: TileDesign) -> Optional[BaseTile]:
        """Create a preview tile with a specific design (for design testing)."""
        plugin = self.get_plugin(tile_type)
        if not plugin:
            return None
            
        # Create minimal instance data for preview
        preview_data = {
            "id": f"preview_{tile_type}",
            "type": tile_type,
            "design_spec": design.spec,
            **plugin.get_default_config()
        }
        
        return self.create_tile(tile_type, preview_data)
        
    def export_plugin_info(self) -> Dict[str, Any]:
        """Export information about all loaded plugins and designs."""
        info = {}
        for tile_id, metadata in self._metadata.items():
            designs = self.get_designs_for_tile(tile_id)
            info[tile_id] = {
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "author": metadata.author,
                "category": metadata.category,
                "capabilities": metadata.capabilities,
                "has_editor": self._plugins[tile_id].get_editor_class() is not None,
                "available_designs": [
                    {
                        "id": design.design_id,
                        "name": design.name,
                        "author": design.author,
                        "version": design.version
                    }
                    for design in designs
                ],
                "supports_custom_design": TileCapabilities.SUPPORTS_CUSTOM_DESIGN in metadata.capabilities
            }
        return info
        
    def validate_design_for_tile(self, tile_type: str, design_spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a design against a tile type's constraints."""
        metadata = self.get_metadata(tile_type)
        if not metadata:
            return False, [f"Unknown tile type: {tile_type}"]
            
        # First validate against general design system rules
        is_valid, errors = DesignSystem.validate_design_spec(design_spec)
        
        # Then validate against tile-specific constraints
        constraints = metadata.design_constraints
        if constraints:
            # Add tile-specific validation here
            pass
            
        return is_valid, errors


# Global registry instance
_registry = None

def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.initialize()
    return _registry