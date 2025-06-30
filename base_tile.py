# pinpoint/base_tile.py - Enhanced with better design rendering

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFrame, QPushButton, QHBoxLayout, 
                              QLabel, QTextEdit, QLineEdit, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QPoint
from typing import Dict, Any, Optional
from .design_system import DesignSystem, ComponentType, spacing, color


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
    This adds the design specification support on top of core functionality.
    """
    
    def __init__(self, tile_data: Dict[str, Any]):
        # Store the full tile data for subclasses to access
        self.tile_data = tile_data.copy()  # Make a copy to avoid mutations
        
        # Store design spec if provided
        self.design_spec = tile_data.get('design_spec', None)
        
        # Initialize core functionality
        super().__init__(tile_data)
        
        # If a design spec is provided, render it
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
        else:
            # For other tiles, just show a label
            label = QLabel(f"{self.tile_data.get('type', 'Unknown')} Tile")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(DesignSystem.get_label_style())
            self.content_layout.addWidget(label)
            
    def render_design_spec(self, spec: Dict[str, Any]):
        """
        Renders a design specification into the content area.
        This is what allows third-party designs to work.
        """
        # Validate the design spec first
        is_valid, errors = DesignSystem.validate_design_spec(spec)
        if not is_valid:
            self._show_design_errors(errors)
            return
            
        # Clear existing content
        self.clear_content()
        
        # Render the layout
        layout_spec = spec.get('layout', {})
        self._render_layout(layout_spec, self.content_layout)
        
        # Apply custom styling if provided
        styling_spec = spec.get('styling', {})
        self._apply_custom_styling(styling_spec)
        
    def _render_layout(self, layout_spec: Dict[str, Any], parent_layout: QVBoxLayout):
        """Recursively renders a layout specification."""
        components = layout_spec.get('components', [])
        
        for comp_spec in components:
            widget = self._create_component(comp_spec)
            if widget:
                parent_layout.addWidget(widget)
                
    def _create_component(self, comp_spec: Dict[str, Any]) -> Optional[QWidget]:
        """Creates a widget from a component specification."""
        comp_type = comp_spec.get('type')
        comp_id = comp_spec.get('id', '')
        
        # Create widget based on type
        widget = None
        
        if comp_type == ComponentType.LABEL.value:
            widget = QLabel()
            widget.setText(comp_spec.get('text', ''))
            widget.setAlignment(self._parse_alignment(comp_spec.get('alignment', 'left')))
            
        elif comp_type == ComponentType.BUTTON.value:
            widget = QPushButton()
            widget.setText(comp_spec.get('text', 'Button'))
            if 'action' in comp_spec:
                # Connect to tile action handler
                widget.clicked.connect(lambda: self.handle_action(comp_spec['action']))
                
        elif comp_type == ComponentType.TEXT_EDIT.value:
            widget = QTextEdit()
            if comp_spec.get('read_only', False):
                widget.setReadOnly(True)
            widget.setPlaceholderText(comp_spec.get('placeholder', ''))
                
        elif comp_type == ComponentType.CONTAINER.value:
            widget = QFrame()
            # Recursively render container contents
            container_layout = QVBoxLayout(widget)
            if 'components' in comp_spec:
                layout_spec = {'components': comp_spec['components']}
                self._render_layout(layout_spec, container_layout)
                
        elif comp_type == ComponentType.SPACER.value:
            # Create a spacer item instead of a widget
            spacer = QSpacerItem(
                comp_spec.get('width', 0),
                comp_spec.get('height', 0),
                QSizePolicy.Policy.Expanding if comp_spec.get('horizontal', True) else QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding if comp_spec.get('vertical', True) else QSizePolicy.Policy.Minimum
            )
            parent_layout.addItem(spacer)
            return None  # Spacer is not a widget
            
        # Add more component types as needed...
        
        if widget:
            # Set object name for styling
            widget.setObjectName(comp_id)
            
            # Apply component style
            style_variant = comp_spec.get('style', 'primary')
            style_size = comp_spec.get('size', 'md')
            style = DesignSystem.get_style(comp_type, style_variant, size=style_size)
            if style:
                widget.setStyleSheet(style)
                
        return widget
        
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
            widget = self.findChild(QWidget, component_id)
            if widget:
                # Apply style overrides safely
                # This would need more implementation
                pass
                
    def _show_design_errors(self, errors: list):
        """Shows design validation errors in the content area."""
        self.clear_content()
        error_label = QLabel("\n".join([
            "❌ Design Specification Errors:",
            "",
            *errors
        ]))
        error_label.setWordWrap(True)
        error_label.setStyleSheet(DesignSystem.get_label_style('error'))
        self.content_layout.addWidget(error_label)
        
    def clear_content(self):
        """Clears all widgets from the content area."""
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
        
    def update_component_data(self, component_id: str, data: Any):
        """
        Updates data for a specific component.
        This allows tile logic to update the UI without knowing the implementation.
        """
        widget = self.findChild(QWidget, component_id)
        if widget:
            if isinstance(widget, QLabel):
                widget.setText(str(data))
            elif isinstance(widget, QPushButton):
                widget.setText(str(data))
            # Add more widget types as needed...
            
    def get_component(self, component_id: str) -> Optional[QWidget]:
        """
        Get a component by ID for direct manipulation.
        Use sparingly - prefer update_component_data for loose coupling.
        """
        return self.findChild(QWidget, component_id)