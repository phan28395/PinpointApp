# pinpoint/design_layer.py
"""
Complete abstraction layer between backend and design.
ALL visual decisions come from external design files.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                              QStackedLayout, QPushButton, QLabel, QFrame,
                              QTextEdit, QLineEdit, QComboBox, QSpinBox,
                              QCheckBox, QRadioButton, QSlider, QProgressBar,
                              QListWidget, QTreeWidget, QTableWidget,
                              QGraphicsView, QMenu, QToolBar, QStatusBar,
                              QApplication)
from PySide6.QtCore import Qt, QObject, Signal, QFileSystemWatcher, QTimer
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor


class DesignLayer(QObject):
    """
    Complete abstraction layer between backend and design.
    Handles all visual aspects of the application.
    """
    
    # Signal emitted when design is reloaded
    design_reloaded = Signal()
    
    def __init__(self, design_path: Path):
        super().__init__()
        self.design_path = design_path
        self.design_data = {}
        self._style_cache = {}
        self._icon_cache = {}
        self._widget_registry = {}  # Track created widgets for updates
        
        # Load all design specifications
        self._load_design()
        
        # Setup file watcher for live reload
        self._setup_watcher()
        
    def _load_design(self):
        """Load all design specifications from the design directory."""
        try:
            # Load main design specification
            main_design_file = self.design_path / "main.json"
            if main_design_file.exists():
                with open(main_design_file, 'r', encoding='utf-8') as f:
                    self.design_data = json.load(f)
            
            # Load included files
            if 'includes' in self.design_data:
                for include_path in self.design_data['includes']:
                    include_file = self.design_path / include_path
                    if include_file.exists():
                        with open(include_file, 'r', encoding='utf-8') as f:
                            include_data = json.load(f)
                            # Merge the data
                            self._merge_design_data(include_data)
            
            # Load additional design files
            self._load_styles()
            self._load_layouts()
            self._load_components()
            self._load_assets()
            
        except Exception as e:
            print(f"Error loading design: {e}")
            # Fall back to minimal default design
            self._load_default_design()
    
    def _merge_design_data(self, new_data: Dict[str, Any]):
        """Merge new design data into existing data."""
        for key, value in new_data.items():
            if key in self.design_data and isinstance(value, dict) and isinstance(self.design_data[key], dict):
                # Merge dictionaries
                self._deep_merge(self.design_data[key], value)
            else:
                # Replace value
                self.design_data[key] = value
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _load_styles(self):
        """Load style specifications."""
        styles_dir = self.design_path / "styles"
        if not styles_dir.exists():
            return
            
        self.design_data['styles'] = {
            'global': self._load_style_file(styles_dir / "global.qss"),
            'classes': {},
            'ids': {},
            'states': {}
        }
        
        # Load widget class styles
        classes_file = styles_dir / "classes.json"
        if classes_file.exists():
            with open(classes_file, 'r', encoding='utf-8') as f:
                self.design_data['styles']['classes'] = json.load(f)
                
        # Load ID-specific styles
        ids_file = styles_dir / "ids.json"
        if ids_file.exists():
            with open(ids_file, 'r', encoding='utf-8') as f:
                self.design_data['styles']['ids'] = json.load(f)
    
    def _load_style_file(self, file_path: Path) -> str:
        """Load a QSS stylesheet file."""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_layouts(self):
        """Load layout specifications."""
        layouts_dir = self.design_path / "layouts"
        if not layouts_dir.exists():
            return
            
        self.design_data['layouts'] = {}
        
        for layout_file in layouts_dir.glob("*.json"):
            layout_name = layout_file.stem
            with open(layout_file, 'r', encoding='utf-8') as f:
                self.design_data['layouts'][layout_name] = json.load(f)
    
    def _load_components(self):
        """Load component templates."""
        components_file = self.design_path / "components.json"
        if components_file.exists():
            with open(components_file, 'r', encoding='utf-8') as f:
                self.design_data['components'] = json.load(f)
        else:
            self.design_data['components'] = {}
    
    def _load_assets(self):
        """Load asset mappings."""
        assets_file = self.design_path / "assets.json"
        if assets_file.exists():
            with open(assets_file, 'r', encoding='utf-8') as f:
                self.design_data['assets'] = json.load(f)
        else:
            self.design_data['assets'] = {
                'icons': {},
                'images': {},
                'fonts': []
            }
    
    def _load_default_design(self):
        """Load minimal default design as fallback."""
        self.design_data = {
            'version': '1.0.0',
            'styles': {
                'global': '',
                'classes': {},
                'ids': {}
            },
            'layouts': {},
            'components': {},
            'assets': {
                'icons': {},
                'images': {}
            }
        }
    
    def _setup_watcher(self):
        """Setup file system watcher for live reload."""
        self.watcher = QFileSystemWatcher()
        self.watcher.addPath(str(self.design_path))
        
        # Watch all subdirectories
        for subdir in ['styles', 'layouts', 'assets']:
            path = self.design_path / subdir
            if path.exists():
                self.watcher.addPath(str(path))
        
        # Debounce timer for reloading
        self.reload_timer = QTimer()
        self.reload_timer.timeout.connect(self._do_reload)
        self.reload_timer.setSingleShot(True)
        
        # Connect watcher
        self.watcher.directoryChanged.connect(self._on_design_changed)
        self.watcher.fileChanged.connect(self._on_design_changed)
    
    def _on_design_changed(self):
        """Handle design file changes with debouncing."""
        self.reload_timer.stop()
        self.reload_timer.start(100)  # 100ms debounce
    
    def _do_reload(self):
        """Reload design and update all registered widgets."""
        print("Reloading design...")
        self._load_design()
        
        # Update all registered widgets
        for widget_id, widget_ref in list(self._widget_registry.items()):
            widget = widget_ref()  # Weak reference
            if widget:
                self.apply_design(widget)
            else:
                # Widget was deleted
                del self._widget_registry[widget_id]
        
        self.design_reloaded.emit()
    
    # Public API Methods
    
    def get_style(self, class_name: str = None, widget_id: str = None, 
                  state: str = "default") -> str:
        """Get style for a widget by class and/or ID."""
        styles = []
        
        # Global styles first
        if 'global' in self.design_data.get('styles', {}):
            styles.append(self.design_data['styles']['global'])
        
        # Class styles
        if class_name and class_name in self.design_data.get('styles', {}).get('classes', {}):
            class_styles = self.design_data['styles']['classes'][class_name]
            if isinstance(class_styles, dict):
                styles.append(class_styles.get(state, class_styles.get('default', '')))
            else:
                styles.append(class_styles)
        
        # ID styles (highest priority)
        if widget_id and widget_id in self.design_data.get('styles', {}).get('ids', {}):
            id_styles = self.design_data['styles']['ids'][widget_id]
            if isinstance(id_styles, dict):
                styles.append(id_styles.get(state, id_styles.get('default', '')))
            else:
                styles.append(id_styles)
        
        return '\n'.join(filter(None, styles))
    
    def get_layout(self, layout_name: str) -> Dict[str, Any]:
        """Get layout specification by name."""
        return self.design_data.get('layouts', {}).get(layout_name, {})
    
    def get_component(self, component_name: str) -> Dict[str, Any]:
        """Get component template by name."""
        return self.design_data.get('components', {}).get(component_name, {})
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """Get a value from design data using dot notation path."""
        keys = path.split('.')
        value = self.design_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_icon(self, icon_name: str) -> QIcon:
        """Get an icon by name, with caching."""
        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]
        
        # Check if it's a text icon (emoji)
        if icon_name in self.design_data.get('assets', {}).get('icons', {}):
            icon_path = self.design_data['assets']['icons'][icon_name]
            
            if icon_path.startswith('text:'):
                # Text-based icon (emoji)
                return QIcon()  # Return empty, handle text separately
            else:
                # File-based icon
                full_path = self.design_path / icon_path
                if full_path.exists():
                    icon = QIcon(str(full_path))
                    self._icon_cache[icon_name] = icon
                    return icon
        
        return QIcon()
    
    def get_icon_text(self, icon_name: str) -> str:
        """Get text representation of an icon (for emoji icons)."""
        if icon_name in self.design_data.get('assets', {}).get('icons', {}):
            icon_value = self.design_data['assets']['icons'][icon_name]
            if icon_value.startswith('text:'):
                return icon_value[5:]  # Remove 'text:' prefix
        return ""
    
    def apply_design(self, widget: QWidget, widget_id: str = None):
        """Apply design to a widget and all its children."""
        if not widget_id:
            widget_id = widget.objectName()
        
        # Register widget for live updates (using weak reference)
        if widget_id:
            import weakref
            self._widget_registry[widget_id] = weakref.ref(widget)
        
        # Apply to this widget
        self._apply_widget_design(widget, widget_id)
        
        # Recursively apply to children
        for child in widget.findChildren(QWidget):
            child_id = child.objectName()
            if child_id:
                self._apply_widget_design(child, child_id)
    
    def _apply_widget_design(self, widget: QWidget, widget_id: str = None):
        """Apply design to a single widget."""
        class_name = widget.__class__.__name__
        
        # Get and apply styles
        style = self.get_style(class_name, widget_id)
        if style:
            widget.setStyleSheet(style)
        
        # Apply properties
        if widget_id:
            props = self.get_value(f'properties.{widget_id}', {})
            self._apply_properties(widget, props)
        
        # Apply class-level properties
        class_props = self.get_value(f'properties._classes.{class_name}', {})
        self._apply_properties(widget, class_props)
    
    def _apply_properties(self, widget: QWidget, properties: Dict[str, Any]):
        """Apply properties to a widget."""
        for prop, value in properties.items():
            if prop == 'size':
                if isinstance(value, dict):
                    widget.resize(value.get('width', 100), value.get('height', 100))
                elif isinstance(value, list) and len(value) == 2:
                    widget.resize(value[0], value[1])
                    
            elif prop == 'min_size':
                if isinstance(value, dict):
                    widget.setMinimumSize(value.get('width', 0), value.get('height', 0))
                elif isinstance(value, list) and len(value) == 2:
                    widget.setMinimumSize(value[0], value[1])
                    
            elif prop == 'max_size':
                if isinstance(value, dict):
                    widget.setMaximumSize(value.get('width', 16777215), 
                                        value.get('height', 16777215))
                elif isinstance(value, list) and len(value) == 2:
                    widget.setMaximumSize(value[0], value[1])
                    
            elif prop == 'fixed_size':
                if isinstance(value, dict):
                    widget.setFixedSize(value.get('width', 100), value.get('height', 100))
                elif isinstance(value, list) and len(value) == 2:
                    widget.setFixedSize(value[0], value[1])
                    
            elif prop == 'position':
                if isinstance(value, dict):
                    widget.move(value.get('x', 0), value.get('y', 0))
                elif isinstance(value, list) and len(value) == 2:
                    widget.move(value[0], value[1])
                    
            elif prop == 'margins' and hasattr(widget, 'setContentsMargins'):
                if isinstance(value, list) and len(value) == 4:
                    widget.setContentsMargins(value[0], value[1], value[2], value[3])
                    
            elif prop == 'spacing' and hasattr(widget, 'layout') and widget.layout():
                widget.layout().setSpacing(value)
                
            elif prop == 'visible':
                widget.setVisible(value)
                
            elif prop == 'enabled':
                widget.setEnabled(value)
                
            elif prop == 'tooltip':
                widget.setToolTip(value)
                
            elif prop == 'font':
                font = QFont()
                if 'family' in value:
                    font.setFamily(value['family'])
                if 'size' in value:
                    font.setPointSize(value['size'])
                if 'weight' in value:
                    font.setWeight(value['weight'])
                if 'italic' in value:
                    font.setItalic(value['italic'])
                widget.setFont(font)
    
    def create_layout(self, layout_spec: Dict[str, Any]) -> Optional[QVBoxLayout]:
        """Create a layout from specification."""
        layout_type = layout_spec.get('type', 'vertical')
        
        if layout_type == 'vertical':
            layout = QVBoxLayout()
        elif layout_type == 'horizontal':
            layout = QHBoxLayout()
        elif layout_type == 'grid':
            layout = QGridLayout()
        elif layout_type == 'stacked':
            layout = QStackedLayout()
        else:
            return None
        
        # Apply layout properties
        if 'spacing' in layout_spec:
            layout.setSpacing(layout_spec['spacing'])
            
        if 'margins' in layout_spec:
            margins = layout_spec['margins']
            if isinstance(margins, list) and len(margins) == 4:
                layout.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
            elif isinstance(margins, int):
                layout.setContentsMargins(margins, margins, margins, margins)
        
        return layout
    
    def create_widget_from_spec(self, spec: Dict[str, Any], parent: QWidget = None) -> Optional[QWidget]:
        """Create a widget from a specification."""
        widget_type = spec.get('type')
        widget_id = spec.get('id')
        
        # Create the appropriate widget
        widget = self._create_widget_by_type(widget_type, parent)
        if not widget:
            return None
        
        # Set object name for styling
        if widget_id:
            widget.setObjectName(widget_id)
        
        # Apply properties from spec
        if 'properties' in spec:
            self._apply_properties(widget, spec['properties'])
        
        # Set text if applicable
        if 'text' in spec and hasattr(widget, 'setText'):
            widget.setText(spec['text'])
        
        # Create children if this is a container
        if 'children' in spec and isinstance(spec['children'], list):
            # Create layout for children
            layout_spec = spec.get('layout', {'type': 'vertical'})
            layout = self.create_layout(layout_spec)
            
            if layout:
                widget.setLayout(layout)
                
                # Add children
                for child_spec in spec['children']:
                    child_widget = self.create_widget_from_spec(child_spec, widget)
                    if child_widget:
                        if isinstance(layout, QGridLayout) and 'grid_position' in child_spec:
                            pos = child_spec['grid_position']
                            layout.addWidget(child_widget, pos.get('row', 0), 
                                           pos.get('column', 0),
                                           pos.get('row_span', 1),
                                           pos.get('column_span', 1))
                        else:
                            layout.addWidget(child_widget)
        
        # Apply design
        self.apply_design(widget, widget_id)
        
        return widget
    
    def _create_widget_by_type(self, widget_type: str, parent: QWidget = None) -> Optional[QWidget]:
        """Create a widget instance by type name."""
        widget_map = {
            'widget': QWidget,
            'frame': QFrame,
            'label': QLabel,
            'button': QPushButton,
            'text_edit': QTextEdit,
            'line_edit': QLineEdit,
            'combo_box': QComboBox,
            'spin_box': QSpinBox,
            'check_box': QCheckBox,
            'radio_button': QRadioButton,
            'slider': QSlider,
            'progress_bar': QProgressBar,
            'list_widget': QListWidget,
            'tree_widget': QTreeWidget,
            'table_widget': QTableWidget,
            'graphics_view': QGraphicsView,
        }
        
        widget_class = widget_map.get(widget_type)
        if widget_class:
            return widget_class(parent)
        
        return None
    
    def get_text(self, text_key: str, default: str = "") -> str:
        """Get localized text from design."""
        texts = self.design_data.get('texts', {})
        return texts.get(text_key, default)