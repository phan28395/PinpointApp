# pinpoint/layout_editor.py

import uuid
import os
import platform
from enum import Enum
from PySide6.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout, 
                              QHBoxLayout, QComboBox, QLabel, QPushButton,
                              QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem,
                              QApplication, QCheckBox, QFontComboBox, QSpinBox,
                              QColorDialog, QFileDialog, QButtonGroup, QRadioButton,
                              QMenu, QToolButton)
from PySide6.QtGui import QPen, QColor, QBrush, QPainter, QFont, QPixmap, QScreen, QPalette
from PySide6.QtCore import Qt, QRectF, Signal, QPointF, QTimer, QPropertyAnimation, QEasingCurve
from .draggable_list_widget import TILE_ID_MIME_TYPE
from .editor_tile_item import EditorTileItem
from .display_manager import get_display_manager


class ArrangePattern(Enum):
    """Patterns for auto-arranging tiles."""
    LEAN_LEFT = "Lean Left"
    LEAN_RIGHT = "Lean Right"
    CENTERED = "Centered"
    GRID = "Grid"
    CASCADE = "Cascade"
    

class TileTheme:
    """Predefined tile themes."""
    THEMES = {
        "Default": {
            "background": "rgba(40, 40, 40, 0.9)",
            "text": "#eeeeee",
            "border": "#666666"
        },
        "Light": {
            "background": "rgba(250, 250, 250, 0.9)",
            "text": "#333333",
            "border": "#cccccc"
        },
        "Dark": {
            "background": "rgba(20, 20, 20, 0.95)",
            "text": "#ffffff",
            "border": "#444444"
        },
        "Blue": {
            "background": "rgba(40, 70, 120, 0.9)",
            "text": "#ddeeff",
            "border": "#5a7a9e"
        },
        "Green": {
            "background": "rgba(46, 125, 50, 0.9)",
            "text": "#ffffff",
            "border": "#2e7d32"
        },
        "Purple": {
            "background": "rgba(123, 31, 162, 0.9)",
            "text": "#ffffff",
            "border": "#7b1fa2"
        },
        "Glass": {
            "background": "rgba(255, 255, 255, 0.1)",
            "text": "#ffffff",
            "border": "rgba(255, 255, 255, 0.3)"
        },
        "Paper": {
            "background": "rgba(245, 241, 227, 0.95)",
            "text": "#586e75",
            "border": "#dcd8c8"
        }
    }


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
        # Removed wallpaper_item
        self.select_all_checkbox = None


