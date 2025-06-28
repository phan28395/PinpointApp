# pinpoint/note_tile.py - A specific tile for displaying text notes.

from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import QTimer
from .base_tile import BaseTile


class NoteTile(BaseTile):
    """A concrete implementation of BaseTile for text notes."""
    
    def __init__(self, tile_data: dict):
        # Initialize the parent BaseTile, which does all the heavy lifting
        super().__init__(tile_data)
        
        # Flag to prevent circular updates
        self._updating_content = False
        
        # --- NoteTile Specific Setup ---
        self.text_edit = QTextEdit()
        self.text_edit.setText(self.tile_data["content"])
        
        # Add our specific widget to the content area provided by the parent
        self.content_layout.addWidget(self.text_edit)
        
        # Set styles specific to this tile type
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #eee;
                border: none;
                font-size: 14px;
            }
        """)
        
        # Debouncing for text changes
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._emit_content_change)
        self.update_timer.setSingleShot(True)
        self.pending_content = None
        
        # Connect signals specific to this tile type
        self.text_edit.textChanged.connect(self.on_content_changed)
        
    def update_display_content(self, tile_data: dict):
        """
        This is a 'slot' that receives update signals from the TileManager.
        It updates the text editor but only if the update is for this specific tile.
        """
        # Check if the broadcasted update is for me
        if self.tile_id != tile_data.get('id'):
            return
            
        # Get the new content
        new_content = tile_data.get('content', '')
        
        # Check if we have a pending update with this exact content
        if self.pending_content == new_content:
            return
            
        # Check if content is actually different from what's displayed
        current_content = self.text_edit.toPlainText()
        
        if current_content != new_content:
            # Set flag to prevent circular updates
            self._updating_content = True
            
            # Store cursor position to restore it after update
            cursor = self.text_edit.textCursor()
            cursor_position = cursor.position()
            
            # Update the content
            self.text_edit.setPlainText(new_content)
            
            # Restore cursor position if possible
            if cursor_position <= len(new_content):
                cursor.setPosition(cursor_position)
                self.text_edit.setTextCursor(cursor)
            
            # Clear the flag
            self._updating_content = False
            
    def on_content_changed(self):
        """Handles text changes with debouncing."""
        # Ignore changes if we're updating from external source
        if self._updating_content:
            return
            
        # Store the pending content
        self.pending_content = self.text_edit.toPlainText()
        
        # Restart the timer (debounce)
        self.update_timer.stop()
        self.update_timer.start(300)  # 300ms delay
        
    def _emit_content_change(self):
        """Emits the content change signal after debounce period."""
        if self.pending_content is not None:
            # Only emit if content is still different from what we last knew
            current_content = self.text_edit.toPlainText()
            if current_content == self.pending_content:
                self.tile_content_changed.emit(self.tile_id, self.pending_content)
            self.pending_content = None
            
    def closeEvent(self, event):
        """Ensures pending updates are sent before closing."""
        # Stop the timer and emit any pending changes immediately
        self.update_timer.stop()
        if self.pending_content is not None:
            self._emit_content_change()
        super().closeEvent(event)