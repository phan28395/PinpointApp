# pinpoint/plugins/note_plugin.py - Refactored to support external designs

from typing import Type, Dict, Any, List
from .plugin_registry import TilePlugin, TileMetadata, TileCapabilities, DesignConstraints
from ..note_tile import NoteTile, NoteTileLogic
from ..note_editor_widget import NoteEditorWidget
from ..design_system import ComponentType


class NotePlugin(TilePlugin):
    """
    Plugin for text note tiles.
    Now focuses on functionality while allowing external visual designs.
    """
    
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
                TileCapabilities.CAN_EXPORT,
                TileCapabilities.SUPPORTS_CUSTOM_DESIGN  # New capability
            ],
            config_schema={
                "content": {
                    "type": "string",
                    "default": "",
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
                    "default": "default",
                    "enum": ["default", "mono"],
                    "description": "Font family preset"
                },
                "word_wrap": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable word wrapping"
                },
                "show_line_numbers": {
                    "type": "boolean",
                    "default": False,
                    "description": "Show line numbers (for code notes)"
                },
                "syntax_highlighting": {
                    "type": "string",
                    "default": "none",
                    "enum": ["none", "python", "javascript", "markdown", "json"],
                    "description": "Syntax highlighting mode"
                }
            },
            design_constraints=DesignConstraints(
                min_width=150,
                max_width=800,
                min_height=100,
                max_height=1000,
                allowed_components=[
                    ComponentType.TEXT_EDIT,
                    ComponentType.LABEL,
                    ComponentType.BUTTON,
                    ComponentType.CONTAINER,
                    ComponentType.SPACER
                ],
                required_components=['noteTextEdit']  # Must have a text edit with this ID
            ),
            default_design="note_default"  # Name of the default design
        )
    
    @classmethod
    def get_tile_class(cls) -> Type[NoteTile]:
        """Return the tile widget class."""
        return NoteTile
    
    @classmethod
    def get_logic_class(cls) -> Type[NoteTileLogic]:
        """Return the tile logic class for separation of concerns."""
        return NoteTileLogic
    
    @classmethod
    def get_editor_class(cls):
        """Return the editor widget class."""
        return EnhancedNoteEditor
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Return default configuration for new note tiles."""
        return {
            "type": "note",
            "width": 250,
            "height": 150,
            "content": "",
            "font_size": 14,
            "font_family": "default",
            "word_wrap": True,
            "show_line_numbers": False,
            "syntax_highlighting": "none"
        }
    
    @classmethod
    def get_builtin_designs(cls) -> List[Dict[str, Any]]:
        """
        Return built-in design specifications for note tiles.
        These are the designs that ship with the plugin.
        """
        return [
            {
                "metadata": {
                    "id": "note_default",
                    "name": "Default Note",
                    "author": "PinPoint Team",
                    "version": "1.0.0",
                    "compatible_with": "1.0.0",
                    "description": "Clean, simple note design"
                },
                "layout": {
                    "type": "vertical",
                    "spacing": "none",
                    "components": [
                        {
                            "type": "text_edit",
                            "id": "noteTextEdit",
                            "style": "primary"
                        }
                    ]
                },
                "styling": {
                    "theme": "default"
                }
            },
            {
                "metadata": {
                    "id": "note_with_header",
                    "name": "Note with Header",
                    "author": "PinPoint Team",
                    "version": "1.0.0",
                    "compatible_with": "1.0.0",
                    "description": "Note with title bar and word count"
                },
                "layout": {
                    "type": "vertical",
                    "spacing": "none",
                    "components": [
                        {
                            "type": "container",
                            "id": "headerContainer",
                            "style": "secondary",
                            "components": [
                                {
                                    "type": "label",
                                    "id": "titleLabel",
                                    "text": "Note",
                                    "style": "muted",
                                    "size": "sm"
                                },
                                {
                                    "type": "spacer"
                                },
                                {
                                    "type": "label",
                                    "id": "wordCountLabel",
                                    "text": "0 words",
                                    "style": "muted",
                                    "size": "xs"
                                }
                            ]
                        },
                        {
                            "type": "text_edit",
                            "id": "noteTextEdit",
                            "style": "primary"
                        }
                    ]
                },
                "styling": {
                    "theme": "default",
                    "custom_styles": {
                        "headerContainer": {
                            "layout": "horizontal",
                            "padding": "xs",
                            "border_bottom": "subtle"
                        }
                    }
                }
            },
            {
                "metadata": {
                    "id": "note_minimal",
                    "name": "Minimal Note",
                    "author": "PinPoint Team",
                    "version": "1.0.0",
                    "compatible_with": "1.0.0",
                    "description": "Borderless, transparent note"
                },
                "layout": {
                    "type": "vertical",
                    "spacing": "none",
                    "components": [
                        {
                            "type": "text_edit",
                            "id": "noteTextEdit",
                            "style": "transparent"
                        }
                    ]
                },
                "styling": {
                    "theme": "minimal",
                    "transparent_background": true
                }
            }
        ]
    
    @classmethod
    def get_available_actions(cls) -> Dict[str, str]:
        """
        Define actions that designs can trigger.
        This creates a contract between designs and logic.
        """
        return {
            "clear": "Clear all text",
            "copy": "Copy selected text",
            "paste": "Paste from clipboard",
            "select_all": "Select all text",
            "undo": "Undo last change",
            "redo": "Redo last change",
            "toggle_wrap": "Toggle word wrap",
            "increase_font": "Increase font size",
            "decrease_font": "Decrease font size",
            "export": "Export note content"
        }
    
    @classmethod
    def get_data_bindings(cls) -> Dict[str, str]:
        """
        Define data that the logic provides to designs.
        Designs can bind components to these data points.
        """
        return {
            "content": "The note text content",
            "word_count": "Current word count",
            "char_count": "Current character count",
            "line_count": "Current line count",
            "modified": "Whether content has been modified",
            "last_saved": "Last save timestamp",
            "font_size": "Current font size"
        }


# Enhanced Note Editor that works with the design system
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QComboBox, QSpinBox, QCheckBox, QLabel)
from PySide6.QtCore import Qt
from ..design_system import DesignSystem, spacing, color


class EnhancedNoteEditor(QWidget):
    """
    Enhanced editor for note tiles that uses the design system.
    This editor allows configuration but respects design constraints.
    """
    
    def __init__(self, tile_data: dict, manager, parent=None):
        super().__init__(parent)
        self.tile_data = tile_data.copy()
        self.tile_id = tile_data['id']
        self.manager = manager
        
        # Create UI using design system
        self._create_ui()
        
        # Load tile content
        self._load_content()
        
    def _create_ui(self):
        """Create the editor UI using the design system."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with settings
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {color('bg_secondary')};
                border-bottom: 1px solid {color('border_subtle')};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(spacing('sm'), spacing('sm'), spacing('sm'), spacing('sm'))
        
        # Settings toggle
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setCheckable(True)
        self.settings_btn.setStyleSheet(DesignSystem.get_button_style('secondary', 'sm'))
        self.settings_btn.toggled.connect(self._toggle_settings)
        header_layout.addWidget(self.settings_btn)
        
        header_layout.addStretch()
        
        # Design selector
        header_layout.addWidget(QLabel("Design:"))
        self.design_combo = QComboBox()
        self.design_combo.setStyleSheet(DesignSystem.get_style('combo_box', 'primary'))
        self._populate_designs()
        self.design_combo.currentTextChanged.connect(self._on_design_changed)
        header_layout.addWidget(self.design_combo)
        
        layout.addWidget(header)
        
        # Settings panel (hidden by default)
        self.settings_panel = self._create_settings_panel()
        self.settings_panel.setVisible(False)
        layout.addWidget(self.settings_panel)
        
        # Main editor
        from ..note_editor_widget import NoteEditorWidget
        self.editor = NoteEditorWidget(self.tile_data, self.manager)
        self.editor.setStyleSheet(f"background-color: {color('bg_primary')};")
        layout.addWidget(self.editor, 1)
        
    def _create_settings_panel(self):
        """Create the settings panel."""
        panel = QWidget()
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {color('bg_tertiary')};
                border-bottom: 1px solid {color('border_subtle')};
                padding: {spacing('sm')}px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(spacing('sm'))
        
        # Font settings
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Default", "Monospace"])
        self.font_combo.setCurrentText(
            "Monospace" if self.tile_data.get("font_family") == "mono" else "Default"
        )
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
        
        # Options
        options_layout = QHBoxLayout()
        
        self.word_wrap_check = QCheckBox("Word Wrap")
        self.word_wrap_check.setChecked(self.tile_data.get("word_wrap", True))
        self.word_wrap_check.stateChanged.connect(self._on_setting_changed)
        options_layout.addWidget(self.word_wrap_check)
        
        self.line_numbers_check = QCheckBox("Line Numbers")
        self.line_numbers_check.setChecked(self.tile_data.get("show_line_numbers", False))
        self.line_numbers_check.stateChanged.connect(self._on_setting_changed)
        options_layout.addWidget(self.line_numbers_check)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Syntax highlighting
        syntax_layout = QHBoxLayout()
        syntax_layout.addWidget(QLabel("Syntax:"))
        
        self.syntax_combo = QComboBox()
        self.syntax_combo.addItems(["None", "Python", "JavaScript", "Markdown", "JSON"])
        self.syntax_combo.setCurrentText(
            self.tile_data.get("syntax_highlighting", "none").title()
        )
        self.syntax_combo.currentTextChanged.connect(self._on_setting_changed)
        syntax_layout.addWidget(self.syntax_combo)
        
        syntax_layout.addStretch()
        layout.addLayout(syntax_layout)
        
        return panel
        
    def _populate_designs(self):
        """Populate the design combo box."""
        registry = self.manager.registry
        designs = registry.get_designs_for_tile("note")
        
        current_design = self.tile_data.get("design_id", "note_default")
        
        for design in designs:
            self.design_combo.addItem(design.name, design.design_id)
            
        # Set current design
        index = self.design_combo.findData(current_design)
        if index >= 0:
            self.design_combo.setCurrentIndex(index)
            
    def _toggle_settings(self, checked):
        """Toggle settings panel visibility."""
        self.settings_panel.setVisible(checked)
        
    def _on_setting_changed(self):
        """Handle setting changes."""
        # Update tile data
        self.tile_data["font_family"] = "mono" if self.font_combo.currentText() == "Monospace" else "default"
        self.tile_data["font_size"] = self.font_size_spin.value()
        self.tile_data["word_wrap"] = self.word_wrap_check.isChecked()
        self.tile_data["show_line_numbers"] = self.line_numbers_check.isChecked()
        self.tile_data["syntax_highlighting"] = self.syntax_combo.currentText().lower()
        
        # Save configuration
        self._save_config()
        
    def _on_design_changed(self):
        """Handle design change."""
        design_id = self.design_combo.currentData()
        if design_id:
            self.tile_data["design_id"] = design_id
            self._save_config()
            
            # Notify that design should be updated
            # In a real implementation, this would trigger a tile refresh
            
    def _save_config(self):
        """Save configuration changes."""
        self.manager.update_tile_config(self.tile_id, self.tile_data)
        
    def _load_content(self):
        """Load tile content into editor."""
        # Content is handled by the embedded NoteEditorWidget
        pass