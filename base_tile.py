# pinpoint/base_tile.py - The reusable, common foundation for all tiles.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QPushButton
from PySide6.QtCore import Qt, Signal, QPoint

class BaseTile(QWidget):
    """A base class for all tiles. Handles window behavior, dragging, etc."""

    tile_moved = Signal(str, int, int)
    tile_resized = Signal(str, int, int)
    tile_content_changed = Signal(str, str)
    tile_closed = Signal(str)

    def __init__(self, tile_data: dict):
        super().__init__()
        self.tile_data = tile_data
        self.tile_id = self.tile_data["id"]

        # In the __init__ method of BaseTile
        self.mode = None # Can be "moving", "resizing", or None
        self.resize_margin = 25 # The pixel size of the resize grip area
        self.setMouseTracking(True) # IMPORTANT: To get mouse move events even when not clicking
        
        # --- NEW: State for pinning ---
        # Default is pinned (Always on Top)
        self.is_pinned = True

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(
            self.tile_data["x"], self.tile_data["y"],
            self.tile_data["width"], self.tile_data["height"]
        )

        # ... (Layout setup is the same) ...
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
        self.container = QFrame(self)
        self.main_layout.addWidget(self.container)
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(10, 5, 10, 10)
        self.inner_layout.setSpacing(5)
        self.drag_handle = QFrame(self)
        self.drag_handle.setFixedHeight(20)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(0)
        self.inner_layout.addWidget(self.drag_handle)
        self.inner_layout.addLayout(self.content_layout)

        # --- Create and configure the close button ---
        self.close_button = QPushButton("✕", self)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.on_manual_close_request)
        self.close_button.hide()
        
        # --- NEW: Create and configure the pin button ---
        self.pin_button = QPushButton("📌", self) # Using a pin emoji
        self.pin_button.setFixedSize(20, 20)
        self.pin_button.setObjectName("pinButton")
        self.pin_button.clicked.connect(self.toggle_pin)
        self.pin_button.hide()

        self.set_common_style()
        self.update_pin_button_style() # Set initial style

    def set_common_style(self):
        """Sets the visual style for the tile's 'chrome' (frame/handle)."""
        self.container.setStyleSheet("QFrame { background-color: rgba(40, 40, 40, 0.9); border-radius: 8px; }")
        self.drag_handle.setStyleSheet("QFrame { background-color: transparent; border-top-left-radius: 8px; border-top-right-radius: 8px; border-bottom: 1px solid #222; }")
        self.drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        
        self.close_button.setStyleSheet("#closeButton { background-color: #555; color: #ccc; border-radius: 10px; font-family: 'Arial'; font-weight: bold; font-size: 12px; } #closeButton:hover { background-color: #E81123; color: white; }")
        
        # --- NEW: Add styling for the pin button ---
        # This uses dynamic properties to change style based on the "pinned" state
        self.pin_button.setStyleSheet("""
            #pinButton {
                background-color: #555;
                color: #ccc;
                border-radius: 10px;
                font-size: 12px;
            }
            #pinButton:hover {
                background-color: #666;
            }
            #pinButton[pinned="true"] {
                background-color: #0078D4;
                color: white;
            }
            #pinButton[pinned="true"]:hover {
                background-color: #0098f4;
            }
        """)

    # --- NEW: Method to toggle the pinned state ---
    def toggle_pin(self):
        """Toggles the 'Always on Top' state of the window."""
        self.is_pinned = not self.is_pinned
        
        if self.is_pinned:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            # To un-set a flag, we set it to False
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        
        # This is important: re-show the window for flag changes to take effect
        self.show()
        self.update_pin_button_style()

    # --- NEW: Helper method to update the button's style ---
    def update_pin_button_style(self):
        """Updates the pin button's visual state."""
        self.pin_button.setProperty("pinned", self.is_pinned)
        # Re-polish the widget to apply the new style
        self.pin_button.style().unpolish(self.pin_button)
        self.pin_button.style().polish(self.pin_button)

    def enterEvent(self, event):
        """Shows both buttons when the mouse enters."""
        self.close_button.show()
        self.pin_button.show() # Also show the pin button
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hides both buttons when the mouse leaves."""
        self.close_button.hide()
        self.pin_button.hide() # Also hide the pin button
        super().leaveEvent(event)

    def resizeEvent(self, event):
        """Positions both buttons correctly."""
        # Position close button at the top-right
        close_btn_size = self.close_button.width()
        self.close_button.move(self.width() - close_btn_size - 5, 5)
        
        # Position pin button to the left of the close button
        pin_btn_size = self.pin_button.width()
        self.pin_button.move(self.close_button.x() - pin_btn_size - 5, 5)
        
        super().resizeEvent(event)

    # ... (on_manual_close_request, mouse events, and closeEvent are unchanged) ...
    def on_manual_close_request(self):
        #self.tile_closed.emit(self.tile_id)
        self.close()


# Replace the old mousePressEvent in BaseTile
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if the click is in the resize area (bottom-right corner)
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


    # Replace the old mouseMoveEvent in BaseTile
    def mouseMoveEvent(self, event):
        pos = event.pos()
        
        # If a drag/resize action is in progress
        if self.mode:
            delta = event.globalPosition().toPoint() - self.mouse_press_pos
            if self.mode == "moving":
                self.move(self.window_press_pos + delta)
            elif self.mode == "resizing":
                # event.pos() gives the mouse position relative to the widget's top-left corner.
                # This is exactly what we need for the new width and height.
                new_width = event.pos().x()
                new_height = event.pos().y()

                # Using fixed minimums is a bit more robust here.
                min_w = 100 
                min_h = 80
                
                self.resize(max(new_width, min_w), max(new_height, min_h))

            event.accept()
        # Otherwise, just check position to update cursor style (no button pressed)
        else:
            in_resize_corner = (
                pos.x() > self.width() - self.resize_margin and
                pos.y() > self.height() - self.resize_margin
            )
            if in_resize_corner:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    # Replace the old mouseReleaseEvent in BaseTile
    def mouseReleaseEvent(self, event):
        if self.mode == "moving":
            self.tile_moved.emit(self.tile_id, self.x(), self.y())
        elif self.mode == "resizing":
            # We use the generic updated signal here too
            self.tile_resized.emit(self.tile_id, self.width(), self.height())

        self.mode = None # Reset mode
        self.setCursor(Qt.CursorShape.ArrowCursor) # Reset cursor
        event.accept()
    def closeEvent(self, event):
        super().closeEvent(event)