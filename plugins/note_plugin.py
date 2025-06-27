# pinpoint/plugins/note_plugin.py

from typing import Type, Dict, Any
from .plugin_registry import TilePlugin, TileMetadata, TileCapabilities
from ..note_tile import NoteTile
from ..note_editor_widget import NoteEditorWidget
from PySide6.QtCore import Qt, QTimer

class NotePlugin(TilePlugin):
    """Plugin for text note tiles."""
    
    @classmethod
    def get_metadata(cls) -> TileMetadata:
        """Return metadata about the note tile type."""
        return TileMetadata(
            tile_id="note",
            name="Text Note",
            description="A simple text note that can be edited and styled",
            author="PinPoint Team",
            version="1.0.0",
            icon="📝",
            category="Productivity",
            capabilities=[
                TileCapabilities.CAN_EDIT,
                TileCapabilities.HAS_SETTINGS,
                TileCapabilities.SUPPORTS_THEMES,
                TileCapabilities.CAN_EXPORT
            ],
            config_schema={
                "content": {
                    "type": "string",
                    "default": "New Note",
                    "description": "The text content of the note"
                },
                "font_size": {
                    "type": "number",
                    "default": 14,
                    "min": 8,
                    "max": 32,
                    "description": "Font size in pixels"
                },
                "font_family": {
                    "type": "string",
                    "default": "Arial",
                    "enum": ["Arial", "Times New Roman", "Courier New", "Helvetica", "Georgia"],
                    "description": "Font family for the text"
                },
                "text_color": {
                    "type": "string",
                    "default": "#eeeeee",
                    "format": "color",
                    "description": "Text color in hex format"
                },
                "background_color": {
                    "type": "string",
                    "default": "rgba(40, 40, 40, 0.9)",
                    "format": "color",
                    "description": "Background color"
                },
                "text_align": {
                    "type": "string",
                    "default": "left",
                    "enum": ["left", "center", "right", "justify"],
                    "description": "Text alignment"
                },
                "word_wrap": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable word wrapping"
                },
                "show_scrollbar": {
                    "type": "string",
                    "default": "auto",
                    "enum": ["always", "never", "auto"],
                    "description": "Scrollbar visibility"
                },
                "padding": {
                    "type": "number",
                    "default": 10,
                    "min": 0,
                    "max": 50,
                    "description": "Internal padding in pixels"
                },
                "theme": {
                    "type": "string",
                    "default": "default",
                    "enum": ["default", "dark", "light", "solarized", "monokai", "ocean"],
                    "description": "Color theme preset"
                }
            }
        )
    
    @classmethod
    def get_tile_class(cls) -> Type[NoteTile]:
        """Return the tile widget class."""
        # We need to create an enhanced version of NoteTile that uses config
        return ConfigurableNoteTile
    
    @classmethod
    def get_editor_class(cls):
        """Return the editor widget class."""
        # We'll create an enhanced editor that includes settings
        return ConfigurableNoteEditor
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Return default configuration for new note tiles."""
        return {
            "type": "note",  # Important: keep the type field
            "width": 250,
            "height": 150,
            "content": "New Note",
            "font_size": 14,
            "font_family": "Arial",
            "text_color": "#eeeeee",
            "background_color": "rgba(40, 40, 40, 0.9)",
            "text_align": "left",
            "word_wrap": True,
            "show_scrollbar": "auto",
            "padding": 10,
            "theme": "default"
        }
    
    @classmethod
    def get_theme_presets(cls) -> Dict[str, Dict[str, str]]:
        """Get available theme presets."""
        return {
            "default": {
                "text_color": "#eeeeee",
                "background_color": "rgba(40, 40, 40, 0.9)"
            },
            "dark": {
                "text_color": "#ffffff",
                "background_color": "rgba(20, 20, 20, 0.95)"
            },
            "light": {
                "text_color": "#333333",
                "background_color": "rgba(250, 250, 250, 0.95)"
            },
            "solarized": {
                "text_color": "#839496",
                "background_color": "rgba(0, 43, 54, 0.9)"
            },
            "monokai": {
                "text_color": "#f8f8f2",
                "background_color": "rgba(39, 40, 34, 0.9)"
            },
            "ocean": {
                "text_color": "#c0c5ce",
                "background_color": "rgba(43, 48, 59, 0.9)"
            }
        }


# Enhanced versions of the tile and editor that use the configuration

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QCheckBox, QLabel, QColorDialog, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from ..note_tile import NoteTile
from ..note_editor_widget import NoteEditorWidget


class ConfigurableNoteTile(NoteTile):
    """Enhanced note tile that applies configuration."""
    
    def __init__(self, tile_data: dict):
        super().__init__(tile_data)
        self._apply_configuration()
        
    def _apply_configuration(self):
        """Apply the configuration to the text editor."""
        config = self.tile_data
        
        # Font settings
        font = QFont(
            config.get("font_family", "Arial"),
            config.get("font_size", 14)
        )
        self.text_edit.setFont(font)
        
        # Text alignment
        alignment_map = {
            "left": Qt.AlignmentFlag.AlignLeft,
            "center": Qt.AlignmentFlag.AlignCenter,
            "right": Qt.AlignmentFlag.AlignRight,
            "justify": Qt.AlignmentFlag.AlignJustify
        }
        alignment = alignment_map.get(config.get("text_align", "left"), Qt.AlignmentFlag.AlignLeft)
        self.text_edit.setAlignment(alignment)
        
        # Word wrap
        if config.get("word_wrap", True):
            self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Scrollbar
        scrollbar_map = {
            "always": Qt.ScrollBarPolicy.ScrollBarAlwaysOn,
            "never": Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            "auto": Qt.ScrollBarPolicy.ScrollBarAsNeeded
        }
        scrollbar_policy = scrollbar_map.get(config.get("show_scrollbar", "auto"), Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setVerticalScrollBarPolicy(scrollbar_policy)
        
        # Apply theme or custom colors
        theme_name = config.get("theme", "default")
        if theme_name != "custom":
            themes = NotePlugin.get_theme_presets()
            if theme_name in themes:
                theme = themes[theme_name]
                text_color = theme["text_color"]
                bg_color = theme["background_color"]
            else:
                text_color = config.get("text_color", "#eeeeee")
                bg_color = config.get("background_color", "rgba(40, 40, 40, 0.9)")
        else:
            text_color = config.get("text_color", "#eeeeee")
            bg_color = config.get("background_color", "rgba(40, 40, 40, 0.9)")
        
        # Apply styling
        padding = config.get("padding", 10)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {text_color};
                border: none;
                padding: {padding}px;
            }}
            QScrollBar:vertical {{
                background: rgba(0, 0, 0, 0.1);
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
        """)
        
        # Update container background
        self.container.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border-radius: 8px; }}")
    
    def update_display_content(self, tile_data: dict):
        """Override to also update configuration."""
        if self.tile_id == tile_data.get('id'):
            # Update our data
            self.tile_data.update(tile_data)
            # Reapply configuration
            self._apply_configuration()
        # Call parent to handle content update
        super().update_display_content(tile_data)


