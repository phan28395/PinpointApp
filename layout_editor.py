# pinpoint/layout_editor.py

import uuid
from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout
from PySide6.QtGui import QPen, QColor, QBrush, QPainter
from PySide6.QtCore import Qt, QRectF, Signal, QPointF, QTimer
from .draggable_list_widget import TILE_ID_MIME_TYPE
from .editor_tile_item import EditorTileItem


class LayoutEditorScene(QGraphicsScene):
    """
    The logical scene that holds the items. It defines the 'world' coordinates
    and emits signals when items are changed by other objects.
    """
    item_position_updated = Signal(str, QPointF) # instance_id, new_position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # The scene has a large, fixed size and does NOT draw the grid itself.
        self.setSceneRect(-10000, -10000, 20000, 20000)


class LayoutView(QGraphicsView):
    """A custom QGraphicsView that handles drag-and-drop events."""
    
    def __init__(self, scene, manager, layout_data, parent=None):
        super().__init__(scene, parent)
        self.manager = manager
        self.layout_data = layout_data
        self.scene = scene
        self.setAcceptDrops(True)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setDragMode(self.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QGraphicsView { background-color: #2D2D2D; border: none; }")
        
        # Grid settings
        self.grid_size = 20
        self.grid_pen = QPen(QColor(60, 60, 60), 1, Qt.PenStyle.SolidLine)
        
        # Performance optimization: cache grid drawing
        self.setCacheMode(self.CacheModeFlag.CacheBackground)
        
    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        painter.setPen(self.grid_pen)
        
        left = int(rect.left())
        right = int(rect.right())
        top = int(rect.top())
        bottom = int(rect.bottom())
        
        # Draw vertical lines
        first_left = left - (left % self.grid_size)
        for x in range(first_left, right, self.grid_size):
            painter.drawLine(x, top, x, bottom)
            
        # Draw horizontal lines
        first_top = top - (top % self.grid_size)
        for y in range(first_top, bottom, self.grid_size):
            painter.drawLine(left, y, right, y)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(TILE_ID_MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Called as the drag moves over the view."""
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat(TILE_ID_MIME_TYPE):
            tile_id = bytes(event.mimeData().data(TILE_ID_MIME_TYPE)).decode()
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # Snap to grid for cleaner placement
            snapped_x = round(scene_pos.x() / self.grid_size) * self.grid_size
            snapped_y = round(scene_pos.y() / self.grid_size) * self.grid_size
            
            self.manager.add_tile_to_layout(
                self.layout_data['id'], 
                tile_id, 
                snapped_x, 
                snapped_y
            )
            self.parent().load_items()
            event.acceptProposedAction()
        else:
            event.ignore()

    def wheelEvent(self, event):
        """
        Overrides the default wheel event to do nothing.
        This prevents the view from zooming with the mouse wheel.
        """
        event.accept() # We accept the event to stop it from propagating further.


class LayoutEditor(QWidget):
    """The main widget for the layout editor, containing the view and scene."""
    
    def __init__(self, layout_data: dict, manager, parent=None):
        super().__init__(parent)
        self.layout_data = layout_data
        self.manager = manager
        
        # Track items for efficient updates
        self.item_map = {}  # instance_id -> EditorTileItem
        
        # Batch position updates
        self.pending_position_updates = {}
        self.position_update_timer = QTimer()
        self.position_update_timer.timeout.connect(self._save_position_updates)
        self.position_update_timer.setSingleShot(True)
        
        # Create scene and view
        self.scene = LayoutEditorScene(self)
        self.scene.item_position_updated.connect(self.on_item_moved)
        
        self.view = LayoutView(self.scene, self.manager, self.layout_data, self)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        
        # Subscribe to tile updates
        self.manager.tile_updated_in_studio.connect(self.on_tile_content_updated)
        
        # Initial load
        self.load_items()

    def on_item_moved(self, instance_id, new_pos):
        """Batch position updates for better performance."""
        # Queue the position update
        self.pending_position_updates[instance_id] = (new_pos.x(), new_pos.y())
        
        # Restart the timer (debounce)
        self.position_update_timer.stop()
        self.position_update_timer.start(100)  # 100ms delay for position updates
        
    def _save_position_updates(self):
        """Save all pending position updates in batch."""
        if not self.pending_position_updates:
            return
            
        # Process each update
        for instance_id, (x, y) in self.pending_position_updates.items():
            self.manager.update_tile_instance_position(
                self.layout_data['id'],
                instance_id,
                x,
                y
            )
            
        # Clear pending updates
        self.pending_position_updates.clear()
        
    def on_tile_content_updated(self, tile_data: dict):
        """Update tile display when content changes."""
        self.update_tile_display(tile_data)
        
    def update_tile_display(self, tile_data: dict):
        """Efficiently update a single tile's display without reloading everything."""
        tile_id = tile_data.get('id')
        if not tile_id:
            return
            
        # Update all instances of this tile
        for instance_id, item in self.item_map.items():
            if item.tile_id == tile_id:
                # Update the item's data
                item.tile_definition_data = tile_data
                item.update_display_text()  # Update cached text
                item.update()  # Trigger repaint
                
    def load_items(self):
        """Load items with better performance and tracking."""
        # Save any pending position updates before reloading
        self.position_update_timer.stop()
        self._save_position_updates()
        
        # Clear existing items efficiently
        self.scene.clear()
        self.item_map.clear()
        
        # Get latest layout data
        latest_layout_data = self.manager.get_layout_by_id(self.layout_data['id'])
        if not latest_layout_data:
            return
        self.layout_data = latest_layout_data

        # --- Automatic Data Migration ---
        needs_saving = False
        for instance_data in self.layout_data.get("tile_instances", []):
            if "instance_id" not in instance_data:
                instance_data["instance_id"] = f"inst_{uuid.uuid4()}"
                needs_saving = True
                
        if needs_saving:
            print("Upgrading layout data with new unique instance_ids...")
            # This save is tricky, we need to save the whole app data structure
            full_app_data = self.manager.storage.load_data()
            for i, layout in enumerate(full_app_data['layouts']):
                if layout['id'] == self.layout_data['id']:
                    full_app_data['layouts'][i] = self.layout_data
                    break
            self.manager.storage.save_data(full_app_data)
        # --- End Migration ---

        # Create items and track them
        for instance_data in self.layout_data.get("tile_instances", []):
            tile_def = self.manager.get_tile_by_id(instance_data['tile_id'])
            if tile_def:
                item = EditorTileItem(instance_data, tile_def)
                self.scene.addItem(item)
                # Track the item
                self.item_map[instance_data['instance_id']] = item
                
    def showEvent(self, event):
        """Refresh when becoming visible."""
        super().showEvent(event)
        # Reload items to ensure we have the latest data
        self.load_items()
        
    def hideEvent(self, event):
        """Save pending changes when hiding."""
        super().hideEvent(event)
        # Save any pending position updates
        self.position_update_timer.stop()
        self._save_position_updates()
        
    def closeEvent(self, event):
        """Cleanup when closing."""
        # Save pending updates
        self.position_update_timer.stop()
        self._save_position_updates()
        
        # Disconnect signals
        try:
            self.manager.tile_updated_in_studio.disconnect(self.on_tile_content_updated)
        except:
            pass
            
        super().closeEvent(event)