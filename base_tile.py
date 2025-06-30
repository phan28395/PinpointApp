# pinpoint/base_tile.py - Enhanced with complete design constraints validation

from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon
from typing import Dict, Any, Optional, Callable, List, Union, Tuple
from design_system import DesignSystem, ComponentType, spacing, color, DesignConstraints
import weakref
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, 
                              QPushButton, QLabel, QTextEdit, QLineEdit, QSpacerItem, 
                              QSizePolicy, QProgressBar, QSlider, QCheckBox, QLayout,
                              QScrollArea, QRadioButton, QComboBox, QSpinBox, QTabWidget,
                              QGroupBox)

class DesignValidator:
    """
    Validates design specifications against tile constraints.
    Provides detailed error messages for debugging.
    """
    
    def __init__(self, tile_type: str, constraints: Optional[DesignConstraints] = None):
        self.tile_type = tile_type
        self.constraints = constraints or DesignConstraints()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate(self, spec: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a complete design specification.
        Returns (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()
        
        # Check version compatibility first
        self._validate_version_compatibility(spec)
        
        # Validate basic structure
        is_structurally_valid, structural_errors = DesignSystem.validate_design_spec(spec)
        self.errors.extend(structural_errors)
        
        if not is_structurally_valid:
            return False, self.errors, self.warnings
            
        # Validate against constraints
        self._validate_size_constraints(spec)
        self._validate_component_constraints(spec)
        self._validate_required_components(spec)
        self._validate_nesting_depth(spec)
        
        return len(self.errors) == 0, self.errors, self.warnings
        
    def _validate_version_compatibility(self, spec: Dict[str, Any]):
        """Check if the design is compatible with current system version."""
        if 'metadata' not in spec:
            self.errors.append("Design metadata is missing")
            return
            
        metadata = spec['metadata']
        compatible_with = metadata.get('compatible_with', '1.0.0')
        
        # Parse versions (simplified - in production use proper semver)
        try:
            design_major, design_minor, design_patch = map(int, compatible_with.split('.'))
            system_major, system_minor, system_patch = map(int, DesignSystem.VERSION.split('.'))
            
            # Major version must match
            if design_major != system_major:
                self.errors.append(
                    f"Design requires design system v{compatible_with}, "
                    f"but current system is v{DesignSystem.VERSION}. "
                    f"Major version mismatch prevents compatibility."
                )
            # Minor version of design can't be newer than system
            elif design_minor > system_minor:
                self.errors.append(
                    f"Design requires features from design system v{compatible_with}, "
                    f"but current system is v{DesignSystem.VERSION}. "
                    f"Please update the design system."
                )
            # Patch differences are just warnings
            elif design_patch > system_patch:
                self.warnings.append(
                    f"Design was created for v{compatible_with}, "
                    f"current system is v{DesignSystem.VERSION}. "
                    f"Minor compatibility issues may occur."
                )
        except (ValueError, AttributeError):
            self.errors.append(
                f"Invalid version format in design: '{compatible_with}'. "
                f"Expected format: MAJOR.MINOR.PATCH (e.g., 1.0.0)"
            )
            
    def _validate_size_constraints(self, spec: Dict[str, Any]):
        """Validate size constraints from styling or layout specs."""
        styling = spec.get('styling', {})
        
        # Check if explicit sizes are specified
        if 'size' in styling:
            size = styling['size']
            if isinstance(size, dict):
                width = size.get('width')
                height = size.get('height')
                
                if width is not None:
                    if width < self.constraints.min_width:
                        self.errors.append(
                            f"Design width ({width}px) is below minimum "
                            f"constraint ({self.constraints.min_width}px)"
                        )
                    elif width > self.constraints.max_width:
                        self.errors.append(
                            f"Design width ({width}px) exceeds maximum "
                            f"constraint ({self.constraints.max_width}px)"
                        )
                        
                if height is not None:
                    if height < self.constraints.min_height:
                        self.errors.append(
                            f"Design height ({height}px) is below minimum "
                            f"constraint ({self.constraints.min_height}px)"
                        )
                    elif height > self.constraints.max_height:
                        self.errors.append(
                            f"Design height ({height}px) exceeds maximum "
                            f"constraint ({self.constraints.max_height}px)"
                        )
                        
    def _validate_component_constraints(self, spec: Dict[str, Any]):
        """Validate that only allowed component types are used."""
        layout = spec.get('layout', {})
        self._check_components_in_layout(layout, "root")
        
    def _check_components_in_layout(self, layout: Dict[str, Any], path: str):
        """Recursively check component types in a layout."""
        components = layout.get('components', [])
        
        for i, comp in enumerate(components):
            comp_type = comp.get('type')
            comp_path = f"{path}.components[{i}]"
            
            if comp_type:
                try:
                    component_enum = ComponentType(comp_type)
                    # Check if this component type is allowed
                    if self.constraints.allowed_components:
                        if component_enum not in self.constraints.allowed_components:
                            self.errors.append(
                                f"{comp_path}: Component type '{comp_type}' is not allowed "
                                f"for {self.tile_type} tiles. Allowed types: "
                                f"{[c.value for c in self.constraints.allowed_components]}"
                            )
                except ValueError:
                    # This error is already caught by basic validation
                    pass
                    
            # Recurse into containers
            if comp_type == ComponentType.CONTAINER.value and 'components' in comp:
                self._check_components_in_layout(
                    {'components': comp['components']}, 
                    f"{comp_path}"
                )
                
    def _validate_required_components(self, spec: Dict[str, Any]):
        """Ensure all required components are present."""
        if not self.constraints.required_components:
            return
            
        # Collect all component IDs
        found_ids = set()
        layout = spec.get('layout', {})
        self._collect_component_ids(layout, found_ids)
        
        # Check for missing required components
        for required_id in self.constraints.required_components:
            if required_id not in found_ids:
                self.errors.append(
                    f"Required component '{required_id}' is missing from the design. "
                    f"{self.tile_type} tiles must include: {self.constraints.required_components}"
                )
                
    def _collect_component_ids(self, layout: Dict[str, Any], found_ids: set):
        """Recursively collect all component IDs."""
        components = layout.get('components', [])
        
        for comp in components:
            comp_id = comp.get('id')
            if comp_id:
                found_ids.add(comp_id)
                
            # Recurse into containers
            if comp.get('type') == ComponentType.CONTAINER.value and 'components' in comp:
                self._collect_component_ids(
                    {'components': comp['components']}, 
                    found_ids
                )
                
    def _validate_nesting_depth(self, spec: Dict[str, Any]):
        """Validate that component nesting doesn't exceed maximum depth."""
        layout = spec.get('layout', {})
        max_depth = self._calculate_max_depth(layout, 0)
        
        if max_depth > self.constraints.max_component_depth:
            self.errors.append(
                f"Component nesting depth ({max_depth}) exceeds maximum "
                f"allowed depth ({self.constraints.max_component_depth}). "
                f"Reduce the number of nested containers."
            )
            
    def _calculate_max_depth(self, layout: Dict[str, Any], current_depth: int) -> int:
        """Calculate the maximum nesting depth in a layout."""
        components = layout.get('components', [])
        max_depth = current_depth
        
        for comp in components:
            if comp.get('type') == ComponentType.CONTAINER.value and 'components' in comp:
                container_depth = self._calculate_max_depth(
                    {'components': comp['components']}, 
                    current_depth + 1
                )
                max_depth = max(max_depth, container_depth)
                
        return max_depth


class ComponentFactory:
    """
    Extensible factory for creating components.
    Allows plugins to register custom component types.
    """
    
    def __init__(self):
        self._creators: Dict[str, Callable] = {}
        self._register_default_components()
        
    def _register_default_components(self):
        """Register all default component creators."""
        self.register('label', self._create_label)
        self.register('button', self._create_button)
        self.register('text_edit', self._create_text_edit)
        self.register('container', self._create_container)
        self.register('icon', self._create_icon)
        self.register('image', self._create_image)
        self.register('progress', self._create_progress)
        self.register('slider', self._create_slider)
        self.register('checkbox', self._create_checkbox)
        self.register('line_edit', self._create_line_edit)
        
    def register(self, component_type: str, creator: Callable):
        """Register a component creator function."""
        self._creators[component_type] = creator
        
    def create(self, spec: Dict[str, Any], parent_tile) -> Optional[QWidget]:
        """Create a component from specification."""
        comp_type = spec.get('type')
        creator = self._creators.get(comp_type)
        
        if creator:
            return creator(spec, parent_tile)
        else:
            print(f"Unknown component type: {comp_type}")
            return None
            
    # Default component creators
    def _create_label(self, spec: Dict[str, Any], parent_tile) -> QLabel:
        widget = QLabel()
        widget.setText(spec.get('text', ''))
        widget.setAlignment(parent_tile._parse_alignment(spec.get('alignment', 'left')))
        if spec.get('word_wrap', False):
            widget.setWordWrap(True)
        return widget
        
    def _create_button(self, spec: Dict[str, Any], parent_tile) -> QPushButton:
        widget = QPushButton()
        widget.setText(spec.get('text', 'Button'))
        
        # Enhanced event mapping
        if 'action' in spec:
            widget.clicked.connect(lambda: parent_tile.handle_action(spec['action']))
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        # Additional properties
        if spec.get('checkable', False):
            widget.setCheckable(True)
        if 'checked' in spec:
            widget.setChecked(spec['checked'])
            
        return widget
        
    def _create_text_edit(self, spec: Dict[str, Any], parent_tile) -> QTextEdit:
        widget = QTextEdit()
        if spec.get('read_only', False):
            widget.setReadOnly(True)
        widget.setPlaceholderText(spec.get('placeholder', ''))
        
        # Initial text
        if 'text' in spec:
            widget.setPlainText(spec['text'])
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget
        
    def _create_line_edit(self, spec: Dict[str, Any], parent_tile) -> QLineEdit:
        widget = QLineEdit()
        widget.setPlaceholderText(spec.get('placeholder', ''))
        
        if 'text' in spec:
            widget.setText(spec['text'])
        if spec.get('password', False):
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        if 'max_length' in spec:
            widget.setMaxLength(spec['max_length'])
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget
        
    def _create_container(self, spec: Dict[str, Any], parent_tile) -> QFrame:
        widget = QFrame()
        
        # Frame style
        if spec.get('frame_style'):
            styles = {
                'box': QFrame.Shape.Box,
                'panel': QFrame.Shape.Panel,
                'styled_panel': QFrame.Shape.StyledPanel,
                'no_frame': QFrame.Shape.NoFrame
            }
            widget.setFrameStyle(styles.get(spec['frame_style'], QFrame.Shape.NoFrame))
            
        return widget
        
    def _create_icon(self, spec: Dict[str, Any], parent_tile) -> QLabel:
        widget = QLabel()
        
        # Support emoji or icon paths
        icon_data = spec.get('icon', '')
        if icon_data.startswith('/') or icon_data.startswith('./'):
            # File path
            pixmap = QPixmap(icon_data)
            if not pixmap.isNull():
                size = spec.get('size', 16)
                pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
                widget.setPixmap(pixmap)
        else:
            # Emoji or text icon
            widget.setText(icon_data)
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        return widget
        
    def _create_image(self, spec: Dict[str, Any], parent_tile) -> QLabel:
        widget = QLabel()
        
        if 'path' in spec:
            pixmap = QPixmap(spec['path'])
            if not pixmap.isNull():
                # Scale if size specified
                if 'width' in spec or 'height' in spec:
                    w = spec.get('width', pixmap.width())
                    h = spec.get('height', pixmap.height())
                    aspect_mode = Qt.AspectRatioMode.KeepAspectRatio
                    if spec.get('stretch', False):
                        aspect_mode = Qt.AspectRatioMode.IgnoreAspectRatio
                    pixmap = pixmap.scaled(w, h, aspect_mode, 
                                         Qt.TransformationMode.SmoothTransformation)
                widget.setPixmap(pixmap)
                
        widget.setAlignment(parent_tile._parse_alignment(spec.get('alignment', 'center')))
        return widget
        
    def _create_progress(self, spec: Dict[str, Any], parent_tile) -> QProgressBar:
        widget = QProgressBar()
        
        widget.setMinimum(spec.get('min', 0))
        widget.setMaximum(spec.get('max', 100))
        widget.setValue(spec.get('value', 0))
        
        if spec.get('text_visible', True):
            widget.setTextVisible(True)
        if 'format' in spec:
            widget.setFormat(spec['format'])
            
        # Orientation
        if spec.get('orientation') == 'vertical':
            widget.setOrientation(Qt.Orientation.Vertical)
            
        return widget
        
    def _create_slider(self, spec: Dict[str, Any], parent_tile) -> QSlider:
        widget = QSlider()
        
        # Orientation
        orientation = Qt.Orientation.Horizontal
        if spec.get('orientation') == 'vertical':
            orientation = Qt.Orientation.Vertical
        widget.setOrientation(orientation)
        
        # Range and value
        widget.setMinimum(spec.get('min', 0))
        widget.setMaximum(spec.get('max', 100))
        widget.setValue(spec.get('value', 50))
        
        # Tick marks
        if spec.get('tick_position'):
            positions = {
                'above': QSlider.TickPosition.TicksAbove,
                'below': QSlider.TickPosition.TicksBelow,
                'both': QSlider.TickPosition.TicksBothSides,
                'none': QSlider.TickPosition.NoTicks
            }
            widget.setTickPosition(positions.get(spec['tick_position'], QSlider.TickPosition.NoTicks))
            
        if 'tick_interval' in spec:
            widget.setTickInterval(spec['tick_interval'])
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget
        
    def _create_checkbox(self, spec: Dict[str, Any], parent_tile) -> QCheckBox:
        widget = QCheckBox()
        
        widget.setText(spec.get('text', ''))
        if 'checked' in spec:
            widget.setChecked(spec['checked'])
        if spec.get('tristate', False):
            widget.setTristate(True)
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget

    def _register_default_components(self):
        """Register all default component creators."""
        self.register('label', self._create_label)
        self.register('button', self._create_button)
        self.register('text_edit', self._create_text_edit)
        self.register('container', self._create_container)
        self.register('icon', self._create_icon)
        self.register('image', self._create_image)
        self.register('progress', self._create_progress)
        self.register('slider', self._create_slider)
        self.register('checkbox', self._create_checkbox)
        self.register('line_edit', self._create_line_edit)
        # New component types
        self.register('radio', self._create_radio)
        self.register('combo_box', self._create_combo_box)
        self.register('spin_box', self._create_spin_box)
        self.register('tab_widget', self._create_tab_widget)
        self.register('group_box', self._create_group_box)
        
    def _create_radio(self, spec: Dict[str, Any], parent_tile) -> QRadioButton:
        """Create a radio button."""
        widget = QRadioButton()
        widget.setText(spec.get('text', ''))
        
        if 'checked' in spec:
            widget.setChecked(spec['checked'])
            
        # Group name for exclusive selection
        if 'group' in spec:
            # Radio buttons with same group name will be exclusive
            widget.setObjectName(f"radio_{spec['group']}")
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget
        
    def _create_combo_box(self, spec: Dict[str, Any], parent_tile) -> QComboBox:
        """Create a combo box."""
        widget = QComboBox()
        
        # Add items
        items = spec.get('items', [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    # Item with data
                    widget.addItem(item.get('text', ''), item.get('data'))
                else:
                    # Simple string item
                    widget.addItem(str(item))
                    
        # Set current item
        if 'current_index' in spec:
            widget.setCurrentIndex(spec['current_index'])
        elif 'current_text' in spec:
            widget.setCurrentText(spec['current_text'])
            
        # Editable
        if spec.get('editable', False):
            widget.setEditable(True)
            
        # Max visible items
        if 'max_visible' in spec:
            widget.setMaxVisibleItems(spec['max_visible'])
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget
        
    def _create_spin_box(self, spec: Dict[str, Any], parent_tile) -> QSpinBox:
        """Create a spin box."""
        widget = QSpinBox()
        
        # Range
        widget.setMinimum(spec.get('min', 0))
        widget.setMaximum(spec.get('max', 100))
        widget.setValue(spec.get('value', 0))
        
        # Step
        if 'step' in spec:
            widget.setSingleStep(spec['step'])
            
        # Prefix/Suffix
        if 'prefix' in spec:
            widget.setPrefix(spec['prefix'])
        if 'suffix' in spec:
            widget.setSuffix(spec['suffix'])
            
        # Special value text (shown at minimum)
        if 'special_value' in spec:
            widget.setSpecialValueText(spec['special_value'])
            
        # Wrapping
        if spec.get('wrapping', False):
            widget.setWrapping(True)
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget
        
    def _create_tab_widget(self, spec: Dict[str, Any], parent_tile) -> QTabWidget:
        """Create a tab widget."""
        widget = QTabWidget()
        
        # Tab position
        positions = {
            'north': QTabWidget.TabPosition.North,
            'south': QTabWidget.TabPosition.South,
            'west': QTabWidget.TabPosition.West,
            'east': QTabWidget.TabPosition.East
        }
        if 'tab_position' in spec:
            widget.setTabPosition(positions.get(spec['tab_position'], QTabWidget.TabPosition.North))
            
        # Closable tabs
        if spec.get('closable', False):
            widget.setTabsClosable(True)
            
        # Movable tabs
        if spec.get('movable', False):
            widget.setMovable(True)
            
        # Add tabs
        tabs = spec.get('tabs', [])
        for tab_spec in tabs:
            if isinstance(tab_spec, dict):
                # Create tab content
                tab_widget = QWidget()
                tab_layout = QVBoxLayout(tab_widget)
                
                # Render components in tab
                if 'components' in tab_spec:
                    parent_tile._render_layout(
                        {'type': 'vertical', 'components': tab_spec['components']},
                        tab_widget
                    )
                    
                # Add tab
                title = tab_spec.get('title', 'Tab')
                icon = tab_spec.get('icon')
                if icon:
                    # Handle icon if provided
                    widget.addTab(tab_widget, title)
                else:
                    widget.addTab(tab_widget, title)
                    
                # Set tab properties
                tab_index = widget.count() - 1
                if tab_spec.get('enabled', True) == False:
                    widget.setTabEnabled(tab_index, False)
                if 'tooltip' in tab_spec:
                    widget.setTabToolTip(tab_index, tab_spec['tooltip'])
                    
        # Set current tab
        if 'current_index' in spec:
            widget.setCurrentIndex(spec['current_index'])
            
        # Events
        if 'events' in spec:
            parent_tile._map_events(widget, spec['events'])
            
        return widget
        
    def _create_group_box(self, spec: Dict[str, Any], parent_tile) -> QGroupBox:
        """Create a group box."""
        widget = QGroupBox()
        
        # Title
        widget.setTitle(spec.get('title', ''))
        
        # Checkable
        if spec.get('checkable', False):
            widget.setCheckable(True)
            if 'checked' in spec:
                widget.setChecked(spec['checked'])
                
        # Alignment
        alignments = {
            'left': Qt.AlignmentFlag.AlignLeft,
            'center': Qt.AlignmentFlag.AlignCenter,
            'right': Qt.AlignmentFlag.AlignRight
        }
        if 'title_alignment' in spec:
            widget.setAlignment(alignments.get(spec['title_alignment'], Qt.AlignmentFlag.AlignLeft))
            
        # Flat style
        if spec.get('flat', False):
            widget.setFlat(True)
            
        # Create layout for contents
        layout_type = spec.get('layout_type', 'vertical')
        layout = LayoutFactory.create(layout_type, spec)
        widget.setLayout(layout)
        
        # Render components inside
        if 'components' in spec:
            parent_tile._render_layout(
                {'type': layout_type, 'components': spec['components']},
                widget
            )
            
        return widget

# Also update the _map_events method to handle new event types:

    def _map_events(self, widget: QWidget, events: Dict[str, str]):
        """Map widget events to tile actions."""
        for event_name, action in events.items():
            if event_name == 'clicked' and hasattr(widget, 'clicked'):
                widget.clicked.connect(lambda a=action: self.handle_action(a))
            elif event_name == 'text_changed':
                if hasattr(widget, 'textChanged'):
                    widget.textChanged.connect(lambda a=action: self.handle_action(a))
                elif hasattr(widget, 'textEdited'):
                    widget.textEdited.connect(lambda text, a=action: self.handle_action(a))
            elif event_name == 'value_changed' and hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(lambda val, a=action: self.handle_action(a))
            elif event_name == 'state_changed' and hasattr(widget, 'stateChanged'):
                widget.stateChanged.connect(lambda state, a=action: self.handle_action(a))
            # New event mappings
            elif event_name == 'toggled' and hasattr(widget, 'toggled'):
                widget.toggled.connect(lambda checked, a=action: self.handle_action(a))
            elif event_name == 'current_changed':
                if hasattr(widget, 'currentIndexChanged'):  # QComboBox, QTabWidget
                    widget.currentIndexChanged.connect(lambda idx, a=action: self.handle_action(a))
                elif hasattr(widget, 'currentTextChanged'):  # QComboBox
                    widget.currentTextChanged.connect(lambda text, a=action: self.handle_action(a))
            elif event_name == 'tab_close_requested' and hasattr(widget, 'tabCloseRequested'):
                widget.tabCloseRequested.connect(lambda idx, a=action: self.handle_action(a))
            elif event_name == 'item_selected' and hasattr(widget, 'itemSelectionChanged'):
                widget.itemSelectionChanged.connect(lambda a=action: self.handle_action(a))
            # Add more event mappings as needed
class LayoutFactory:
    """Factory for creating different layout types."""
    
    @staticmethod
    def create(layout_type: str, spec: Dict[str, Any]) -> QLayout:
        """Create a layout based on type."""
        if layout_type == 'horizontal':
            layout = QHBoxLayout()
        elif layout_type == 'grid':
            layout = QGridLayout()
            # Set grid properties
            if 'column_spacing' in spec:
                layout.setHorizontalSpacing(spec['column_spacing'])
            if 'row_spacing' in spec:
                layout.setVerticalSpacing(spec['row_spacing'])
        else:  # Default to vertical
            layout = QVBoxLayout()
            
        # Common layout properties
        if 'spacing' in spec:
            if isinstance(spec['spacing'], str):
                layout.setSpacing(spacing(spec['spacing']))
            else:
                layout.setSpacing(spec['spacing'])
                
        if 'margins' in spec:
            margins = spec['margins']
            if isinstance(margins, str):
                m = spacing(margins)
                layout.setContentsMargins(m, m, m, m)
            elif isinstance(margins, list) and len(margins) == 4:
                layout.setContentsMargins(*margins)
                
        return layout


class PropertyBinding:
    """Manages property bindings between tile data and UI components."""
    
    def __init__(self, tile):
        self.tile = weakref.ref(tile)  # Weak reference to avoid circular refs
        self.bindings: Dict[str, List[Dict[str, Any]]] = {}
        
    def bind(self, data_key: str, component_id: str, property_name: str, 
             transformer: Optional[Callable] = None):
        """Bind a data key to a component property."""
        if data_key not in self.bindings:
            self.bindings[data_key] = []
            
        self.bindings[data_key].append({
            'component_id': component_id,
            'property': property_name,
            'transformer': transformer
        })
        
    def update(self, data_key: str, value: Any):
        """Update all bindings for a data key."""
        tile = self.tile()
        if not tile:
            return
            
        if data_key in self.bindings:
            for binding in self.bindings[data_key]:
                component = tile.get_component(binding['component_id'])
                if component:
                    # Apply transformer if provided
                    if binding['transformer']:
                        value = binding['transformer'](value)
                        
                    # Update component property
                    self._update_property(component, binding['property'], value)
                    
    def _update_property(self, widget: QWidget, property_name: str, value: Any):
        """Update a specific property on a widget."""
        if property_name == 'text':
            if hasattr(widget, 'setText'):
                widget.setText(str(value))
            elif hasattr(widget, 'setPlainText'):
                widget.setPlainText(str(value))
        elif property_name == 'value':
            if hasattr(widget, 'setValue'):
                widget.setValue(value)
        elif property_name == 'checked':
            if hasattr(widget, 'setChecked'):
                widget.setChecked(bool(value))
        elif property_name == 'visible':
            widget.setVisible(bool(value))
        elif property_name == 'enabled':
            widget.setEnabled(bool(value))
        # Add more property mappings as needed


class BaseTileCore(QWidget):
    """
    Core tile functionality that cannot be modified by designers.
    This handles all the critical behaviors: dragging, resizing, signals, etc.
    """
    
    # Core signals that the system depends on
    tile_moved = Signal(str, int, int)
    tile_resized = Signal(str, int, int)
    tile_content_changed = Signal(str, str)
    tile_closed = Signal(str)
    tile_design_requested = Signal(str)  # New: request design refresh
    
    def __init__(self, tile_data: Dict[str, Any]):
        super().__init__()
        self.tile_data = tile_data
        self.tile_id = self.tile_data["id"]
        self.tile_type = self.tile_data.get("type", "note")
        
        # Core behavioral state
        self.mode = None  # Can be "moving", "resizing", or None
        self.resize_margin = 25
        self.is_pinned = True  # Default pinned state
        
        # Window setup (non-negotiable for security/functionality)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        # Set initial geometry
        self.setGeometry(
            self.tile_data.get("x", 100),
            self.tile_data.get("y", 100),
            self.tile_data.get("width", 250),
            self.tile_data.get("height", 150)
        )
        
        # Create core structure (this is protected)
        self._create_core_structure()
        
        # Apply design (this can be customized)
        self._apply_design()
        
    def _create_core_structure(self):
        """Creates the non-negotiable structure of a tile."""
        # Main layout with no margins (design system will handle spacing)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Core container (designers can style this)
        self.container = QFrame(self)
        self.container.setObjectName("tileContainer")
        self.main_layout.addWidget(self.container)
        
        # Inner layout for container
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # Create chrome (header area with controls)
        self._create_chrome()
        
        # Content area (this is where designers work)
        self.content_widget = QWidget()
        self.content_widget.setObjectName("tileContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(
            spacing('sm'), spacing('sm'), spacing('sm'), spacing('sm')
        )
        self.container_layout.addWidget(self.content_widget, 1)  # Takes remaining space
        
    def _create_chrome(self):
        """Creates the tile header with drag handle and controls."""
        # Chrome container
        self.chrome_widget = QWidget()
        self.chrome_widget.setObjectName("tileChrome")
        self.chrome_layout = QHBoxLayout(self.chrome_widget)
        self.chrome_layout.setContentsMargins(spacing('xs'), spacing('xs'), spacing('xs'), spacing('xs'))
        self.chrome_layout.setSpacing(spacing('xs'))
        
        # Drag handle (invisible but functional)
        self.drag_handle = QFrame()
        self.drag_handle.setObjectName("dragHandle")
        self.drag_handle.setFixedHeight(spacing('md'))
        self.drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        self.chrome_layout.addWidget(self.drag_handle, 1)  # Takes remaining space
        
        # Control buttons container
        self.controls_widget = QWidget()
        self.controls_layout = QHBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(spacing('xs'))
        
        # Pin button
        self.pin_button = QPushButton("📌")
        self.pin_button.setObjectName("pinButton")
        self.pin_button.setFixedSize(spacing('md'), spacing('md'))
        self.pin_button.clicked.connect(self.toggle_pin)
        self.pin_button.hide()
        self.controls_layout.addWidget(self.pin_button)
        
        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(spacing('md'), spacing('md'))
        self.close_button.clicked.connect(self.close)
        self.close_button.hide()
        self.controls_layout.addWidget(self.close_button)
        
        self.chrome_layout.addWidget(self.controls_widget)
        self.container_layout.addWidget(self.chrome_widget)
        
    def _apply_design(self):
        """Applies the design system styles to the tile."""
        # Apply base tile styling from design system
        self.setStyleSheet(DesignSystem.get_tile_base_style())
        
        # Update pin button state
        self.pin_button.setProperty("pinned", self.is_pinned)
        
    def toggle_pin(self):
        """Toggles the 'Always on Top' state."""
        self.is_pinned = not self.is_pinned
        
        if self.is_pinned:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        
        self.show()
        self.pin_button.setProperty("pinned", self.is_pinned)
        # Re-apply styles to update button appearance
        self.pin_button.style().unpolish(self.pin_button)
        self.pin_button.style().polish(self.pin_button)
        
    def enterEvent(self, event):
        """Shows controls on mouse enter."""
        self.close_button.show()
        self.pin_button.show()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Hides controls on mouse leave."""
        self.close_button.hide()
        self.pin_button.hide()
        super().leaveEvent(event)
        
    def resizeEvent(self, event):
        """Ensures controls are positioned correctly."""
        super().resizeEvent(event)
        # Controls are now handled by layout, no manual positioning needed
        
    # Mouse handling for drag and resize (unchanged from original)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            in_resize_corner = (
                event.pos().x() > self.width() - self.resize_margin and
                event.pos().y() > self.height() - self.resize_margin
            )
            
            if in_resize_corner:
                self.mode = "resizing"
            elif self.drag_handle.underMouse():
                self.mode = "moving"
            else:
                self.mode = None
            
            if self.mode:
                self.mouse_press_pos = event.globalPosition().toPoint()
                self.window_press_pos = self.frameGeometry().topLeft()
                self.window_press_geometry = self.geometry()
                event.accept()
                
    def mouseMoveEvent(self, event):
        pos = event.pos()
        
        if self.mode:
            delta = event.globalPosition().toPoint() - self.mouse_press_pos
            if self.mode == "moving":
                self.move(self.window_press_pos + delta)
            elif self.mode == "resizing":
                new_width = event.pos().x()
                new_height = event.pos().y()
                min_w = 100
                min_h = 80
                self.resize(max(new_width, min_w), max(new_height, min_h))
            event.accept()
        else:
            in_resize_corner = (
                pos.x() > self.width() - self.resize_margin and
                pos.y() > self.height() - self.resize_margin
            )
            if in_resize_corner:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                
    def mouseReleaseEvent(self, event):
        if self.mode == "moving":
            self.tile_moved.emit(self.tile_id, self.x(), self.y())
        elif self.mode == "resizing":
            self.tile_resized.emit(self.tile_id, self.width(), self.height())
        self.mode = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()
        
    def closeEvent(self, event):
        """Handle close event."""
        self.tile_closed.emit(self.tile_id)
        super().closeEvent(event)


class BaseTile(BaseTileCore):
    """
    The base tile class that plugins extend.
    This adds the design specification support with constraints validation.
    """
    
    def __init__(self, tile_data: Dict[str, Any]):
        # Store the full tile data for subclasses to access
        self.tile_data = tile_data.copy()  # Make a copy to avoid mutations
        
        # Store design spec if provided
        self.design_spec = tile_data.get('design_spec', None)
        
        # Initialize component factory and property binding
        self.component_factory = ComponentFactory()
        self.property_binding = PropertyBinding(self)
        
        # Component registry for tracking created components
        self._components: Dict[str, QWidget] = {}
        
        # Event handlers registry
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Error display widget (for constraint violations)
        self._error_widget = None
        
        # Initialize core functionality
        super().__init__(tile_data)
        
        # If a design spec is provided, render it with validation
        if self.design_spec:
            self.render_design_spec(self.design_spec)
        else:
            # Load default design for this tile type
            self._load_default_design()
            
    def _load_default_design(self):
        """Load the default design for this tile type."""
        # Get the plugin registry to find default designs
        from .plugins.plugin_registry import get_registry
        registry = get_registry()
        
        tile_type = self.tile_data.get('type', 'note')
        plugin = registry.get_plugin(tile_type)
        
        if plugin:
            # Get builtin designs
            builtin_designs = plugin.get_builtin_designs()
            if builtin_designs:
                # Use the first design as default
                default_design = builtin_designs[0]
                self.render_design_spec(default_design)
            else:
                # No designs available, create minimal default
                self._create_minimal_default()
        else:
            self._create_minimal_default()
            
    def _create_minimal_default(self):
        """Create a minimal default UI when no design is available."""
        # For note tiles, create a basic text edit
        if self.tile_data.get('type') == 'note':
            text_edit = QTextEdit()
            text_edit.setObjectName("noteTextEdit")
            text_edit.setStyleSheet(DesignSystem.get_text_edit_style())
            self.content_layout.addWidget(text_edit)
            self._components["noteTextEdit"] = text_edit
        else:
            # For other tiles, just show a label
            label = QLabel(f"{self.tile_data.get('type', 'Unknown')} Tile")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(DesignSystem.get_label_style())
            self.content_layout.addWidget(label)
            
    def render_design_spec(self, spec: Dict[str, Any]):
        """
        Renders a design specification with full constraint validation.
        """
        # Get constraints for this tile type
        constraints = self._get_tile_constraints()
        
        # Validate the design with constraints
        validator = DesignValidator(self.tile_type, constraints)
        is_valid, errors, warnings = validator.validate(spec)
        
        # Show warnings if any (but continue rendering)
        if warnings:
            for warning in warnings:
                print(f"Design Warning: {warning}")
        
        # If there are errors, show them and stop
        if not is_valid:
            self._show_design_errors(errors)
            return
            
        # Clear existing content
        self.clear_content()
        
        # Clear component registry
        self._components.clear()
        
        # Apply size constraints from design
        self._apply_size_constraints(spec)
        
        # Process bindings if specified
        if 'bindings' in spec:
            self._setup_bindings(spec['bindings'])
        
        # Render the layout
        layout_spec = spec.get('layout', {})
        self._render_layout(layout_spec, self.content_widget)
        
        # Apply custom styling if provided
        styling_spec = spec.get('styling', {})
        self._apply_custom_styling(styling_spec)
        
        # Initialize bound data
        self._initialize_bound_data()
        
    def _get_tile_constraints(self) -> DesignConstraints:
        """Get constraints for this tile type from the plugin."""
        from .plugins.plugin_registry import get_registry
        registry = get_registry()
        
        plugin = registry.get_plugin(self.tile_type)
        if plugin:
            metadata = plugin.get_metadata()
            if metadata and metadata.design_constraints:
                return metadata.design_constraints
                
        # Return default constraints
        return DesignConstraints()
        
    def _apply_size_constraints(self, spec: Dict[str, Any]):
        """Apply size constraints from the design specification."""
        styling = spec.get('styling', {})
        if 'size' in styling:
            size = styling['size']
            if isinstance(size, dict):
                width = size.get('width')
                height = size.get('height')
                
                # Get current constraints
                constraints = self._get_tile_constraints()
                
                # Apply width constraints
                if width is not None:
                    # Clamp to allowed range
                    width = max(constraints.min_width, min(width, constraints.max_width))
                    self.resize(width, self.height())
                    
                # Apply height constraints
                if height is not None:
                    # Clamp to allowed range
                    height = max(constraints.min_height, min(height, constraints.max_height))
                    self.resize(self.width(), height)
        
    def _render_layout(self, layout_spec: Dict[str, Any], parent_widget: QWidget):
        """Recursively renders a layout specification."""
        # Get or create layout
        layout_type = layout_spec.get('type', 'vertical')
        
        if parent_widget == self.content_widget:
            # Replace the content layout
            old_layout = parent_widget.layout()
            if old_layout:
                QWidget().setLayout(old_layout)  # Detach old layout
            
            new_layout = LayoutFactory.create(layout_type, layout_spec)
            parent_widget.setLayout(new_layout)
            layout = new_layout
        else:
            # Create new layout for container
            layout = LayoutFactory.create(layout_type, layout_spec)
            parent_widget.setLayout(layout)
        
        # Render components
        components = layout_spec.get('components', [])
        
        for i, comp_spec in enumerate(components):
            widget = self._create_component(comp_spec)
            if widget:
                # Add to layout with positioning
                if isinstance(layout, QGridLayout) and 'grid' in comp_spec:
                    grid = comp_spec['grid']
                    row = grid.get('row', i)
                    col = grid.get('col', 0)
                    row_span = grid.get('row_span', 1)
                    col_span = grid.get('col_span', 1)
                    layout.addWidget(widget, row, col, row_span, col_span)
                else:
                    # Add stretch factors if specified
                    stretch = comp_spec.get('stretch', 0)
                    if isinstance(layout, (QHBoxLayout, QVBoxLayout)):
                        layout.addWidget(widget, stretch)
                    else:
                        layout.addWidget(widget)
                        
    def _create_component(self, comp_spec: Dict[str, Any]) -> Optional[QWidget]:
        """Creates a widget from a component specification."""
        # Handle spacers separately
        if comp_spec.get('type') == ComponentType.SPACER.value:
            # Create a spacer item instead of a widget
            spacer = QSpacerItem(
                comp_spec.get('width', 0),
                comp_spec.get('height', 0),
                QSizePolicy.Policy.Expanding if comp_spec.get('horizontal', True) else QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding if comp_spec.get('vertical', True) else QSizePolicy.Policy.Minimum
            )
            return None  # Spacer is not a widget
            
        # Use component factory
        widget = self.component_factory.create(comp_spec, self)
        
        if widget:
            comp_id = comp_spec.get('id', '')
            
            # Set object name for styling
            widget.setObjectName(comp_id)
            
            # Register component
            if comp_id:
                self._components[comp_id] = widget
            
            # Apply component style
            comp_type = comp_spec.get('type')
            style_variant = comp_spec.get('style', 'primary')
            style_size = comp_spec.get('size', 'md')
            style = DesignSystem.get_style(comp_type, style_variant, size=style_size)
            if style:
                widget.setStyleSheet(style)
                
            # Handle container recursion
            if comp_spec.get('type') == ComponentType.CONTAINER.value and 'components' in comp_spec:
                layout_spec = {
                    'type': comp_spec.get('layout_type', 'vertical'),
                    'components': comp_spec['components']
                }
                self._render_layout(layout_spec, widget)
                
            # Set size constraints if specified
            if 'min_width' in comp_spec:
                widget.setMinimumWidth(comp_spec['min_width'])
            if 'min_height' in comp_spec:
                widget.setMinimumHeight(comp_spec['min_height'])
            if 'max_width' in comp_spec:
                widget.setMaximumWidth(comp_spec['max_width'])
            if 'max_height' in comp_spec:
                widget.setMaximumHeight(comp_spec['max_height'])
            if 'fixed_width' in comp_spec:
                widget.setFixedWidth(comp_spec['fixed_width'])
            if 'fixed_height' in comp_spec:
                widget.setFixedHeight(comp_spec['fixed_height'])
                
        return widget
        
    def _map_events(self, widget: QWidget, events: Dict[str, str]):
        """Map widget events to tile actions."""
        for event_name, action in events.items():
            if event_name == 'clicked' and hasattr(widget, 'clicked'):
                widget.clicked.connect(lambda a=action: self.handle_action(a))
            elif event_name == 'text_changed':
                if hasattr(widget, 'textChanged'):
                    widget.textChanged.connect(lambda a=action: self.handle_action(a))
                elif hasattr(widget, 'textEdited'):
                    widget.textEdited.connect(lambda text, a=action: self.handle_action(a))
            elif event_name == 'value_changed' and hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(lambda val, a=action: self.handle_action(a))
            elif event_name == 'state_changed' and hasattr(widget, 'stateChanged'):
                widget.stateChanged.connect(lambda state, a=action: self.handle_action(a))
            # Add more event mappings as needed
            
    def _setup_bindings(self, bindings: List[Dict[str, Any]]):
        """Setup property bindings from design spec."""
        for binding in bindings:
            data_key = binding.get('data')
            component_id = binding.get('component')
            property_name = binding.get('property', 'text')
            transformer = binding.get('transformer')
            
            if data_key and component_id:
                # Parse transformer if it's a string expression
                if isinstance(transformer, str):
                    transformer = self._create_transformer(transformer)
                    
                self.property_binding.bind(data_key, component_id, property_name, transformer)
                
    def _create_transformer(self, expression: str) -> Callable:
        """Create a transformer function from a string expression."""
        # Simple expression parser - in production, use a proper expression evaluator
        if expression.startswith('format:'):
            format_str = expression[7:]
            return lambda val: format_str.format(val)
        elif expression == 'uppercase':
            return lambda val: str(val).upper()
        elif expression == 'lowercase':
            return lambda val: str(val).lower()
        else:
            # Default: convert to string
            return str
            
    def _initialize_bound_data(self):
        """Initialize any bound data from tile data."""
        # This would be overridden by subclasses to set initial values
        pass
        
    def _parse_alignment(self, alignment: str) -> Qt.AlignmentFlag:
        """Parse alignment string to Qt alignment flag."""
        alignments = {
            'left': Qt.AlignmentFlag.AlignLeft,
            'center': Qt.AlignmentFlag.AlignCenter,
            'right': Qt.AlignmentFlag.AlignRight,
            'top': Qt.AlignmentFlag.AlignTop,
            'bottom': Qt.AlignmentFlag.AlignBottom,
        }
        return alignments.get(alignment, Qt.AlignmentFlag.AlignLeft)
        
    def _apply_custom_styling(self, styling_spec: Dict[str, Any]):
        """Applies custom styling from the design spec."""
        # Apply theme if specified
        theme = styling_spec.get('theme', 'default')
        # Theme application would go here
        
        # Apply custom component styles
        custom_styles = styling_spec.get('custom_styles', {})
        for component_id, style_overrides in custom_styles.items():
            widget = self.get_component(component_id)
            if widget:
                # Build custom stylesheet from overrides
                custom_style = self._build_custom_style(widget, style_overrides)
                if custom_style:
                    widget.setStyleSheet(widget.styleSheet() + custom_style)
                    
    def _build_custom_style(self, widget: QWidget, overrides: Dict[str, Any]) -> str:
        """Build custom stylesheet from style overrides."""
        # This is a simplified version - in production, use a proper CSS builder
        styles = []
        
        if 'background' in overrides:
            styles.append(f"background-color: {overrides['background']};")
        if 'color' in overrides:
            styles.append(f"color: {overrides['color']};")
        if 'padding' in overrides:
            p = overrides['padding']
            if isinstance(p, str):
                p = spacing(p)
            styles.append(f"padding: {p}px;")
        if 'border' in overrides:
            styles.append(f"border: {overrides['border']};")
            
        if styles:
            widget_class = widget.__class__.__name__
            return f"{widget_class} {{ {' '.join(styles)} }}"
        return ""
        
    def _show_design_errors(self, errors: list):
        """Shows design validation errors in the content area."""
        self.clear_content()
        
        # Create scrollable error display
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: rgba(255, 0, 0, 0.1);
                border: 2px solid #f87171;
                border-radius: 8px;
            }
        """)
        
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        
        # Title
        title_label = QLabel("❌ Design Validation Failed")
        title_label.setStyleSheet("""
            QLabel {
                color: #f87171;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
            }
        """)
        error_layout.addWidget(title_label)
        
        # Error list
        for error in errors:
            error_label = QLabel(f"• {error}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet("""
                QLabel {
                    color: #fca5a5;
                    font-size: 13px;
                    padding: 4px 8px;
                }
            """)
            error_layout.addWidget(error_label)
            
        # Help text
        help_label = QLabel("\nPlease fix these errors in your design specification.")
        help_label.setStyleSheet("""
            QLabel {
                color: #fbbf24;
                font-size: 12px;
                padding: 8px;
            }
        """)
        error_layout.addWidget(help_label)
        
        error_layout.addStretch()
        
        scroll_area.setWidget(error_widget)
        self.content_layout.addWidget(scroll_area)
        self._error_widget = scroll_area
        
    def clear_content(self):
        """Clears all widgets from the content area."""
        # Clear components registry
        self._components.clear()
        
        # Clear error widget reference
        self._error_widget = None
        
        # Clear layout
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def handle_action(self, action: str):
        """
        Handle actions triggered by design components.
        Subclasses should override this to implement tile-specific actions.
        """
        print(f"Action triggered: {action}")
        
        # Emit custom event if handlers are registered
        if action in self._event_handlers:
            for handler in self._event_handlers[action]:
                handler()
                
    def register_action_handler(self, action: str, handler: Callable):
        """Register a handler for a custom action."""
        if action not in self._event_handlers:
            self._event_handlers[action] = []
        self._event_handlers[action].append(handler)
        
    def update_component_data(self, component_id: str, data: Any):
        """
        Updates data for a specific component.
        This allows tile logic to update the UI without knowing the implementation.
        """
        widget = self.get_component(component_id)
        if widget:
            if isinstance(widget, QLabel):
                widget.setText(str(data))
            elif isinstance(widget, QPushButton):
                widget.setText(str(data))
            elif isinstance(widget, QProgressBar):
                widget.setValue(int(data))
            elif isinstance(widget, QSlider):
                widget.setValue(int(data))
            elif isinstance(widget, QCheckBox):
                if isinstance(data, bool):
                    widget.setChecked(data)
                else:
                    widget.setText(str(data))
            # Add more widget types as needed...
            
    def update_bound_data(self, data_key: str, value: Any):
        """Update data through the binding system."""
        self.property_binding.update(data_key, value)
        
    def get_component(self, component_id: str) -> Optional[QWidget]:
        """
        Get a component by ID for direct manipulation.
        Use sparingly - prefer update_component_data for loose coupling.
        """
        return self._components.get(component_id)
        
    def register_component_factory(self, component_type: str, creator: Callable):
        """Allow plugins to register custom component types."""
        self.component_factory.register(component_type, creator)