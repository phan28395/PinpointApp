# pinpoint/note_tile.py - Fully separated logic from UI

from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import QTimer
from typing import Dict, Any, Optional
from .base_tile import BaseTile
from .design_system import DesignSystem


class NoteTileLogic:
    """
    Pure logic for note tile functionality.
    This class handles all the business logic without any UI dependencies.
    """
    
    def __init__(self, tile_id: str, initial_content: str = ""):
        self.tile_id = tile_id
        self.content = initial_content
        self.pending_content = None
        self.update_callback = None
        self.is_updating = False
        
        # Debouncing timer
        self.debounce_timer = QTimer()
        self.debounce_timer.timeout.connect(self._emit_content_change)
        self.debounce_timer.setSingleShot(True)
        
    def set_update_callback(self, callback):
        """Set the callback for content updates."""
        self.update_callback = callback
        
    def handle_text_change(self, new_text: str):
        """Handle text changes with debouncing."""
        if self.is_updating:
            return
            
        self.pending_content = new_text
        self.debounce_timer.stop()
        self.debounce_timer.start(300)  # 300ms delay
        
    def update_content_external(self, new_content: str):
        """Update content from external source (e.g., sync from studio)."""
        if self.pending_content == new_content:
            return
            
        if self.content != new_content:
            self.is_updating = True
            self.content = new_content
            self.is_updating = False
            return True  # Content was updated
        return False  # No update needed
        
    def _emit_content_change(self):
        """Emit content change after debounce period."""
        if self.pending_content is not None and self.update_callback:
            if self.content != self.pending_content:
                self.content = self.pending_content
                self.update_callback(self.tile_id, self.content)
            self.pending_content = None
            
    def get_content(self) -> str:
        """Get current content."""
        return self.content


class NoteTile(BaseTile):
    """
    Note tile implementation using the new architecture.
    All UI is now handled by the design system.
    """
    
    def __init__(self, tile_data: Dict[str, Any]):
        # Initialize logic component
        tile_id = tile_data.get("id", "unknown")
        content = tile_data.get("content", "")
        
        self.logic = NoteTileLogic(tile_id, content)
        # Initialize base tile - let it handle all UI creation
        super().__init__(tile_data)
        self.logic.set_update_callback(self._on_content_change)
        
        # Store reference to text widget for efficient access
        self._text_widget = None
        

        
        # After UI is created by base class, connect to the text widget if it exists
        self._connect_to_text_widget()
        
    def _connect_to_text_widget(self):
        """Connect to the text widget created by the design system."""
        # Find the text edit widget created by the design
        text_widget = self.get_component("noteTextEdit")
        
        if text_widget and isinstance(text_widget, QTextEdit):
            # Set initial content
            text_widget.setPlainText(self.logic.get_content())
            
            # Connect change signal
            text_widget.textChanged.connect(self._on_text_changed)
            
            # Store reference for updates
            self._text_widget = text_widget
        else:
            print(f"Warning: No text edit widget found with id 'noteTextEdit'")
            self._text_widget = None
    
    def _on_text_changed(self):
        """Handle text changes from UI."""
        if self._text_widget and not self.logic.is_updating:
            new_text = self._text_widget.toPlainText()
            self.logic.handle_text_change(new_text)
    
    def _on_content_change(self, tile_id: str, content: str):
        """Handle content changes from logic."""
        self.tile_content_changed.emit(tile_id, content)
    
    def update_display_content(self, tile_data: Dict[str, Any]):
        """Update content from external source (e.g., studio sync)."""
        if self.tile_id != tile_data.get('id'):
            return
            
        new_content = tile_data.get('content', '')
        
        # Update logic
        if self.logic.update_content_external(new_content):
            # Update UI if content changed
            if self._text_widget:
                # Store cursor position
                cursor = self._text_widget.textCursor()
                cursor_position = cursor.position()
                
                # Update text
                self._text_widget.setPlainText(new_content)
                
                # Restore cursor position
                if cursor_position <= len(new_content):
                    cursor.setPosition(cursor_position)
                    self._text_widget.setTextCursor(cursor)
    
    def handle_action(self, action: str):
        """Handle actions from design spec components."""
        if action == "clear":
            if self._text_widget:
                self._text_widget.clear()
        elif action == "copy":
            if self._text_widget:
                self._text_widget.copy()
        elif action == "paste":
            if self._text_widget:
                self._text_widget.paste()
        elif action == "select_all":
            if self._text_widget:
                self._text_widget.selectAll()
        elif action == "undo":
            if self._text_widget:
                self._text_widget.undo()
        elif action == "redo":
            if self._text_widget:
                self._text_widget.redo()
    
    def update_component_data(self, component_id: str, data: Any):
        """Update data for specific components (for designs with multiple components)."""
        if component_id == "wordCountLabel":
            # Calculate word count
            word_count = len(self.logic.get_content().split())
            super().update_component_data(component_id, f"{word_count} words")
        else:
            super().update_component_data(component_id, data)
    
    def closeEvent(self, event):
        """Ensure pending updates are sent before closing."""
        # Stop the timer and emit any pending changes
        self.logic.debounce_timer.stop()
        self.logic._emit_content_change()
        super().closeEvent(event)