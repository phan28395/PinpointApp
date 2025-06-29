# pinpoint/note_editor_widget.py

from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PySide6.QtCore import QTimer


class NoteEditorWidget(QWidget):
    """A dedicated widget for editing a single text note."""
    
    def __init__(self, tile_data: dict, manager, parent=None):
        super().__init__(parent)
        self.tile_id = tile_data['id']
        self.manager = manager
        
        # Flag to prevent circular updates
        self._updating_content = False
        
        # Setup UI
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(tile_data['content'])
        self.text_edit.setStyleSheet("QTextEdit { font-size: 14px; border: none; }")
        layout.addWidget(self.text_edit)
        
        # Debouncing setup
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._save_content)
        self.update_timer.setSingleShot(True)
        self.pending_content = None
        
        # Connect signals
        self.text_edit.textChanged.connect(self.on_text_changed)
        
        # Subscribe to external updates
        self.manager.tile_updated_in_studio.connect(self.on_external_update)
        
    def on_text_changed(self):
        """Handles text changes with debouncing."""
        # Ignore changes if we're updating from external source
        if self._updating_content:
            return
            
        # Store the pending content
        self.pending_content = self.text_edit.toPlainText()
        
        # Restart the timer (debounce)
        self.update_timer.stop()
        self.update_timer.start(300)  # 300ms delay to match NoteTile
        
    def _save_content(self):
        """Saves the content after debounce period."""
        if self.pending_content is not None:
            # Only save if content is still what we intended to save
            current_content = self.text_edit.toPlainText()
            if current_content == self.pending_content:
                self.manager.update_tile_content(
                    self.tile_id, 
                    self.pending_content,
                    source="editor"  # Identify the source
                )
            self.pending_content = None
            
    def on_external_update(self, tile_data: dict):
        """Handles updates from external sources (live tiles or other editors)."""
        # Only process updates for our tile
        if tile_data.get('id') != self.tile_id:
            return
            
        new_content = tile_data.get('content', '')
        
        # Check if we have a pending update with this content
        if self.pending_content == new_content:
            return
            
        current_content = self.text_edit.toPlainText()
        
        # Only update if content is different
        if current_content != new_content:
            # Set flag to prevent circular updates
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
            
            # Clear the flag
            self._updating_content = False
            
    def showEvent(self, event):
        """Called when the widget becomes visible."""
        super().showEvent(event)
        # Refresh content when showing in case it changed while hidden
        tile_data = self.manager.get_tile_by_id(self.tile_id)
        if tile_data:
            self.on_external_update(tile_data)
            
    def hideEvent(self, event):
        """Called when the widget becomes hidden."""
        super().hideEvent(event)
        # Save any pending changes immediately when hiding
        self.update_timer.stop()
        if self.pending_content is not None:
            self._save_content()
            
    def closeEvent(self, event):
        """Ensures pending updates are saved and cleanup is done."""
        # Save pending changes
        self.update_timer.stop()
        if self.pending_content is not None:
            self._save_content()
            
        # Disconnect from manager signals to prevent memory leaks
        try:
            self.manager.tile_updated_in_studio.disconnect(self.on_external_update)
        except:
            pass
            
        super().closeEvent(event)