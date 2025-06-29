# pinpoint/editor_tile_item_refactored.py
"""
Refactored editor tile item with complete separation of visual styling from functionality.
All visual properties come from the design layer.
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QColor, QBrush, QPainter, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRectF, QPointF

from .design_layer import DesignLayer


class EditorTileItem(QGraphicsItem):
    """
    A graphics item representing a tile in the layout editor.
    All visual properties come from the design layer.
    """
    
    def __init__(self, tile_instance_data: dict, tile_definition_data: dict, design_layer: DesignLayer):
        super().__init__()
        
        # Store data
        self.tile_instance_data = tile_instance_data
        self.tile_definition_data = tile_definition_data
        self.design = design_layer
        
        # Extract IDs
        self.instance_id = self.tile_instance_data['instance_id']
        self.tile_id = self.tile_definition_data['id']
        self.tile_type = self.tile_definition_data.get('type', 'note')
        
        # Size from instance data
        self.width = self.tile_instance_data['width']
        self.height = self.tile_instance_data['height']
        
        # Functional state
        self.is_dragging = False
        self.is_hovered = False
        self.snap_to_grid = True
        
        # Boundary constraints
        self.min_x = 0
        self.min_y = 0
        self.max_x = float('inf')
        self.max_y = float('inf')
        
        # Set position
        self.setPos(self.tile_instance_data['x'], self.tile_instance_data['y'])
        
        # Enable hover events
        self.setAcceptHoverEvents(True)
        
        # Set flags
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Cache mode for performance
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        
        # Cache display text
        self._cached_display_text = self._get_display_text()
        
        # Get visual properties from design
        self._load_visual_properties()
        
    def _load_visual_properties(self):
        """Load all visual properties from design layer."""
        # Grid settings
        self.grid_size = self.design.get_value("editor.grid_size", 20)
        
        # Colors for different states
        colors = self.design.get_value("editor.tile_item.colors", {
            "normal": {"fill": "#4678b4", "border": "#96b4dc"},
            "hover": {"fill": "#5a8cc8", "border": "#b4d2fa"},
            "drag": {"fill": "#6496d2", "border": "#c8e6ff"},
            "selected": {"fill": "#78aae6", "border": "#dcf0ff"}
        })
        
        # Create brushes
        self.normal_brush = QBrush(QColor(colors["normal"]["fill"]))
        self.hover_brush = QBrush(QColor(colors["hover"]["fill"]))
        self.drag_brush = QBrush(QColor(colors["drag"]["fill"]))
        self.selected_brush = QBrush(QColor(colors["selected"]["fill"]))
        
        # Create pens
        border_width = self.design.get_value("editor.tile_item.border_width", 2)
        self.normal_pen = QPen(QColor(colors["normal"]["border"]), border_width)
        self.hover_pen = QPen(QColor(colors["hover"]["border"]), border_width + 1)
        self.drag_pen = QPen(QColor(colors["drag"]["border"]), border_width + 1, Qt.PenStyle.DashLine)
        self.selected_pen = QPen(QColor(colors["selected"]["border"]), border_width + 1)
        
        # Shadow settings
        shadow_config = self.design.get_value("editor.tile_item.shadow", {
            "enabled": True,
            "color": "#000000",
            "opacity": 0.3,
            "offset": {"x": 2, "y": 2},
            "blur": 0
        })
        self.shadow_enabled = shadow_config.get("enabled", True)
        self.shadow_color = QColor(shadow_config.get("color", "#000000"))
        self.shadow_color.setAlphaF(shadow_config.get("opacity", 0.3))
        self.shadow_offset = QPointF(
            shadow_config["offset"].get("x", 2),
            shadow_config["offset"].get("y", 2)
        )
        
        # Font settings
        font_config = self.design.get_value("editor.tile_item.font", {
            "family": "Arial",
            "size": 12,
            "weight": "normal"
        })
        self.font = QFont(font_config.get("family", "Arial"))
        self.font.setPointSize(font_config.get("size", 12))
        if font_config.get("weight") == "bold":
            self.font.setWeight(QFont.Weight.Bold)
        self.font_metrics = QFontMetrics(self.font)
        
        # Text color
        self.text_color = QColor(self.design.get_value("editor.tile_item.text_color", "#ffffff"))
        
        # Corner radius
        self.corner_radius = self.design.get_value("editor.tile_item.corner_radius", 8)
        
        # Resize handle
        self.resize_handle_size = self.design.get_value("editor.tile_item.resize_handle_size", 15)
        self.resize_handle_margin = self.design.get_value("editor.tile_item.resize_handle_margin", 5)
        
    def _get_display_text(self):
        """Extract display text from tile content."""
        content = self.tile_definition_data.get('content', '')
        first_line = content.split('\n')[0] if content else "Empty Note"
        
        max_chars = self.design.get_value("editor.tile_item.max_text_chars", 30)
        if len(first_line) > max_chars:
            return first_line[:max_chars-3] + "..."
        return first_line
        
    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle."""
        padding = self.design.get_value("editor.tile_item.bounding_padding", 5)
        return QRectF(-padding, -padding, 
                     self.width + 2*padding, 
                     self.height + 2*padding)
        
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the tile item."""
        # Choose brush and pen based on state
        if self.is_dragging:
            brush = self.drag_brush
            pen = self.drag_pen
        elif self.isSelected():
            brush = self.selected_brush
            pen = self.selected_pen
        elif self.is_hovered:
            brush = self.hover_brush
            pen = self.hover_pen
        else:
            brush = self.normal_brush
            pen = self.normal_pen
            
        # Draw shadow if enabled and not dragging
        if self.shadow_enabled and not self.is_dragging:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.shadow_color))
            shadow_rect = QRectF(
                self.shadow_offset.x(),
                self.shadow_offset.y(),
                self.width,
                self.height
            )
            painter.drawRoundedRect(shadow_rect, self.corner_radius, self.corner_radius)
            
        # Draw the tile
        painter.setBrush(brush)
        painter.setPen(pen)
        rect = QRectF(0, 0, self.width, self.height)
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # Draw text
        painter.setPen(self.text_color)
        painter.setFont(self.font)
        
        # Text padding from design
        text_padding = self.design.get_value("editor.tile_item.text_padding", 10)
        text_rect = rect.adjusted(text_padding, text_padding, -text_padding, -text_padding)
        
        # Draw text with elision
        elided_text = self.font_metrics.elidedText(
            self._cached_display_text,
            Qt.TextElideMode.ElideRight,
            int(text_rect.width())
        )
        
        # Text alignment from design
        text_align = self.design.get_value("editor.tile_item.text_align", "center")
        alignment = Qt.AlignmentFlag.AlignCenter
        if text_align == "left":
            alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        elif text_align == "right":
            alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            
        painter.drawText(text_rect, alignment, elided_text)
        
        # Draw resize handle if hovered and not dragging
        if self.is_hovered and not self.is_dragging:
            handle_color = QColor(self.design.get_value("editor.tile_item.resize_handle_color", "#ffffff"))
            handle_color.setAlpha(100)
            painter.setPen(QPen(handle_color, 1))
            
            handle_fill = QColor(handle_color)
            handle_fill.setAlpha(50)
            painter.setBrush(QBrush(handle_fill))
            
            handle_rect = QRectF(
                self.width - self.resize_handle_size - self.resize_handle_margin,
                self.height - self.resize_handle_size - self.resize_handle_margin,
                self.resize_handle_size,
                self.resize_handle_size
            )
            painter.drawRoundedRect(handle_rect, 3, 3)
            
    def hoverEnterEvent(self, event):
        """Handle hover enter."""
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Handle hover leave."""
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            resize_margin = self.design.get_value("editor.tile_item.resize_margin", 25)
            
            # Check if in resize corner
            in_resize_corner = (
                event.pos().x() > self.width - resize_margin and
                event.pos().y() > self.height - resize_margin
            )
            
            if in_resize_corner:
                self.drag_mode = "resizing"
            else:
                self.drag_mode = "moving"
                self.is_dragging = True
                
            self.drag_start_pos = event.pos()
            
            # Opacity while dragging from design
            drag_opacity = self.design.get_value("editor.tile_item.drag_opacity", 0.7)
            self.setOpacity(drag_opacity)
            
            self.update()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        if not hasattr(self, 'drag_mode'):
            return
            
        if self.drag_mode == "moving":
            # Calculate new position
            orig_pos = self.pos()
            delta = event.pos() - self.drag_start_pos
            new_pos = orig_pos + delta
            
            # Apply grid snapping if enabled
            if self.snap_to_grid:
                new_pos.setX(round(new_pos.x() / self.grid_size) * self.grid_size)
                new_pos.setY(round(new_pos.y() / self.grid_size) * self.grid_size)
                
            # Apply boundary constraints
            new_x = max(self.min_x, min(new_pos.x(), self.max_x - self.width))
            new_y = max(self.min_y, min(new_pos.y(), self.max_y - self.height))
            new_pos.setX(new_x)
            new_pos.setY(new_y)
            
            # Only update if position changed
            if new_pos != orig_pos:
                self.setPos(new_pos)
                
        elif self.drag_mode == "resizing":
            # Handle resize
            min_size = self.design.get_value("editor.tile_item.min_size", {
                "width": 100,
                "height": 80
            })
            
            new_width = max(event.pos().x(), min_size.get("width", 100))
            new_height = max(event.pos().y(), min_size.get("height", 80))
            
            # Apply grid snapping to size if enabled
            if self.snap_to_grid:
                new_width = round(new_width / self.grid_size) * self.grid_size
                new_height = round(new_height / self.grid_size) * self.grid_size
                
            if new_width != self.width or new_height != self.height:
                self.prepareGeometryChange()
                self.width = new_width
                self.height = new_height
                self.update()
                
        event.accept()
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if hasattr(self, 'drag_mode'):
            if self.drag_mode == "moving":
                self.is_dragging = False
                # Emit position update
                if self.scene():
                    self.scene().item_position_updated.emit(self.instance_id, self.pos())
                    
            elif self.drag_mode == "resizing":
                # Emit size update
                if self.scene():
                    # This would need to be added to the scene
                    pass
                    
            delattr(self, 'drag_mode')
            self.setOpacity(1.0)
            self.update()
            
        super().mouseReleaseEvent(event)
        
    def itemChange(self, change, value):
        """Handle item changes."""
        if (change == self.GraphicsItemChange.ItemPositionHasChanged 
            and self.scene() 
            and not self.is_dragging):
            # Handle programmatic position changes
            self.scene().item_position_updated.emit(self.instance_id, value)
            
        return super().itemChange(change, value)
        
    def set_bounds(self, min_x, min_y, max_x, max_y):
        """Set boundary constraints."""
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        
    def update_display_text(self):
        """Update the cached display text."""
        self._cached_display_text = self._get_display_text()
        self.update()