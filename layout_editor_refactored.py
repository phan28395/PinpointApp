# pinpoint/layout_editor_refactored.py
"""
Refactored layout editor with complete separation of design and functionality.
All visual constants and styling come from the design layer.
"""

import uuid
from enum import Enum
from PySide6.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout, 
                              QHBoxLayout, QComboBox, QLabel, QPushButton,
                              QGraphicsRectItem, QCheckBox, QToolButton,
                              QMenu, QSpinBox, QFontComboBox)
from PySide6.QtGui import QPen, QColor, QBrush, QPainter, QFont
from PySide6.QtCore import Qt, QRectF, Signal, QPointF, QTimer

from .draggable_list_widget import TILE_ID_MIME_TYPE
from .editor_tile_item_refactored import EditorTileItem
from .display_manager import get_display_manager
from .design_layer import DesignLayer
from .widget_factory import WidgetFactory


class ArrangePattern(Enum):
    """Patterns for auto-arranging tiles."""
    LEAN_LEFT = "Lean Left"
    LEAN_RIGHT = "Lean Right"
    CENTERED = "Centered"
    GRID = "Grid"
    CASCADE = "Cascade"


class LayoutEditorScene(QGraphicsScene):
    """Scene that holds layout items."""
    item_position_updated = Signal(str, QPointF)  # instance_id, new_position
    
    def __init__(self, design_layer: DesignLayer, parent=None):
        super().__init__(parent)
        self.design = design_layer
        self.display_rect_item = None
        self.display_info_item = None
        self.setObjectName("layout_editor_scene")