class LayoutView(QGraphicsView):
    """A custom QGraphicsView that handles drag-and-drop events and display visualization."""
    
    def __init__(self, scene, manager, layout_data, parent=None):
        super().__init__(scene, parent)
        self.manager = manager
        self.layout_data = layout_data
        self.scene = scene
        self.display_manager = get_display_manager()
        
        # Display visualization (removed wallpaper variables)
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
        self.grid_pen = QPen(QColor(40, 40, 40, 180), 1, Qt.PenStyle.SolidLine)
        self.ruler_pen = QPen(QColor(80, 80, 80, 180), 1, Qt.PenStyle.SolidLine)
        
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
        
        # Auto-arrange state
        self.current_pattern_index = 0
        self.arrange_patterns = list(ArrangePattern)
        
        # Layout settings (with defaults)
        self.layout_settings = layout_data.get("settings", {
            "theme": "Default",
            "overlappable": True,
            "start_with_system": False,
            "global_font_family": "Arial",
            "global_font_size": 14
        })
        
        # Create UI
        self._create_ui()
        
        # Connect display manager signals
        self.display_manager.displays_changed.connect(self._on_displays_changed)
        
        # Subscribe to tile updates
        self.manager.tile_updated_in_studio.connect(self.on_tile_content_updated)
        
        # Initial setup
        self._update_display_selector()
        self._update_display_visualization()
        self._apply_theme()
        self.load_items()
        
    def _create_ui(self):
        """Create the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left side of toolbar
        left_toolbar = QHBoxLayout()
        
        # Select All checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        left_toolbar.addWidget(self.select_all_checkbox)
        
        left_toolbar.addSpacing(20)
        
        # Theme selector
        left_toolbar.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(TileTheme.THEMES.keys()))
        self.theme_combo.addItem("Custom...")
        self.theme_combo.setCurrentText(self.layout_settings.get("theme", "Default"))
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        left_toolbar.addWidget(self.theme_combo)
        
        # Theme from image button
        self.theme_from_image_btn = QPushButton("🎨 From Image")
        self.theme_from_image_btn.clicked.connect(self._create_theme_from_image)
        left_toolbar.addWidget(self.theme_from_image_btn)
        
        toolbar_layout.addLayout(left_toolbar)
        toolbar_layout.addStretch()
        
        # Middle toolbar
        middle_toolbar = QHBoxLayout()
        
        # Font settings
        middle_toolbar.addWidget(QLabel("Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.layout_settings.get("global_font_family", "Arial")))
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        middle_toolbar.addWidget(self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.layout_settings.get("global_font_size", 14))
        self.font_size_spin.valueChanged.connect(self._on_font_size_changed)
        middle_toolbar.addWidget(self.font_size_spin)
        
        toolbar_layout.addLayout(middle_toolbar)
        toolbar_layout.addStretch()
        
        # Right side of toolbar
        right_toolbar = QHBoxLayout()
        
        # Display selector
        right_toolbar.addWidget(QLabel("Display:"))
        self.display_combo = QComboBox()
        self.display_combo.currentIndexChanged.connect(self._on_display_selected)
        right_toolbar.addWidget(self.display_combo)
        
        # Display info
        self.display_info_label = QLabel()
        right_toolbar.addWidget(self.display_info_label)
        
        toolbar_layout.addLayout(right_toolbar)
        
        main_layout.addLayout(toolbar_layout)
        
        # Second toolbar row
        toolbar2_layout = QHBoxLayout()
        toolbar2_layout.setContentsMargins(5, 0, 5, 5)
        
        # Overlappable toggle
        self.overlappable_checkbox = QCheckBox("🔲 Overlappable")
        self.overlappable_checkbox.setChecked(self.layout_settings.get("overlappable", True))
        self.overlappable_checkbox.stateChanged.connect(self._on_overlappable_changed)
        toolbar2_layout.addWidget(self.overlappable_checkbox)
        
        # Start with system
        self.startup_checkbox = QCheckBox("🚀 Start with System")
        self.startup_checkbox.setChecked(self.layout_settings.get("start_with_system", False))
        self.startup_checkbox.stateChanged.connect(self._on_startup_changed)
        toolbar2_layout.addWidget(self.startup_checkbox)
        
        toolbar2_layout.addStretch()
        
        # Wallpaper toggle (disabled but kept for future use)
        self.wallpaper_button = QPushButton("🖼️ Wallpaper")
        self.wallpaper_button.setCheckable(True)
        self.wallpaper_button.setChecked(False)  # Disabled by default
        self.wallpaper_button.setEnabled(False)  # Disabled functionality
        self.wallpaper_button.setToolTip("Wallpaper preview coming in future update")
        toolbar2_layout.addWidget(self.wallpaper_button)
        
        # Auto-arrange button
        self.arrange_button = QPushButton("✨ Auto-Arrange")
        self.arrange_button.clicked.connect(self._auto_arrange_tiles)
        toolbar2_layout.addWidget(self.arrange_button)
        
        # Project button with dropdown
        self.project_button = QToolButton()
        self.project_button.setText("▶️ Project")
        self.project_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.project_button.clicked.connect(self._project_layout)
        
        # Create project menu
        project_menu = QMenu()
        self.project_default_action = project_menu.addAction("Project as Default")
        self.project_default_action.triggered.connect(self._project_as_default)
        project_menu.addSeparator()
        
        # Add display options
        for i, display in enumerate(self.display_manager.displays):
            action = project_menu.addAction(f"Project to {display.display_name}")
            action.triggered.connect(lambda checked, idx=i: self._project_to_display(idx))
            
        self.project_button.setMenu(project_menu)
        toolbar2_layout.addWidget(self.project_button)
        
        # Scale info
        self.scale_info_label = QLabel("Scale: Fit to view")
        toolbar2_layout.addWidget(self.scale_info_label)
        
        main_layout.addLayout(toolbar2_layout)
        
        # Create scene and view
        self.scene = LayoutEditorScene(self)
        self.scene.item_position_updated.connect(self.on_item_moved)
        
        self.view = LayoutView(self.scene, self.manager, self.layout_data, self)
        main_layout.addWidget(self.view)
        
    def _on_select_all_changed(self, state):
        """Handle select all checkbox state change."""
        selected = state == Qt.CheckState.Checked
        for item in self.item_map.values():
            item.setSelected(selected)
            
    def _on_theme_changed(self, theme_name):
        """Handle theme selection."""
        if theme_name == "Custom...":
            # Open color picker for custom theme
            color = QColorDialog.getColor(Qt.GlobalColor.blue, self, "Choose Theme Color")
            if color.isValid():
                # Create custom theme based on color
                self.layout_settings["theme"] = "Custom"
                self.layout_settings["custom_theme"] = {
                    "background": f"rgba({color.red()}, {color.green()}, {color.blue()}, 0.9)",
                    "text": "#ffffff" if color.lightness() < 128 else "#000000",
                    "border": color.darker().name()
                }
        else:
            self.layout_settings["theme"] = theme_name
            
        self._apply_theme()
        self._save_layout_settings()
        
    def _create_theme_from_image(self):
        """Create theme from an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image for Theme",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            # Extract dominant color from image
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Simple color extraction - get color from center
                image = pixmap.toImage()
                center_color = image.pixelColor(image.width() // 2, image.height() // 2)
                
                # Create theme from color
                self.layout_settings["theme"] = "Custom"
                self.layout_settings["custom_theme"] = {
                    "background": f"rgba({center_color.red()}, {center_color.green()}, {center_color.blue()}, 0.9)",
                    "text": "#ffffff" if center_color.lightness() < 128 else "#000000",
                    "border": center_color.darker().name()
                }
                
                self.theme_combo.setCurrentText("Custom...")
                self._apply_theme()
                self._save_layout_settings()
                
    def _apply_theme(self):
        """Apply the selected theme to all tiles."""
        theme_name = self.layout_settings.get("theme", "Default")
        
        if theme_name == "Custom" and "custom_theme" in self.layout_settings:
            theme = self.layout_settings["custom_theme"]
        else:
            theme = TileTheme.THEMES.get(theme_name, TileTheme.THEMES["Default"])
            
        # Apply to all tiles
        for item in self.item_map.values():
            # Update item appearance based on theme
            # This is a simplified version - actual implementation would update tile colors
            item.update()
            
    def _on_font_changed(self, font):
        """Handle font family change."""
        self.layout_settings["global_font_family"] = font.family()
        self._apply_global_font()
        self._save_layout_settings()
        
    def _on_font_size_changed(self, size):
        """Handle font size change."""
        self.layout_settings["global_font_size"] = size
        self._apply_global_font()
        self._save_layout_settings()
        
    def _apply_global_font(self):
        """Apply global font settings to all tiles."""
        font_family = self.layout_settings.get("global_font_family", "Arial")
        font_size = self.layout_settings.get("global_font_size", 14)
        
        # This would be applied to actual tiles when they support it
        # For now, just save the settings
        
    def _on_overlappable_changed(self, state):
        """Handle overlappable toggle."""
        self.layout_settings["overlappable"] = state == Qt.CheckState.Checked
        self._save_layout_settings()
        
    def _on_startup_changed(self, state):
        """Handle startup toggle."""
        self.layout_settings["start_with_system"] = state == Qt.CheckState.Checked
        self._save_layout_settings()
        
        if self.layout_settings["start_with_system"]:
            # Mark this layout as default
            self._set_as_default_layout()
            
    def _set_as_default_layout(self):
        """Set this layout as the default startup layout."""
        # Save to app settings
        from PySide6.QtCore import QSettings
        settings = QSettings("PinPoint", "PinPoint")
        settings.setValue("default_layout_id", self.layout_data['id'])
        
    def _project_layout(self):
        """Project the layout to its target display."""
        display_index = self.display_combo.currentIndex()
        self.manager.project_layout(self.layout_data['id'], display_index)
        
    def _project_as_default(self):
        """Project as default and save as startup layout."""
        self._set_as_default_layout()
        self._project_layout()
        
    def _project_to_display(self, display_index):
        """Project to a specific display."""
        self.manager.project_layout(self.layout_data['id'], display_index)
        
    def _save_layout_settings(self):
        """Save layout settings to storage."""
        # Update layout data with settings
        self.layout_data["settings"] = self.layout_settings
        
        # Save to storage
        app_data = self.manager.storage.load_data()
        for layout in app_data.get("layouts", []):
            if layout['id'] == self.layout_data['id']:
                layout["settings"] = self.layout_settings
                break
                
        self.manager.storage.save_data(app_data)
        
    # Removed all wallpaper-related functions:
    # - _toggle_wallpaper()
    # - _capture_display_wallpaper()
    # - _get_wallpaper_path()
    # - _update_wallpaper()
        
    def _auto_arrange_tiles(self):
        """Auto-arrange tiles in different patterns."""
        if not self.item_map:
            return
            
        display = self.display_manager.get_selected_display()
        if not display:
            return
            
        # Get current pattern
        pattern = self.arrange_patterns[self.current_pattern_index]
        
        # Calculate positions based on pattern
        positions = self._calculate_positions(pattern, len(self.item_map), display)
        
        # Animate tiles to new positions
        for i, (instance_id, item) in enumerate(self.item_map.items()):
            if i < len(positions):
                new_x, new_y = positions[i]
                # Ensure within bounds
                new_x = max(0, min(new_x, display.width - item.width))
                new_y = max(0, min(new_y, display.height - item.height))
                
                # Create animation
                self._animate_item_to_position(item, new_x, new_y)
                
                # Queue position update
                self.pending_position_updates[instance_id] = (new_x, new_y)
        
        # Save positions after animation
        QTimer.singleShot(500, self._save_position_updates)
        
        # Update button text to show current pattern
        self.arrange_button.setText(f"✨ {pattern.value}")
        
        # Cycle to next pattern
        self.current_pattern_index = (self.current_pattern_index + 1) % len(self.arrange_patterns)
        
    def _calculate_positions(self, pattern: ArrangePattern, count: int, display) -> list:
        """Calculate tile positions based on pattern."""
        positions = []
        padding = 20
        
        if pattern == ArrangePattern.LEAN_LEFT:
            # Stack tiles on the left side
            x = padding
            y = padding
            for i in range(count):
                positions.append((x, y))
                y += 180  # Default tile height + spacing
                if y + 150 > display.height:
                    y = padding
                    x += 270  # Default tile width + spacing
                    
        elif pattern == ArrangePattern.CENTERED:
            # Center tiles in the display
            total_width = min(count * 270, display.width - 2 * padding)
            tiles_per_row = max(1, total_width // 270)
            rows = (count + tiles_per_row - 1) // tiles_per_row
            
            total_height = rows * 180
            start_y = (display.height - total_height) // 2
            
            for i in range(count):
                row = i // tiles_per_row
                col = i % tiles_per_row
                row_width = min(tiles_per_row, count - row * tiles_per_row) * 270
                start_x = (display.width - row_width) // 2
                
                x = start_x + col * 270
                y = start_y + row * 180
                positions.append((x, y))
                
        elif pattern == ArrangePattern.GRID:
            # Evenly distributed grid
            cols = max(1, int((display.width - 2 * padding) / 270))
            for i in range(count):
                row = i // cols
                col = i % cols
                x = padding + col * ((display.width - 2 * padding) // cols)
                y = padding + row * 180
                positions.append((x, y))
                
        elif pattern == ArrangePattern.CASCADE:
            # Windows-style cascade
            offset = 30
            x = padding
            y = padding
            for i in range(count):
                positions.append((x, y))
                x += offset
                y += offset
                if x + 250 > display.width or y + 150 > display.height:
                    x = padding
                    y = padding
                    
        return positions
        
    def _animate_item_to_position(self, item, x, y):
        """Animate item to new position."""
        # Simple position setting for now (can be enhanced with QPropertyAnimation)
        item.setPos(x, y)
        
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
        # Removed wallpaper_item reference
        
        # Re-add display visualization
        self._update_display_visualization()
        
        # Get latest layout data
        latest_layout_data = self.manager.get_layout_by_id(self.layout_data['id'])
        if not latest_layout_data:
            return
        self.layout_data = latest_layout_data
        
        # Update settings from loaded data
        self.layout_settings = self.layout_data.get("settings", self.layout_settings)

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