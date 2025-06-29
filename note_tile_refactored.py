# pinpoint/note_tile_refactored.py
"""
Refactored note tile with complete separation of functionality and design.
This file contains ONLY the text editing logic, no visual styling.
"""

from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import QTimer
from typing import Dict, Any

from .base_tile_refactored import BaseTile
from .design_layer import DesignLayer


class NoteTile(BaseTile):
    """
    Note tile implementation with pure functionality.
    All visual aspects are handled by the design layer.
    """
    
    def __init__(self, tile_data: Dict[str, Any], design_layer: DesignLayer):
        # Initialize base tile
        super().__init__(tile_data, design_layer)
    
    def setup_content(self):
        """Set up the note-specific content."""
        # Create text editor (no styling)
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("note_text_editor")
        
        # Set initial content
        self.text_edit.setPlainText(self.tile_data.get("content", ""))
        
        # Configure functional properties
        self.text_edit.setAcceptRichText(False)  # Plain text only
        word_wrap = self.tile_data.get("word_wrap", True)
        self.text_edit.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth if word_wrap else QTextEdit.LineWrapMode.NoWrap
        )
        
        # Add to content area
        self.content_layout.addWidget(self.text_edit)
        
        # Set up debouncing for content changes
        self.content_timer = QTimer()
        self.content_timer.timeout.connect(self._save_content)
        self.content_timer.setSingleShot(True)
        self.pending_content = None
        
        # Flag to prevent circular updates
        self._updating_content = False
        
        # Connect signals
        self.text_edit.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self):
        """Handle text changes with debouncing."""
        if self._updating_content:
            return
        
        # Store pending content
        self.pending_content = self.text_edit.toPlainText()
        
        # Restart timer (debounce)
        self.content_timer.stop()
        self.content_timer.start(300)  # 300ms delay
    
    def _save_content(self):
        """Save content after debounce period."""
        if self.pending_content is not None:
            current_content = self.text_edit.toPlainText()
            if current_content == self.pending_content:
                # Emit content change signal
                self.tile_content_changed.emit(self.tile_id, self.pending_content)
            self.pending_content = None
    
    def update_display_content(self, tile_data: Dict[str, Any]):
        """Update content from external source (e.g., studio sync)."""
        if self.tile_id != tile_data.get('id'):
            return
        
        new_content = tile_data.get('content', '')
        
        # Check if we have a pending update with this content
        if self.pending_content == new_content:
            return
        
        current_content = self.text_edit.toPlainText()
        
        # Only update if content is different
        if current_content != new_content:
            self._updating_content = True
            
            # Store cursor position
            cursor = self.text_edit.textCursor()
            cursor_position = cursor.position()
            
            # Store selection if any
            has_selection = cursor.hasSelection()
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()
            
            # Update content
            self.text_edit.setPlainText(new_content)
            
            # Restore cursor position and selection
            if cursor_position <= len(new_content):
                cursor.setPosition(cursor_position)
                
                # Restore selection if it's still valid
                if has_selection and selection_end <= len(new_content):
                    cursor.setPosition(selection_start)
                    cursor.setPosition(selection_end, cursor.KeepAnchor)
                
                self.text_edit.setTextCursor(cursor)
            
            self._updating_content = False
    
    def update_display_config(self, tile_data: Dict[str, Any]):
        """Update configuration settings."""
        super().update_display_config(tile_data)
        
        # Update word wrap if changed
        if 'word_wrap' in tile_data:
            word_wrap = tile_data['word_wrap']
            self.text_edit.setLineWrapMode(
                QTextEdit.LineWrapMode.WidgetWidth if word_wrap else QTextEdit.LineWrapMode.NoWrap
            )
    
    def closeEvent(self, event):
        """Ensure pending updates are sent before closing."""
        # Stop timer and emit any pending changes
        self.content_timer.stop()
        self._save_content()
        
        # Call parent close event
        super().closeEvent(event)