# pinpoint/layout_editor.py

import uuid
from PySide6.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout, 
                              QHBoxLayout, QComboBox, QLabel, QPushButton,
                              QGraphicsRectItem, QGraphicsTextItem)
from PySide6.QtGui import QPen, QColor, QBrush, QPainter, QFont
from PySide6.QtCore import Qt, QRectF, Signal, QPointF, QTimer
from .draggable_list_widget import TILE_ID_MIME_TYPE
from .editor_tile_item import EditorTileItem
from .display_manager import get_display_manager


class LayoutEditorScene(QGraphicsScene):
    """
    The logical scene that holds the items. It defines the 'world' coordinates
    and emits signals when items are changed by other objects.
    """
    item_position_updated = Signal(str, QPointF) # instance_id, new_position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # We'll set scene rect dynamically based on display
        self.display_rect_item = None
        self.display_info_item = None


class LayoutView(QGraphicsView):
    """A custom QGraphicsView that handles drag-and-drop events and display visualization."""
    
    def __init__(self, scene, manager, layout_data, parent=None):
        super().__init__(scene, parent)
        self.manager = manager
        self.layout_data = layout_data
        self.scene = scene
        self.display_manager = get_display_manager()
        
        # Display visualization
        self.show_display_bounds = True
        
        self.setAcceptDrops(True)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setDragMode(self.DragMode.NoDrag)
        
        # Fixed view - no scrollbars needed since we show exact display size
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.setStyleSheet("QGraphicsView { background-color: #1a1a1a; border: none; }")
        
        # Grid settings
        self.grid_size = 20
        self.grid_pen = QPen(QColor(40, 40, 40), 1, Qt.PenStyle.SolidLine)
        self.ruler_pen = QPen(QColor(80, 80, 80), 1, Qt.PenStyle.SolidLine)
        
        # Performance optimization: cache grid drawing
        self.setCacheMode(self.CacheModeFlag.CacheBackground)
        
    def fit_display_in_view(self):
        """Scale the view to show the entire display with some padding."""
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Calculate scale to fit display with padding
        padding = 20
        viewport_rect = self.viewport().rect()
        available_width = viewport_rect.width() - (2 * padding)
        available_height = viewport_rect.height() - (2 * padding)
        
        if available_width <= 0 or available_height <= 0:
            return
            
        # Calculate scale to fit
        scale_x = available_width / display.width
        scale_y = available_height / display.height
        scale = min(scale_x, scale_y)
        
        # Apply the scale
        self.resetTransform()
        self.scale(scale, scale)
        
        # Center the display in the view
        self.centerOn(display.width / 2, display.height / 2)
        
    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        
        # Get display bounds
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Only draw grid within display bounds
        display_rect = QRectF(0, 0, display.width, display.height)
        draw_rect = rect.intersected(display_rect)
        
        if draw_rect.isEmpty():
            return
        
        painter.setPen(self.grid_pen)
        
        left = int(draw_rect.left())
        right = int(draw_rect.right())
        top = int(draw_rect.top())
        bottom = int(draw_rect.bottom())
        
        # Draw vertical lines
        first_left = left - (left % self.grid_size)
        for x in range(first_left, right + 1, self.grid_size):
            if 0 <= x <= display.width:
                painter.drawLine(x, max(0, top), x, min(display.height, bottom))
            
        # Draw horizontal lines
        first_top = top - (top % self.grid_size)
        for y in range(first_top, bottom + 1, self.grid_size):
            if 0 <= y <= display.height:
                painter.drawLine(max(0, left), y, min(display.width, right), y)
            
        # Draw rulers at 100px intervals
        painter.setPen(self.ruler_pen)
        painter.setFont(QFont("Arial", 8))
        
        # Draw measurements on major grid lines (every 100px)
        for x in range(0, display.width + 1, 100):
            if left <= x <= right:
                painter.drawLine(x, max(0, top), x, min(display.height, bottom))
                if x % 200 == 0:  # Show text every 200px
                    painter.drawText(x + 2, max(15, top + 15), str(x))
                    
        for y in range(0, display.height + 1, 100):
            if top <= y <= bottom:
                painter.drawLine(max(0, left), y, min(display.width, right), y)
                if y % 200 == 0:  # Show text every 200px
                    painter.drawText(max(2, left + 2), y - 2, str(y))

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
            
            # Get display bounds
            display = self.display_manager.get_selected_display()
            if not display:
                event.ignore()
                return
            
            # Snap to grid for cleaner placement
            snapped_x = round(scene_pos.x() / self.grid_size) * self.grid_size
            snapped_y = round(scene_pos.y() / self.grid_size) * self.grid_size
            
            # Ensure drop is within display bounds (with minimum tile size of 50x50)
            snapped_x = max(0, min(snapped_x, display.width - 50))
            snapped_y = max(0, min(snapped_y, display.height - 50))
            
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
        """Disable zoom with mouse wheel."""
        # Do nothing - no zooming allowed
        event.ignore()