class LayoutView(QGraphicsView):
    """Custom graphics view for the layout editor."""
    
    def __init__(self, scene, manager, layout_data, design_layer: DesignLayer, parent=None):
        super().__init__(scene, parent)
        self.manager = manager
        self.layout_data = layout_data
        self.scene = scene
        self.design = design_layer
        self.display_manager = get_display_manager()
        
        # Set object name for styling
        self.setObjectName("layout_editor_view")
        
        # Functional properties
        self.show_display_bounds = True
        self.setAcceptDrops(True)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setDragMode(self.DragMode.NoDrag)
        
        # No scrollbars - we show exact display size
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Get visual constants from design
        self.grid_size = self.design.get_value("editor.grid_size", 20)
        self.grid_enabled = self.design.get_value("editor.grid_enabled", True)
        
        # Performance optimization
        self.setCacheMode(self.CacheModeFlag.CacheBackground)
        
    def fit_display_in_view(self):
        """Scale the view to show the entire display."""
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Get padding from design
        padding = self.design.get_value("editor.display_padding", 20)
        
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
        
        # Center the display
        self.centerOn(display.width / 2, display.height / 2)
        
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Draw background with grid from design settings."""
        super().drawBackground(painter, rect)
        
        if not self.grid_enabled:
            return
            
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Get visual properties from design
        grid_color = QColor(self.design.get_value("editor.grid_color", "#282828"))
        grid_width = self.design.get_value("editor.grid_width", 1)
        ruler_color = QColor(self.design.get_value("editor.ruler_color", "#505050"))
        ruler_width = self.design.get_value("editor.ruler_width", 1)
        ruler_interval = self.design.get_value("editor.ruler_interval", 100)
        ruler_text_interval = self.design.get_value("editor.ruler_text_interval", 200)
        
        # Font from design
        font_config = self.design.get_value("editor.ruler_font", {
            "family": "Arial",
            "size": 8
        })
        ruler_font = QFont(font_config.get("family", "Arial"), font_config.get("size", 8))
        
        # Only draw within display bounds
        display_rect = QRectF(0, 0, display.width, display.height)
        draw_rect = rect.intersected(display_rect)
        
        if draw_rect.isEmpty():
            return
            
        # Set up grid pen
        grid_pen = QPen(grid_color, grid_width, Qt.PenStyle.SolidLine)
        painter.setPen(grid_pen)
        
        left = int(draw_rect.left())
        right = int(draw_rect.right())
        top = int(draw_rect.top())
        bottom = int(draw_rect.bottom())
        
        # Draw grid lines
        first_left = left - (left % self.grid_size)
        for x in range(first_left, right + 1, self.grid_size):
            if 0 <= x <= display.width:
                painter.drawLine(x, max(0, top), x, min(display.height, bottom))
                
        first_top = top - (top % self.grid_size)
        for y in range(first_top, bottom + 1, self.grid_size):
            if 0 <= y <= display.height:
                painter.drawLine(max(0, left), y, min(display.width, right), y)
                
        # Draw rulers
        ruler_pen = QPen(ruler_color, ruler_width)
        painter.setPen(ruler_pen)
        painter.setFont(ruler_font)
        
        # Draw ruler lines and text
        for x in range(0, display.width + 1, ruler_interval):
            if left <= x <= right:
                painter.drawLine(x, max(0, top), x, min(display.height, bottom))
                if x % ruler_text_interval == 0:
                    painter.drawText(x + 2, max(15, top + 15), str(x))
                    
        for y in range(0, display.height + 1, ruler_interval):
            if top <= y <= bottom:
                painter.drawLine(max(0, left), y, min(display.width, right), y)
                if y % ruler_text_interval == 0:
                    painter.drawText(max(2, left + 2), y - 2, str(y))
                    
    def dragEnterEvent(self, event):
        """Handle drag enter."""
        if event.mimeData().hasFormat(TILE_ID_MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """Handle drag move."""
        event.acceptProposedAction()
        
    def dropEvent(self, event):
        """Handle drop event."""
        if event.mimeData().hasFormat(TILE_ID_MIME_TYPE):
            tile_id = bytes(event.mimeData().data(TILE_ID_MIME_TYPE)).decode()
            scene_pos = self.mapToScene(event.position().toPoint())
            
            display = self.display_manager.get_selected_display()
            if not display:
                event.ignore()
                return
                
            # Snap to grid if enabled
            if self.design.get_value("editor.snap_to_grid", True):
                snapped_x = round(scene_pos.x() / self.grid_size) * self.grid_size
                snapped_y = round(scene_pos.y() / self.grid_size) * self.grid_size
            else:
                snapped_x = scene_pos.x()
                snapped_y = scene_pos.y()
                
            # Get minimum tile size from design
            min_tile_size = self.design.get_value("editor.min_tile_size", 50)
            
            # Ensure within bounds
            snapped_x = max(0, min(snapped_x, display.width - min_tile_size))
            snapped_y = max(0, min(snapped_y, display.height - min_tile_size))
            
            self.manager.add_tile_to_layout(
                self.layout_data['id'],
                tile_id,
                int(snapped_x),
                int(snapped_y)
            )
            self.parent().load_items()
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def wheelEvent(self, event):
        """Disable zoom for now."""
        event.ignore()


class LayoutEditor(QWidget):
    """Main layout editor widget."""
    
    def __init__(self, layout_data: dict, manager, design_layer: DesignLayer, parent=None):
        super().__init__(parent)
        self.layout_data = layout_data
        self.manager = manager
        self.design = design_layer
        self.factory = WidgetFactory(design_layer)
        self.display_manager = get_display_manager()
        
        # Set object name for styling
        self.setObjectName("layout_editor")
        
        # Track items
        self.item_map = {}  # instance_id -> EditorTileItem
        
        # Batch position updates
        self.pending_position_updates = {}
        self.position_update_timer = QTimer()
        self.position_update_timer.timeout.connect(self._save_position_updates)
        self.position_update_timer.setSingleShot(True)
        
        # Auto-arrange state
        self.current_pattern_index = 0
        self.arrange_patterns = list(ArrangePattern)
        
        # Create UI
        self._create_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Apply design
        self.design.apply_design(self)
        
        # Initial setup
        self._update_display_selector()
        self._update_display_visualization()
        self.load_items()
        
    def _create_ui(self):
        """Create UI structure without styling."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top toolbar
        toolbar = QWidget()
        toolbar.setObjectName("layout_editor_toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Left toolbar section
        left_toolbar = QWidget()
        left_toolbar.setObjectName("toolbar_left")
        left_layout = QHBoxLayout(left_toolbar)
        
        # Select All checkbox
        self.select_all_checkbox = QCheckBox()
        self.select_all_checkbox.setObjectName("select_all_checkbox")
        self.select_all_checkbox.setText(self.design.get_text("editor.select_all", "Select All"))
        left_layout.addWidget(self.select_all_checkbox)
        
        left_layout.addSpacing(self.design.get_value("editor.toolbar_spacing", 20))
        
        toolbar_layout.addWidget(left_toolbar)
        toolbar_layout.addStretch()
        
        # Right toolbar section
        right_toolbar = QWidget()
        right_toolbar.setObjectName("toolbar_right")
        right_layout = QHBoxLayout(right_toolbar)
        
        # Display selector
        display_label = QLabel()
        display_label.setObjectName("display_label")
        display_label.setText(self.design.get_text("editor.display", "Display:"))
        right_layout.addWidget(display_label)
        
        self.display_combo = QComboBox()
        self.display_combo.setObjectName("display_selector")
        right_layout.addWidget(self.display_combo)
        
        # Display info
        self.display_info_label = QLabel()
        self.display_info_label.setObjectName("display_info")
        right_layout.addWidget(self.display_info_label)
        
        toolbar_layout.addWidget(right_toolbar)
        main_layout.addWidget(toolbar)
        
        # Second toolbar
        toolbar2 = QWidget()
        toolbar2.setObjectName("layout_editor_toolbar2")
        toolbar2_layout = QHBoxLayout(toolbar2)
        
        # Grid toggle
        self.grid_checkbox = QCheckBox()
        self.grid_checkbox.setObjectName("grid_toggle")
        self.grid_checkbox.setText(self.design.get_text("editor.show_grid", "Show Grid"))
        self.grid_checkbox.setChecked(self.design.get_value("editor.grid_enabled", True))
        toolbar2_layout.addWidget(self.grid_checkbox)
        
        # Snap to grid
        self.snap_checkbox = QCheckBox()
        self.snap_checkbox.setObjectName("snap_toggle")
        self.snap_checkbox.setText(self.design.get_text("editor.snap_to_grid", "Snap to Grid"))
        self.snap_checkbox.setChecked(self.design.get_value("editor.snap_to_grid", True))
        toolbar2_layout.addWidget(self.snap_checkbox)
        
        toolbar2_layout.addStretch()
        
        # Auto-arrange button
        self.arrange_button = QPushButton()
        self.arrange_button.setObjectName("arrange_button")
        self.arrange_button.setText(self.design.get_text("editor.auto_arrange", "✨ Auto-Arrange"))
        toolbar2_layout.addWidget(self.arrange_button)
        
        # Project button
        self.project_button = QToolButton()
        self.project_button.setObjectName("project_button")
        self.project_button.setText(self.design.get_text("editor.project", "▶️ Project"))
        self.project_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        
        # Create project menu
        project_menu = QMenu()
        project_menu.setObjectName("project_menu")
        
        project_default_action = project_menu.addAction(
            self.design.get_text("editor.project_default", "Project as Default")
        )
        project_default_action.triggered.connect(self._project_as_default)
        project_menu.addSeparator()
        
        # Add display options
        for i, display in enumerate(self.display_manager.displays):
            action = project_menu.addAction(
                self.design.get_text("editor.project_to", "Project to {display}").format(
                    display=display.display_name
                )
            )
            action.triggered.connect(lambda checked, idx=i: self._project_to_display(idx))
            
        self.project_button.setMenu(project_menu)
        toolbar2_layout.addWidget(self.project_button)
        
        main_layout.addWidget(toolbar2)
        
        # Create scene and view
        self.scene = LayoutEditorScene(self.design, self)
        self.view = LayoutView(self.scene, self.manager, self.layout_data, self.design, self)
        main_layout.addWidget(self.view)
        
    def _connect_signals(self):
        """Connect all signals."""
        # UI signals
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        self.display_combo.currentIndexChanged.connect(self._on_display_selected)
        self.grid_checkbox.toggled.connect(self._on_grid_toggled)
        self.snap_checkbox.toggled.connect(self._on_snap_toggled)
        self.arrange_button.clicked.connect(self._auto_arrange_tiles)
        self.project_button.clicked.connect(self._project_layout)
        
        # Scene signals
        self.scene.item_position_updated.connect(self.on_item_moved)
        
        # Manager signals
        self.manager.tile_updated_in_studio.connect(self.on_tile_content_updated)
        
        # Display manager signals
        self.display_manager.displays_changed.connect(self._on_displays_changed)
        
    def _on_select_all_changed(self, state):
        """Handle select all state change."""
        selected = state == Qt.CheckState.Checked
        for item in self.item_map.values():
            item.setSelected(selected)
            
    def _on_grid_toggled(self, checked):
        """Handle grid toggle."""
        self.view.grid_enabled = checked
        self.view.viewport().update()
        
    def _on_snap_toggled(self, checked):
        """Handle snap toggle."""
        # This is used during drop events
        pass
        
    def _on_display_selected(self, index: int):
        """Handle display selection."""
        self.display_manager.select_display(index)
        self._update_display_visualization()
        self._update_display_info()
        self.load_items()
        
    def _on_displays_changed(self):
        """Handle display configuration changes."""
        self._update_display_selector()
        self._update_display_visualization()
        
    def _update_display_selector(self):
        """Update display selector combo."""
        self.display_combo.blockSignals(True)
        self.display_combo.clear()
        
        for display in self.display_manager.displays:
            self.display_combo.addItem(display.display_name)
            
        if self.display_manager.selected_display_index is not None:
            self.display_combo.setCurrentIndex(self.display_manager.selected_display_index)
            
        self.display_combo.blockSignals(False)
        
    def _update_display_info(self):
        """Update display information label."""
        display = self.display_manager.get_selected_display()
        if display:
            info_template = self.design.get_text(
                "editor.display_info",
                "Native: {resolution} @ ({x}, {y})"
            )
            info_text = info_template.format(
                resolution=display.resolution_string,
                x=display.x,
                y=display.y
            )
            
            if abs(display.dpi - 96) > 5:
                scale_percent = int((display.dpi / 96) * 100)
                scale_template = self.design.get_text(
                    "editor.display_scale",
                    " | Display Scale: {scale}%"
                )
                info_text += scale_template.format(scale=scale_percent)
                
            self.display_info_label.setText(info_text)
        else:
            self.display_info_label.setText(
                self.design.get_text("editor.no_display", "No display selected")
            )
            
    def _update_display_visualization(self):
        """Update the visual representation of the display."""
        # Clear old display rectangle
        if hasattr(self.scene, 'display_rect_item') and self.scene.display_rect_item:
            try:
                self.scene.removeItem(self.scene.display_rect_item)
            except RuntimeError:
                pass
            self.scene.display_rect_item = None
            
        if hasattr(self.scene, 'display_info_item') and self.scene.display_info_item:
            try:
                self.scene.removeItem(self.scene.display_info_item)
            except RuntimeError:
                pass
            self.scene.display_info_item = None
            
        display = self.display_manager.get_selected_display()
        if not display:
            self.scene.setSceneRect(0, 0, 1920, 1080)
            return
            
        # Set scene rect to display size
        self.scene.setSceneRect(0, 0, display.width, display.height)
        
        # Draw display rectangle
        display_rect = QRectF(0, 0, display.width, display.height)
        
        # Get border style from design
        border_color = QColor(self.design.get_value("editor.display_border_color", "#6496c8"))
        border_width = self.design.get_value("editor.display_border_width", 3)
        
        pen = QPen(border_color, border_width, Qt.PenStyle.SolidLine)
        brush = QBrush(Qt.BrushStyle.NoBrush)
        
        self.scene.display_rect_item = self.scene.addRect(display_rect, pen, brush)
        self.scene.display_rect_item.setZValue(-1000)
        
        # Add display info text
        info_template = self.design.get_text(
            "editor.display_label",
            "Display {index}: {resolution}"
        )
        info_text = info_template.format(
            index=display.index + 1,
            resolution=display.resolution_string
        )
        
        self.scene.display_info_item = self.scene.addText(info_text)
        
        # Text style from design
        text_color = QColor(self.design.get_value("editor.display_text_color", "#969696"))
        font_config = self.design.get_value("editor.display_text_font", {
            "family": "Arial",
            "size": 10
        })
        
        self.scene.display_info_item.setDefaultTextColor(text_color)
        font = QFont(font_config.get("family", "Arial"), font_config.get("size", 10))
        self.scene.display_info_item.setFont(font)
        self.scene.display_info_item.setPos(5, 5)
        self.scene.display_info_item.setZValue(1000)
        
        # Fit display in view
        self.view.fit_display_in_view()
        
    def _auto_arrange_tiles(self):
        """Auto-arrange tiles in patterns."""
        if not self.item_map:
            return
            
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Get pattern
        pattern = self.arrange_patterns[self.current_pattern_index]
        
        # Get spacing from design
        tile_spacing = self.design.get_value("editor.auto_arrange_spacing", {
            "horizontal": 20,
            "vertical": 20
        })
        
        # Calculate positions
        positions = self._calculate_positions(pattern, len(self.item_map), display, tile_spacing)
        
        # Move tiles
        for i, (instance_id, item) in enumerate(self.item_map.items()):
            if i < len(positions):
                new_x, new_y = positions[i]
                new_x = max(0, min(new_x, display.width - item.width))
                new_y = max(0, min(new_y, display.height - item.height))
                
                item.setPos(new_x, new_y)
                self.pending_position_updates[instance_id] = (new_x, new_y)
                
        # Save positions
        QTimer.singleShot(500, self._save_position_updates)
        
        # Update button text
        pattern_text = self.design.get_text(f"editor.pattern_{pattern.value.lower()}", pattern.value)
        self.arrange_button.setText(f"✨ {pattern_text}")
        
        # Next pattern
        self.current_pattern_index = (self.current_pattern_index + 1) % len(self.arrange_patterns)
        
    def _calculate_positions(self, pattern: ArrangePattern, count: int, display, spacing: dict) -> list:
        """Calculate tile positions based on pattern."""
        positions = []
        h_space = spacing.get("horizontal", 20)
        v_space = spacing.get("vertical", 20)
        padding = self.design.get_value("editor.arrange_padding", 20)
        
        # Get default tile size from design
        default_tile_size = self.design.get_value("editor.default_tile_size", {
            "width": 250,
            "height": 150
        })
        tile_width = default_tile_size.get("width", 250)
        tile_height = default_tile_size.get("height", 150)
        
        if pattern == ArrangePattern.LEAN_LEFT:
            x = padding
            y = padding
            for i in range(count):
                positions.append((x, y))
                y += tile_height + v_space
                if y + tile_height > display.height:
                    y = padding
                    x += tile_width + h_space
                    
        elif pattern == ArrangePattern.LEAN_RIGHT:
            x = display.width - tile_width - padding
            y = padding
            for i in range(count):
                positions.append((x, y))
                y += tile_height + v_space
                if y + tile_height > display.height:
                    y = padding
                    x -= tile_width + h_space
                    
        elif pattern == ArrangePattern.CENTERED:
            total_width = min(count * (tile_width + h_space), display.width - 2 * padding)
            tiles_per_row = max(1, total_width // (tile_width + h_space))
            rows = (count + tiles_per_row - 1) // tiles_per_row
            
            total_height = rows * (tile_height + v_space)
            start_y = (display.height - total_height) // 2
            
            for i in range(count):
                row = i // tiles_per_row
                col = i % tiles_per_row
                row_width = min(tiles_per_row, count - row * tiles_per_row) * (tile_width + h_space)
                start_x = (display.width - row_width) // 2
                
                x = start_x + col * (tile_width + h_space)
                y = start_y + row * (tile_height + v_space)
                positions.append((x, y))
                
        elif pattern == ArrangePattern.GRID:
            cols = max(1, int((display.width - 2 * padding) // (tile_width + h_space)))
            for i in range(count):
                row = i // cols
                col = i % cols
                x = padding + col * (tile_width + h_space)
                y = padding + row * (tile_height + v_space)
                positions.append((x, y))
                
        elif pattern == ArrangePattern.CASCADE:
            cascade_offset = self.design.get_value("editor.cascade_offset", 30)
            x = padding
            y = padding
            for i in range(count):
                positions.append((x, y))
                x += cascade_offset
                y += cascade_offset
                if x + tile_width > display.width or y + tile_height > display.height:
                    x = padding
                    y = padding
                    
        return positions
        
    def _project_layout(self):
        """Project the layout."""
        display_index = self.display_combo.currentIndex()
        self.manager.project_layout(self.layout_data['id'], display_index)
        
    def _project_as_default(self):
        """Project as default startup layout."""
        from PySide6.QtCore import QSettings
        settings = QSettings("PinPoint", "PinPoint")
        settings.setValue("default_layout_id", self.layout_data['id'])
        self._project_layout()
        
    def _project_to_display(self, display_index):
        """Project to specific display."""
        self.manager.project_layout(self.layout_data['id'], display_index)
        
    def on_item_moved(self, instance_id, new_pos):
        """Handle item position updates."""
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        item = self.item_map.get(instance_id)
        if not item:
            return
            
        # Clamp to display bounds
        max_x = display.width - item.width
        max_y = display.height - item.height
        
        x = max(0, min(new_pos.x(), max_x))
        y = max(0, min(new_pos.y(), max_y))
        
        if x != new_pos.x() or y != new_pos.y():
            item.setPos(x, y)
            
        # Queue update
        self.pending_position_updates[instance_id] = (x, y)
        
        # Debounce saves
        save_delay = self.design.get_value("editor.position_save_delay", 100)
        self.position_update_timer.stop()
        self.position_update_timer.start(save_delay)
        
    def _save_position_updates(self):
        """Save pending position updates."""
        if not self.pending_position_updates:
            return
            
        for instance_id, (x, y) in self.pending_position_updates.items():
            self.manager.update_tile_instance_position(
                self.layout_data['id'],
                instance_id,
                int(x),
                int(y)
            )
            
        self.pending_position_updates.clear()
        
    def on_tile_content_updated(self, tile_data: dict):
        """Update tile display when content changes."""
        self.update_tile_display(tile_data)
        
    def update_tile_display(self, tile_data: dict):
        """Update a single tile's display."""
        tile_id = tile_data.get('id')
        if not tile_id:
            return
            
        for instance_id, item in self.item_map.items():
            if item.tile_id == tile_id:
                item.tile_definition_data = tile_data
                item.update_display_text()
                item.update()
                
    def load_items(self):
        """Load all tile items."""
        # Save pending updates
        self.position_update_timer.stop()
        self._save_position_updates()
        
        # Clear existing
        self.scene.clear()
        self.item_map.clear()
        
        # Clear references
        if hasattr(self.scene, 'display_rect_item'):
            self.scene.display_rect_item = None
        if hasattr(self.scene, 'display_info_item'):
            self.scene.display_info_item = None
            
        # Re-add display visualization
        self._update_display_visualization()
        
        # Get latest data
        latest_layout_data = self.manager.get_layout_by_id(self.layout_data['id'])
        if not latest_layout_data:
            return
        self.layout_data = latest_layout_data
        
        # Check for migration needs
        needs_saving = False
        for instance_data in self.layout_data.get("tile_instances", []):
            if "instance_id" not in instance_data:
                instance_data["instance_id"] = f"inst_{uuid.uuid4()}"
                needs_saving = True
                
        if needs_saving:
            # Save migration
            full_app_data = self.manager.storage.load_data()
            for i, layout in enumerate(full_app_data['layouts']):
                if layout['id'] == self.layout_data['id']:
                    full_app_data['layouts'][i] = self.layout_data
                    break
            self.manager.storage.save_data(full_app_data)
            
        # Get display bounds
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Create items
        for instance_data in self.layout_data.get("tile_instances", []):
            tile_def = self.manager.get_tile_by_id(instance_data['tile_id'])
            if tile_def:
                # Ensure within bounds
                x = instance_data.get('x', 0)
                y = instance_data.get('y', 0)
                width = instance_data.get('width', 250)
                height = instance_data.get('height', 150)
                
                x = max(0, min(x, display.width - width))
                y = max(0, min(y, display.height - height))
                
                if x != instance_data.get('x', 0) or y != instance_data.get('y', 0):
                    instance_data['x'] = x
                    instance_data['y'] = y
                    needs_saving = True
                    
                # Create item with design layer
                item = EditorTileItem(instance_data, tile_def, self.design)
                item.set_bounds(0, 0, display.width, display.height)
                self.scene.addItem(item)
                self.item_map[instance_data['instance_id']] = item
                
        if needs_saving:
            self.manager.update_layout_display(
                self.layout_data['id'],
                self.display_manager.selected_display_index
            )
            
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self._update_display_info()
        self._update_display_visualization()
        self.load_items()
        
    def resizeEvent(self, event):
        """Handle resize event."""
        super().resizeEvent(event)
        if hasattr(self, 'view'):
            self.view.fit_display_in_view()
            
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        self.position_update_timer.stop()
        self._save_position_updates()
        
    def closeEvent(self, event):
        """Handle close event."""
        self.position_update_timer.stop()
        self._save_position_updates()
        
        # Disconnect signals
        try:
            self.manager.tile_updated_in_studio.disconnect(self.on_tile_content_updated)
            self.display_manager.displays_changed.disconnect(self._on_displays_changed)
        except:
            pass
            
        super().closeEvent(event)