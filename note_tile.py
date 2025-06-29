# pinpoint/note_tile.py - Refactored to separate logic from design

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
    """
    
    def __init__(self, tile_data: Dict[str, Any]):
        # Debug print
        print(f"NoteTile.__init__ called with tile_data keys: {tile_data.keys()}")
        print(f"Content in tile_data: '{tile_data.get('content', '')}'")
        
        # Initialize logic component
        tile_id = tile_data.get("id", "unknown")
        content = tile_data.get("content", "")
        
        print(f"Creating NoteTileLogic with tile_id='{tile_id}', content='{content}'")
        self.logic = NoteTileLogic(tile_id, content)
        
        # Set up logic callback
        self.logic.set_update_callback(self._on_content_change)
        
        # Store reference to main text widget
        self.text_edit: Optional[QTextEdit] = None
        
        # IMPORTANT: Remove design_spec to force embedded design
        # This ensures the text widget is created properly
        tile_data_copy = tile_data.copy()
        if 'design_spec' in tile_data_copy:
            print("Removing design_spec to force embedded design")
            del tile_data_copy['design_spec']
        
        # Initialize base tile WITHOUT design spec
        super().__init__(tile_data_copy)
        
        # Always create default embedded design
        print("Creating default embedded design")
        self._create_default_design()
        
        # Connect the text widget to logic
        self._connect_text_widget()
        
        # Debug: Check if text_edit was created and has content
        if self.text_edit:
            print(f"text_edit created successfully, current text: '{self.text_edit.toPlainText()}'")
        else:
            print("ERROR: text_edit was not created!")

    def _create_default_design(self):
        """Creates the default note tile design (embedded approach)."""
        print("_create_default_design called")
        
        # Create text edit widget
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("noteTextEdit")
        
        # Set the content from logic IMMEDIATELY
        content = self.logic.get_content()
        print(f"Setting initial content in text_edit: '{content}'")
        self.text_edit.setPlainText(content)
        
        # Apply design system styling
        self.text_edit.setStyleSheet(DesignSystem.get_text_edit_style())
        
        # Add to content area
        if hasattr(self, 'content_layout') and self.content_layout:
            self.content_layout.addWidget(self.text_edit)
            print("text_edit added to content_layout successfully")
        else:
            print("ERROR: content_layout not found!")

    def _connect_text_widget(self):
        """Connect text widget to logic."""
        print("_connect_text_widget called")
        
        if self.text_edit:
            # Connect change signal
            self.text_edit.textChanged.connect(self._on_text_changed)
            print("Connected textChanged signal")
        else:
            print("ERROR: text_edit is None in _connect_text_widget!")

    def _on_text_changed(self):
        """Handle text changes from UI."""
        if self.text_edit and not self.logic.is_updating:
            new_text = self.text_edit.toPlainText()
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
            if self.text_edit:
                # Store cursor position
                cursor = self.text_edit.textCursor()
                cursor_position = cursor.position()
                
                # Update text
                self.text_edit.setPlainText(new_content)
                
                # Restore cursor position
                if cursor_position <= len(new_content):
                    cursor.setPosition(cursor_position)
                    self.text_edit.setTextCursor(cursor)

    def handle_action(self, action: str):
        """Handle actions from design spec components."""
        if action == "clear":
            if self.text_edit:
                self.text_edit.clear()
        elif action == "copy":
            if self.text_edit:
                self.text_edit.copy()
        elif action == "paste":
            if self.text_edit:
                self.text_edit.paste()

    def closeEvent(self, event):
        """Ensure pending updates are sent before closing."""
        # Stop the timer and emit any pending changes
        self.logic.debounce_timer.stop()
        self.logic._emit_content_change()
        super().closeEvent(event)