class LayoutEditor(QWidget):
    """The main widget for the layout editor, containing the view and scene."""
    
    def __init__(self, layout_data: dict, manager, parent=None):
        super().__init__(parent)
        self.layout_data = layout_data
        self.manager = manager
        self.display_manager = get_display_manager()
        
        # Track items for efficient updates
        self.item_map = {}  # instance_id -> EditorTileItem
        
        # Batch position updates
        self.pending_position_updates = {}
        self.position_update_timer = QTimer()
        self.position_update_timer.timeout.connect(self._save_position_updates)
        self.position_update_timer.setSingleShot(True)
        
        # Create UI
        self._create_ui()
        
        # Connect display manager signals
        self.display_manager.displays_changed.connect(self._on_displays_changed)
        
        # Subscribe to tile updates
        self.manager.tile_updated_in_studio.connect(self.on_tile_content_updated)
        
        # Initial setup
        self._update_display_selector()
        self._update_display_visualization()
        self.load_items()
        
    def _create_ui(self):
        """Create the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Display selector
        toolbar_layout.addWidget(QLabel("Display:"))
        self.display_combo = QComboBox()
        self.display_combo.currentIndexChanged.connect(self._on_display_selected)
        toolbar_layout.addWidget(self.display_combo)
        
        # Display info
        self.display_info_label = QLabel()
        toolbar_layout.addWidget(self.display_info_label)
        
        toolbar_layout.addStretch()
        
        # Scale info (read-only)
        self.scale_info_label = QLabel("Scale: Fit to view")
        toolbar_layout.addWidget(self.scale_info_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # Create scene and view
        self.scene = LayoutEditorScene(self)
        self.scene.item_position_updated.connect(self.on_item_moved)
        
        self.view = LayoutView(self.scene, self.manager, self.layout_data, self)
        main_layout.addWidget(self.view)
        
    def _update_display_selector(self):
        """Update the display selector combo box."""
        self.display_combo.blockSignals(True)
        self.display_combo.clear()
        
        for display in self.display_manager.displays:
            self.display_combo.addItem(display.display_name)
            
        # Select the current display
        if self.display_manager.selected_display_index is not None:
            self.display_combo.setCurrentIndex(self.display_manager.selected_display_index)
            
        self.display_combo.blockSignals(False)
        
    def _on_display_selected(self, index: int):
        """Handle display selection."""
        self.display_manager.select_display(index)
        self._update_display_visualization()
        self._update_display_info()
        self.load_items()  # Reload items for new display bounds
        
    def _on_displays_changed(self):
        """Handle display configuration changes."""
        self._update_display_selector()
        self._update_display_visualization()
        
    def _update_display_info(self):
        """Update the display information label."""
        display = self.display_manager.get_selected_display()
        if display:
            # Show native resolution and position
            info_text = f"Native: {display.resolution_string} @ ({display.x}, {display.y})"
            
            # Add DPI/scale info if significantly different from 96 DPI (standard)
            if abs(display.dpi - 96) > 5:  # More than 5 DPI difference
                scale_percent = int((display.dpi / 96) * 100)
                info_text += f" | Display Scale: {scale_percent}%"
                
            self.display_info_label.setText(info_text)
        else:
            self.display_info_label.setText("No display selected")
            
    def _update_display_visualization(self):
        """Update the visual representation of the display in the scene."""
        # Clear old display rectangle
        if hasattr(self.scene, 'display_rect_item') and self.scene.display_rect_item:
            try:
                self.scene.removeItem(self.scene.display_rect_item)
            except RuntimeError:
                # Item was already deleted
                pass
            self.scene.display_rect_item = None
            
        if hasattr(self.scene, 'display_info_item') and self.scene.display_info_item:
            try:
                self.scene.removeItem(self.scene.display_info_item)
            except RuntimeError:
                # Item was already deleted
                pass
            self.scene.display_info_item = None
            
        display = self.display_manager.get_selected_display()
        if not display:
            # Set a default scene rect if no display
            self.scene.setSceneRect(0, 0, 1920, 1080)
            return
            
        # Set scene rect to exactly match display (no extra margin)
        self.scene.setSceneRect(0, 0, display.width, display.height)
        
        # Draw display rectangle border
        display_rect = QRectF(0, 0, display.width, display.height)
        pen = QPen(QColor(100, 150, 200), 3, Qt.PenStyle.SolidLine)
        brush = QBrush(Qt.BrushStyle.NoBrush)  # No fill
        
        self.scene.display_rect_item = self.scene.addRect(display_rect, pen, brush)
        self.scene.display_rect_item.setZValue(-1000)  # Behind everything
        
        # Add display info text in top-left corner
        info_text = f"Display {display.index + 1}: {display.resolution_string}"
        self.scene.display_info_item = self.scene.addText(info_text)
        self.scene.display_info_item.setDefaultTextColor(QColor(150, 150, 150))
        font = QFont("Arial", 10)
        self.scene.display_info_item.setFont(font)
        self.scene.display_info_item.setPos(5, 5)
        self.scene.display_info_item.setZValue(1000)  # On top
        
        # Fit display in view
        self.view.fit_display_in_view()

    def on_item_moved(self, instance_id, new_pos):
        """Batch position updates for better performance."""
        # Get display bounds
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Get the item to check its size
        item = self.item_map.get(instance_id)
        if not item:
            return
            
        # Clamp position to display bounds
        max_x = display.width - item.width
        max_y = display.height - item.height
        
        x = max(0, min(new_pos.x(), max_x))
        y = max(0, min(new_pos.y(), max_y))
        
        # Update item position if it was clamped
        if x != new_pos.x() or y != new_pos.y():
            item.setPos(x, y)
            
        # Queue the position update
        self.pending_position_updates[instance_id] = (x, y)
        
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
        
        # Clear references to deleted items
        if hasattr(self.scene, 'display_rect_item'):
            self.scene.display_rect_item = None
        if hasattr(self.scene, 'display_info_item'):
            self.scene.display_info_item = None
        
        # Re-add display visualization
        self._update_display_visualization()
        
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

        # Get current display bounds
        display = self.display_manager.get_selected_display()
        if not display:
            return

        # Create items and track them
        for instance_data in self.layout_data.get("tile_instances", []):
            tile_def = self.manager.get_tile_by_id(instance_data['tile_id'])
            if tile_def:
                # Ensure tile is within bounds
                x = instance_data.get('x', 0)
                y = instance_data.get('y', 0)
                width = instance_data.get('width', 250)
                height = instance_data.get('height', 150)
                
                # Clamp to display bounds
                x = max(0, min(x, display.width - width))
                y = max(0, min(y, display.height - height))
                
                # Update instance data if position was clamped
                if x != instance_data.get('x', 0) or y != instance_data.get('y', 0):
                    instance_data['x'] = x
                    instance_data['y'] = y
                    needs_saving = True
                
                item = EditorTileItem(instance_data, tile_def)
                # Set bounds constraint on the item
                item.set_bounds(0, 0, display.width, display.height)
                self.scene.addItem(item)
                # Track the item
                self.item_map[instance_data['instance_id']] = item
                
        # Save if any positions were clamped
        if needs_saving:
            self.manager.update_layout_display(self.layout_data['id'], 
                                             self.display_manager.selected_display_index)
                
    def showEvent(self, event):
        """Refresh when becoming visible."""
        super().showEvent(event)
        # Update display info and reload items
        self._update_display_info()
        self._update_display_visualization()
        self.load_items()
        
    def resizeEvent(self, event):
        """Handle widget resize to refit display."""
        super().resizeEvent(event)
        # Refit the display when the widget is resized
        if hasattr(self, 'view'):
            self.view.fit_display_in_view()
        
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
            self.display_manager.displays_changed.disconnect(self._on_displays_changed)
        except:
            pass
            
        super().closeEvent(event)