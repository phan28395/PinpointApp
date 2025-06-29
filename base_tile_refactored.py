# pinpoint/base_tile_refactored.py
"""
Refactored base tile with complete separation of functionality and design.
All visual aspects are handled by the design layer.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor
from typing import Dict, Any, Optional

from .design_layer import DesignLayer
from .widget_factory import WidgetFactory


class BaseTile(QWidget):
    """
    Base tile class with complete design separation.
    This class handles ONLY functionality - all visual aspects come from design.
    """
    
    # Functional signals (behavior, not appearance)
    tile_moved = Signal(str, int, int)
    tile_resized = Signal(str, int, int)
    tile_content_changed = Signal(str, str)
    tile_closed = Signal(str)
    
    def __init__(self, tile_data: Dict[str, Any], design_layer: DesignLayer):
        super().__init__()
        
        # Store references
        self.tile_data = tile_data
        self.design = design_layer
        self.factory = WidgetFactory(design_layer)
        
        # Extract functional data
        self.tile_id = self.tile_data["id"]
        self.tile_type = self.tile_data.get("type", "note")
        
        # Functional state (not visual)
        self.is_pinned = True
        self.drag_mode = None  # Can be "moving", "resizing", or None
        
        # Window identification for design
        self.setObjectName(f"tile_window_{self.tile_type}")
        
        # Set window flags (functional requirement)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Enable transparency support (functional)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        # Create structure
        self._create_structure()
        
        # Connect signals
        self._connect_signals()
        
        # Set initial position and size from data
        self.move(
            self.tile_data.get("x", 100),
            self.tile_data.get("y", 100)
        )
        self.resize(
            self.tile_data.get("width", 250),
            self.tile_data.get("height", 150)
        )
        
        # Apply all visual design
        self.design.apply_design(self)
        
        # Let subclasses initialize their content
        self.setup_content()
    
    def _create_structure(self):
        """Create the tile structure without any styling."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Container
        self.container = self.factory.create_tile_container(self.tile_id, self.tile_type)
        self.main_layout.addWidget(self.container)
        
        # Get container's layout
        self.container_layout = self.container.layout()
        
        # Create header with controls
        self.header = self.factory.create_tile_header(self.tile_id)
        self.container_layout.addWidget(self.header)
        
        # Content area
        self.content_widget = QWidget()
        self.content_widget.setObjectName("tile_content")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addWidget(self.content_widget, 1)  # Takes remaining space
        
        # Store references to controls
        self.drag_handle = self.header.drag_handle
        self.pin_button = self.header.pin_button
        self.close_button = self.header.close_button
        
        # Initially hide controls
        self.pin_button.hide()
        self.close_button.hide()
    
    def _connect_signals(self):
        """Connect internal signals for functionality."""
        self.pin_button.clicked.connect(self.toggle_pin)
        self.close_button.clicked.connect(self.close)
    
    def setup_content(self):
        """
        Override in subclasses to set up tile-specific content.
        This is where tiles add their functional widgets.
        """
        pass
    
    def toggle_pin(self):
        """Toggle the always-on-top state."""
        self.is_pinned = not self.is_pinned
        
        if self.is_pinned:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        
        self.show()
        
        # Update button state for design system
        self.pin_button.setProperty("pinned", self.is_pinned)
        # Force style update
        self.pin_button.style().unpolish(self.pin_button)
        self.pin_button.style().polish(self.pin_button)
    
    def enterEvent(self, event):
        """Show controls on mouse enter."""
        self.close_button.show()
        self.pin_button.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hide controls on mouse leave."""
        self.close_button.hide()
        self.pin_button.hide()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging and resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get resize margin from design
            resize_margin = self.design.get_value("tile.resize_margin", 25)
            
            # Check if in resize corner
            in_resize_corner = (
                event.pos().x() > self.width() - resize_margin and
                event.pos().y() > self.height() - resize_margin
            )
            
            if in_resize_corner:
                self.drag_mode = "resizing"
            elif self.drag_handle.underMouse():
                self.drag_mode = "moving"
            else:
                self.drag_mode = None
            
            if self.drag_mode:
                self.mouse_press_pos = event.globalPosition().toPoint()
                self.window_press_pos = self.frameGeometry().topLeft()
                self.window_press_geometry = self.geometry()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging and resizing."""
        pos = event.pos()
        
        if self.drag_mode:
            delta = event.globalPosition().toPoint() - self.mouse_press_pos
            
            if self.drag_mode == "moving":
                self.move(self.window_press_pos + delta)
            elif self.drag_mode == "resizing":
                # Get minimum size from design
                min_width = self.design.get_value("tile.min_width", 100)
                min_height = self.design.get_value("tile.min_height", 80)
                
                new_width = max(event.pos().x(), min_width)
                new_height = max(event.pos().y(), min_height)
                self.resize(new_width, new_height)
            
            event.accept()
        else:
            # Update cursor for resize hint
            resize_margin = self.design.get_value("tile.resize_margin", 25)
            in_resize_corner = (
                pos.x() > self.width() - resize_margin and
                pos.y() > self.height() - resize_margin
            )
            
            if in_resize_corner:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging."""
        if self.drag_mode == "moving":
            self.tile_moved.emit(self.tile_id, self.x(), self.y())
        elif self.drag_mode == "resizing":
            self.tile_resized.emit(self.tile_id, self.width(), self.height())
        
        self.drag_mode = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()
    
    def update_display_content(self, tile_data: Dict[str, Any]):
        """
        Update tile content from external source.
        Override in subclasses to handle content updates.
        """
        pass
    
    def update_display_config(self, tile_data: Dict[str, Any]):
        """
        Update tile configuration.
        The design layer will handle visual updates automatically.
        """
        self.tile_data.update(tile_data)
        
        # Update position/size if changed
        if 'x' in tile_data or 'y' in tile_data:
            self.move(
                tile_data.get('x', self.x()),
                tile_data.get('y', self.y())
            )
        
        if 'width' in tile_data or 'height' in tile_data:
            self.resize(
                tile_data.get('width', self.width()),
                tile_data.get('height', self.height())
            )
    
    def closeEvent(self, event):
        """Handle close event."""
        self.tile_closed.emit(self.tile_id)
        super().closeEvent(event)