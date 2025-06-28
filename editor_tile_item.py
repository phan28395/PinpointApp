# pinpoint/editor_tile_item.py

from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QPen, QColor, QBrush, QPainter, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRectF, Signal, QPointF


class EditorTileItem(QGraphicsItem):
    """A custom, movable QGraphicsItem that handles its own drag logic."""

    def __init__(self, tile_instance_data: dict, tile_definition_data: dict):
        super().__init__()
        
        self.tile_instance_data = tile_instance_data
        self.tile_definition_data = tile_definition_data
        self.instance_id = self.tile_instance_data['instance_id']
        self.tile_id = self.tile_definition_data['id']
        
        self.width = self.tile_instance_data['width']
        self.height = self.tile_instance_data['height']
        
        # Visual states
        self.is_dragging = False
        self.is_hovered = False
        
        # Performance optimization: cache display text
        self._cached_display_text = self._get_display_text()
        
        # Grid snapping
        self.grid_size = 20
        self.snap_to_grid = True
        
        # Visual styling
        self.normal_brush = QBrush(QColor(70, 120, 180, 200))
        self.hover_brush = QBrush(QColor(90, 140, 200, 220))
        self.drag_brush = QBrush(QColor(100, 150, 210, 180))
        self.normal_pen = QPen(QColor(150, 180, 220), 2)
        self.hover_pen = QPen(QColor(180, 210, 250), 3)
        self.drag_pen = QPen(QColor(200, 230, 255), 3, Qt.PenStyle.DashLine)
        
        # Font setup
        self.font = QFont("Arial", 12)
        self.font_metrics = QFontMetrics(self.font)
        
        # Shadow effect for depth
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(2, 2)
        
        # Boundary constraints
        self.min_x = 0
        self.min_y = 0
        self.max_x = float('inf')
        self.max_y = float('inf')
        
        # Set initial position
        self.setPos(self.tile_instance_data['x'], self.tile_instance_data['y'])
        
        # Enable hover events
        self.setAcceptHoverEvents(True)
        
        # Set flags
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges)
        # We handle dragging manually for better control
        
        # Cache mode for better performance
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def _get_display_text(self):
        """Extract and cache the display text from tile content."""
        content = self.tile_definition_data.get('content', '')
        # Get first line or "Empty Note"
        first_line = content.split('\n')[0] if content else "Empty Note"
        # Truncate if too long
        max_chars = 30
        if len(first_line) > max_chars:
            return first_line[:max_chars-3] + "..."
        return first_line

    def boundingRect(self) -> QRectF:
        """Defines the outer boundaries of the item."""
        # Add a bit of padding for the shadow effect
        padding = 5
        return QRectF(-padding, -padding, 
                     self.width + 2*padding, 
                     self.height + 2*padding)

    def paint(self, painter: QPainter, option, widget=None):
        """Where all the drawing happens."""
        # Choose brush and pen based on state
        if self.is_dragging:
            brush = self.drag_brush
            pen = self.drag_pen
        elif self.is_hovered:
            brush = self.hover_brush
            pen = self.hover_pen
        else:
            brush = self.normal_brush
            pen = self.normal_pen
        
        # Draw shadow when not dragging (dragging makes it semi-transparent)
        if not self.is_dragging:
            painter.setOpacity(0.3)
            painter.fillRect(QRectF(2, 2, self.width, self.height), QColor(0, 0, 0))
            painter.setOpacity(1.0)
        
        # Draw the tile
        painter.setBrush(brush)
        painter.setPen(pen)
        rect = QRectF(0, 0, self.width, self.height)
        painter.drawRoundedRect(rect, 8.0, 8.0)
        
        # Draw text
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(self.font)
        
        # Calculate text rectangle with padding
        text_rect = rect.adjusted(10, 10, -10, -10)
        
        # Draw text with elision if needed
        elided_text = self.font_metrics.elidedText(
            self._cached_display_text,
            Qt.TextElideMode.ElideRight,
            int(text_rect.width())
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided_text)
        
        # Draw resize handle hint in bottom-right corner
        if self.is_hovered and not self.is_dragging:
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
            handle_size = 15
            handle_rect = QRectF(
                self.width - handle_size - 5,
                self.height - handle_size - 5,
                handle_size,
                handle_size
            )
            painter.drawRoundedRect(handle_rect, 3, 3)

    def hoverEnterEvent(self, event):
        """Called when mouse enters the item."""
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Called when mouse leaves the item."""
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Called when the user clicks on this item."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.setOpacity(0.7)  # Make semi-transparent while dragging
            self.update()
        event.accept()

    def update_display_text(self):
        """Update the cached display text when content changes."""
        self._cached_display_text = self._get_display_text()
        self.update()  # Trigger repaint
        
    def mouseMoveEvent(self, event):
        """Called when the user moves the mouse after clicking on this item."""
        if not self.is_dragging:
            return
            
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
        
        # Only update position if it actually changed (important for performance)
        if new_pos != orig_pos:
            self.setPos(new_pos)

    def mouseReleaseEvent(self, event):
        """Called when the user releases the mouse button."""
        if self.is_dragging:
            self.is_dragging = False
            self.setOpacity(1.0)  # Restore full opacity
            self.update()
            
            # Emit position update signal
            if self.scene():
                self.scene().item_position_updated.emit(self.instance_id, self.pos())
                
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """A special method called by Qt to notify of changes."""
        # Only emit signal on final position change, not during dragging
        if (change == self.GraphicsItemChange.ItemPositionHasChanged 
            and self.scene() 
            and not self.is_dragging):
            # This handles programmatic position changes
            self.scene().item_position_updated.emit(self.instance_id, value)
        
        return super().itemChange(change, value)
    
    def set_bounds(self, min_x, min_y, max_x, max_y):
        """Set the boundary constraints for this item."""
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y