class ConfigurableNoteEditor(NoteEditorWidget):
    """Enhanced editor with configuration panel."""
    
    def __init__(self, tile_data: dict, manager, parent=None):
        # Don't call super().__init__ yet, we'll do our own setup
        QWidget.__init__(self, parent)
        self.tile_id = tile_data['id']
        self.tile_data = tile_data.copy()
        self.manager = manager
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Settings panel
        self.settings_panel = self._create_settings_panel()
        self.settings_panel.setVisible(False)
        main_layout.addWidget(self.settings_panel)
        
        # Toggle button for settings
        self.toggle_settings_btn = QPushButton("⚙️ Settings")
        self.toggle_settings_btn.setCheckable(True)
        self.toggle_settings_btn.toggled.connect(self.settings_panel.setVisible)
        self.toggle_settings_btn.setMaximumHeight(30)
        main_layout.addWidget(self.toggle_settings_btn)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(tile_data.get('content', ''))
        main_layout.addWidget(self.text_edit)
        
        # Apply current configuration
        self._apply_configuration()
        
        # Setup the rest like parent class
        self._updating_content = False
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._save_content)
        self.update_timer.setSingleShot(True)
        self.pending_content = None
        
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.manager.tile_updated_in_studio.connect(self.on_external_update)
        
    def _create_settings_panel(self):
        """Create the settings panel."""
        panel = QWidget()
        panel.setStyleSheet("QWidget { background-color: #3a3a3a; padding: 10px; }")
        layout = QVBoxLayout(panel)
        
        # Theme selector
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        themes = ["default", "dark", "light", "solarized", "monokai", "ocean", "custom"]
        self.theme_combo.addItems(themes)
        self.theme_combo.setCurrentText(self.tile_data.get("theme", "default"))
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Font settings
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "Courier New", "Helvetica", "Georgia"])
        self.font_combo.setCurrentText(self.tile_data.get("font_family", "Arial"))
        self.font_combo.currentTextChanged.connect(self._on_setting_changed)
        font_layout.addWidget(self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setValue(self.tile_data.get("font_size", 14))
        self.font_size_spin.valueChanged.connect(self._on_setting_changed)
        font_layout.addWidget(self.font_size_spin)
        font_layout.addWidget(QLabel("px"))
        
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        # Text alignment
        align_layout = QHBoxLayout()
        align_layout.addWidget(QLabel("Align:"))
        self.align_combo = QComboBox()
        self.align_combo.addItems(["left", "center", "right", "justify"])
        self.align_combo.setCurrentText(self.tile_data.get("text_align", "left"))
        self.align_combo.currentTextChanged.connect(self._on_setting_changed)
        align_layout.addWidget(self.align_combo)
        align_layout.addStretch()
        layout.addLayout(align_layout)
        
        # Options
        self.word_wrap_check = QCheckBox("Word Wrap")
        self.word_wrap_check.setChecked(self.tile_data.get("word_wrap", True))
        self.word_wrap_check.stateChanged.connect(self._on_setting_changed)
        layout.addWidget(self.word_wrap_check)
        
        return panel
        
    def _apply_configuration(self):
        """Apply configuration to the editor."""
        # Similar to ConfigurableNoteTile._apply_configuration
        # but applied to the editor's text widget
        config = self.tile_data
        
        font = QFont(
            config.get("font_family", "Arial"),
            config.get("font_size", 14)
        )
        self.text_edit.setFont(font)
        
        # Apply theme colors to editor
        theme_name = config.get("theme", "default")
        if theme_name != "custom":
            themes = NotePlugin.get_theme_presets()
            if theme_name in themes:
                theme = themes[theme_name]
                text_color = theme["text_color"]
                bg_color = theme["background_color"]
            else:
                text_color = config.get("text_color", "#333")
                bg_color = "white"
        else:
            text_color = config.get("text_color", "#333")
            bg_color = "white"
            
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{ 
                font-size: {config.get('font_size', 14)}px; 
                border: none; 
                color: {text_color};
                background-color: {bg_color};
            }}
        """)
        
    def _on_theme_changed(self, theme_name):
        """Handle theme change."""
        self.tile_data["theme"] = theme_name
        if theme_name != "custom":
            # Apply preset colors
            themes = NotePlugin.get_theme_presets()
            if theme_name in themes:
                theme = themes[theme_name]
                self.tile_data["text_color"] = theme["text_color"]
                self.tile_data["background_color"] = theme["background_color"]
        self._apply_configuration()
        self._save_config()
        
    def _on_setting_changed(self):
        """Handle setting changes."""
        self.tile_data["font_family"] = self.font_combo.currentText()
        self.tile_data["font_size"] = self.font_size_spin.value()
        self.tile_data["text_align"] = self.align_combo.currentText()
        self.tile_data["word_wrap"] = self.word_wrap_check.isChecked()
        self._apply_configuration()
        self._save_config()
        
    def _save_config(self):
        """Save configuration changes."""
        # Update the tile through the manager
        # This will trigger updates to all views
        self.manager.update_tile_config(self.tile_id, self.tile_data)
        
    # Keep all the parent class methods for text handling
    from PySide6.QtCore import QTimer
    
    def on_text_changed(self):
        if self._updating_content:
            return
        self.pending_content = self.text_edit.toPlainText()
        self.update_timer.stop()
        self.update_timer.start(300)
        
    def _save_content(self):
        if self.pending_content is not None:
            self.tile_data["content"] = self.pending_content
            self.manager.update_tile_content(self.tile_id, self.pending_content, source="editor")
            self.pending_content = None