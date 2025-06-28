# pinpoint/main_window.py

import uuid
from PySide6.QtWidgets import (QMainWindow, QLabel, QSplitter, QListWidget, 
                              QListWidgetItem, QTabWidget, QPushButton, 
                              QVBoxLayout, QWidget, QMenu, QStackedWidget,
                              QTreeWidget, QTreeWidgetItem, QHBoxLayout,
                              QDialog, QDialogButtonBox, QTextEdit, QLineEdit,
                              QToolBar, QComboBox, QActionGroup, QButtonGroup,
                              QMessageBox, QInputDialog, QCheckBox)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon
from .layout_editor import LayoutEditor
from .draggable_list_widget import DraggableListWidget
from .display_manager import get_display_manager


class IconButton(QPushButton):
    """Custom button for sidebar navigation."""
    def __init__(self, icon_text, tooltip, parent=None):
        super().__init__(icon_text, parent)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedWidth(60)
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: none;
                color: #888;
                font-size: 24px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #fff;
            }
            QPushButton:checked {
                background-color: #0d7377;
                color: #fff;
                border-left: 3px solid #14ffec;
            }
        """)


class NewTileDialog(QDialog):
    """Dialog for creating a new tile with type selection."""
    
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.selected_type = None
        
        self.setWindowTitle("Create New Tile")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Type selection
        layout.addWidget(QLabel("Select tile type:"))
        
        self.type_tree = QTreeWidget()
        self.type_tree.setHeaderLabel("Available Tile Types")
        self.type_tree.itemClicked.connect(self._on_type_selected)
        
        # Populate tile types by category
        self._populate_tile_types()
        
        layout.addWidget(self.type_tree)
        
        # Description area
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)
        self.description_text.setPlainText("Select a tile type to see its description")
        layout.addWidget(self.description_text)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def _populate_tile_types(self):
        """Populate the tree with available tile types."""
        registry = self.manager.registry
        categories = registry.get_categories()
        
        for category in categories:
            category_item = QTreeWidgetItem([category])
            category_item.setExpanded(True)
            self.type_tree.addTopLevelItem(category_item)
            
            # Add tiles in this category
            for metadata in registry.get_plugins_by_category(category):
                tile_item = QTreeWidgetItem([f"{metadata.icon} {metadata.name}"])
                tile_item.setData(0, Qt.ItemDataRole.UserRole, metadata.tile_id)
                tile_item.setData(0, Qt.ItemDataRole.UserRole + 1, metadata)
                category_item.addChild(tile_item)
                
    def _on_type_selected(self, item, column):
        """Handle tile type selection."""
        metadata = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if metadata:
            self.selected_type = metadata.tile_id
            # Show description
            desc = f"**{metadata.name}** v{metadata.version}\n"
            desc += f"by {metadata.author}\n\n"
            desc += metadata.description
            if metadata.capabilities:
                desc += f"\n\nCapabilities: {', '.join(metadata.capabilities)}"
            self.description_text.setPlainText(desc)


class TileLibraryWidget(QWidget):
    """Enhanced tile library with categorization and folder support."""
    
    tile_selected = Signal(str)  # tile_id
    
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top toolbar for tile operations
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        self.new_folder_btn = QPushButton("📁 New Folder")
        self.new_folder_btn.clicked.connect(self._create_folder)
        toolbar_layout.addWidget(self.new_folder_btn)
        
        self.new_tile_btn = QPushButton("➕ New Tile")
        self.new_tile_btn.clicked.connect(self._create_tile)
        toolbar_layout.addWidget(self.new_tile_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Tree widget for folders and tiles
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)
        
        self.populate_tree()
        
    def populate_tree(self):
        """Populate the tree with folders and tiles."""
        self.tree.clear()
        
        # For now, show all tiles in a flat structure
        # TODO: Implement folder structure in storage
        all_tiles = self.manager.get_all_tile_data()
        
        for tile_data in all_tiles:
            # Get metadata for this tile type
            tile_type = tile_data.get('type', 'note')
            metadata = self.manager.registry.get_metadata(tile_type)
            
            # Create tree item
            content = tile_data.get('content', '')
            item_text = content.split('\n')[0][:30] or "Empty"
            
            if metadata:
                item_text = f"{metadata.icon} {item_text}"
                
            tree_item = QTreeWidgetItem([item_text])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, tile_data['id'])
            tree_item.setData(0, Qt.ItemDataRole.UserRole + 1, "tile")
            tree_item.setData(0, Qt.ItemDataRole.UserRole + 2, tile_type)
            
            # Add tooltip
            if metadata:
                tooltip = f"Type: {metadata.name}\nCategory: {metadata.category}"
                tree_item.setToolTip(0, tooltip)
                
            self.tree.addTopLevelItem(tree_item)
            
    def _create_folder(self):
        """Create a new folder."""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            # TODO: Implement folder creation in storage
            folder_item = QTreeWidgetItem([f"📁 {name}"])
            folder_item.setData(0, Qt.ItemDataRole.UserRole + 1, "folder")
            self.tree.addTopLevelItem(folder_item)
            
    def _create_tile(self):
        """Create a new tile."""
        dialog = NewTileDialog(self.manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_type:
            self.manager.create_new_tile_definition(dialog.selected_type)
            self.populate_tree()
            
    def _on_item_clicked(self, item, column):
        """Handle item selection."""
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type == "tile":
            tile_id = item.data(0, Qt.ItemDataRole.UserRole)
            self.tile_selected.emit(tile_id)
            
    def _show_context_menu(self, position):
        """Show context menu for tiles/folders."""
        item = self.tree.itemAt(position)
        if not item:
            return
            
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        menu = QMenu()
        
        # Standard actions
        duplicate_action = menu.addAction("📋 Duplicate")
        duplicate_action.triggered.connect(lambda: self._duplicate_item(item))
        
        rename_action = menu.addAction("✏️ Rename")
        rename_action.triggered.connect(lambda: self._rename_item(item))
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self._delete_item(item))
        
        menu.addSeparator()
        
        # Private checkbox
        private_action = menu.addAction("🔒 Private")
        private_action.setCheckable(True)
        # TODO: Implement privacy settings
        
        # Type-specific actions
        if item_type == "tile":
            tile_type = item.data(0, Qt.ItemDataRole.UserRole + 2)
            metadata = self.manager.registry.get_metadata(tile_type)
            if metadata and "can_edit" in metadata.capabilities:
                menu.addSeparator()
                edit_action = menu.addAction("📝 Edit")
                edit_action.triggered.connect(lambda: self._edit_tile(item))
                
        menu.exec(self.tree.mapToGlobal(position))
        
    def _duplicate_item(self, item):
        """Duplicate a tile or folder."""
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type == "tile":
            tile_id = item.data(0, Qt.ItemDataRole.UserRole)
            self.manager.duplicate_tile(tile_id)
            self.populate_tree()
            
    def _rename_item(self, item):
        """Rename a tile or folder."""
        old_name = item.text(0)
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and name:
            item.setText(0, name)
            # TODO: Save rename to storage
            
    def _delete_item(self, item):
        """Delete a tile or folder."""
        reply = QMessageBox.question(self, "Delete", 
                                   "Are you sure you want to delete this item?",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if item_type == "tile":
                tile_id = item.data(0, Qt.ItemDataRole.UserRole)
                self.manager.delete_tile(tile_id)
                self.populate_tree()
                
    def _edit_tile(self, item):
        """Edit a tile."""
        tile_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.tile_selected.emit(tile_id)


class MainWindow(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.display_manager = get_display_manager()
        self.editors = {}
        
        self.setWindowTitle("PinPoint Studio")
        self.setMinimumSize(1200, 700)
        
        # Create main layout
        self._create_ui()
        
        # Load initial content
        self._show_editor_panel()
        
    def _create_ui(self):
        """Create the main UI with icon sidebar."""
        # Main widget
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Icon sidebar
        self.icon_sidebar = QWidget()
        self.icon_sidebar.setFixedWidth(60)
        self.icon_sidebar.setStyleSheet("background-color: #1a1a1a;")
        
        icon_layout = QVBoxLayout(self.icon_sidebar)
        icon_layout.setContentsMargins(0, 10, 0, 10)
        icon_layout.setSpacing(5)
        
        # Icon buttons
        self.icon_group = QButtonGroup()
        
        self.editor_btn = IconButton("📝", "Editor")
        self.library_btn = IconButton("📚", "Library")
        self.marketplace_btn = IconButton("🛍️", "Marketplace (Coming Soon)")
        self.account_btn = IconButton("👤", "Account (Coming Soon)")
        self.settings_btn = IconButton("⚙️", "Settings (Coming Soon)")
        
        # Add buttons to group
        self.icon_group.addButton(self.editor_btn, 0)
        self.icon_group.addButton(self.library_btn, 1)
        self.icon_group.addButton(self.marketplace_btn, 2)
        self.icon_group.addButton(self.account_btn, 3)
        self.icon_group.addButton(self.settings_btn, 4)
        
        # Disable future features
        self.marketplace_btn.setEnabled(False)
        self.account_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        
        # Connect signals
        self.icon_group.buttonClicked.connect(self._on_icon_clicked)
        
        # Add to layout
        icon_layout.addWidget(self.editor_btn)
        icon_layout.addWidget(self.library_btn)
        icon_layout.addWidget(self.marketplace_btn)
        icon_layout.addWidget(self.account_btn)
        icon_layout.addWidget(self.settings_btn)
        icon_layout.addStretch()
        
        # Content area
        self.content_stack = QStackedWidget()
        
        # Create panels
        self._create_editor_panel()
        self._create_library_panel()
        
        # Add panels to stack
        self.content_stack.addWidget(self.editor_panel)
        self.content_stack.addWidget(self.library_panel)
        
        # Main splitter (sidebar content | main content)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.content_stack)
        content_layout.addWidget(self.central_stack)
        
        # Add to main layout
        main_layout.addWidget(self.icon_sidebar)
        main_layout.addLayout(content_layout)
        
        self.setCentralWidget(main_widget)
        
        # Set default selection
        self.editor_btn.setChecked(True)
        
    def _create_editor_panel(self):
        """Create the editor panel (layouts and tiles)."""
        self.editor_panel = QWidget()
        layout = QVBoxLayout(self.editor_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for layouts and tiles
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Layouts section
        layouts_widget = QWidget()
        layouts_layout = QVBoxLayout(layouts_widget)
        layouts_layout.setContentsMargins(5, 5, 5, 5)
        
        # Layout controls
        layout_toolbar = QHBoxLayout()
        layout_toolbar.addWidget(QLabel("Layouts"))
        layout_toolbar.addStretch()
        
        self.new_layout_btn = QPushButton("➕")
        self.new_layout_btn.setToolTip("Create new layout")
        self.new_layout_btn.setFixedSize(25, 25)
        self.new_layout_btn.clicked.connect(self.create_new_layout)
        layout_toolbar.addWidget(self.new_layout_btn)
        
        layouts_layout.addLayout(layout_toolbar)
        
        # Layout list
        self.layout_library_list = QListWidget()
        self.layout_library_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layout_library_list.customContextMenuRequested.connect(self.show_layout_context_menu)
        self.layout_library_list.itemClicked.connect(self.on_layout_item_selected)
        layouts_layout.addWidget(self.layout_library_list)
        
        # Tiles section
        self.tile_library = TileLibraryWidget(self.manager)
        self.tile_library.tile_selected.connect(self.on_tile_selected)
        
        splitter.addWidget(layouts_widget)
        splitter.addWidget(self.tile_library)
        splitter.setSizes([300, 400])
        
        layout.addWidget(splitter)
        
        # Central content area
        self.central_stack = QStackedWidget()
        self.placeholder_widget = QLabel("Select an item to edit")
        self.placeholder_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_widget.setStyleSheet("color: #666; font-size: 16px;")
        self.central_stack.addWidget(self.placeholder_widget)
        
        # Connect signals
        self.manager.tile_updated_in_studio.connect(self.on_tile_data_changed)
        self.manager.tile_config_updated.connect(self.on_tile_config_changed)
        
        # Populate layouts
        self.populate_layout_library()
        
    def _create_library_panel(self):
        """Create the library panel."""
        self.library_panel = QWidget()
        layout = QVBoxLayout(self.library_panel)
        
        # Library header
        header = QLabel("📚 Tile Library")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Categories
        self.library_tree = QTreeWidget()
        self.library_tree.setHeaderLabel("Available Tile Types")
        
        # Populate with available tile types
        registry = self.manager.registry
        for category in registry.get_categories():
            category_item = QTreeWidgetItem([category])
            category_item.setExpanded(True)
            self.library_tree.addTopLevelItem(category_item)
            
            for metadata in registry.get_plugins_by_category(category):
                tile_item = QTreeWidgetItem([f"{metadata.icon} {metadata.name}"])
                tile_item.setData(0, Qt.ItemDataRole.UserRole, metadata)
                category_item.addChild(tile_item)
                
        layout.addWidget(self.library_tree)
        
    def _on_icon_clicked(self, button):
        """Handle icon button clicks."""
        index = self.icon_group.id(button)
        
        if index == 0:  # Editor
            self._show_editor_panel()
        elif index == 1:  # Library
            self._show_library_panel()
            
    def _show_editor_panel(self):
        """Show the editor panel."""
        self.content_stack.setCurrentWidget(self.editor_panel)
        
    def _show_library_panel(self):
        """Show the library panel."""
        self.content_stack.setCurrentWidget(self.library_panel)
        
    def show_layout_context_menu(self, position):
        """Show context menu for layouts."""
        item = self.layout_library_list.itemAt(position)
        if not item:
            return
            
        layout_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu()
        
        # Standard actions
        duplicate_action = menu.addAction("📋 Duplicate")
        duplicate_action.triggered.connect(lambda: self._duplicate_layout(layout_id))
        
        rename_action = menu.addAction("✏️ Rename")
        rename_action.triggered.connect(lambda: self._rename_layout(item, layout_id))
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self._delete_layout(layout_id))
        
        menu.addSeparator()
        
        # Private checkbox
        private_action = menu.addAction("🔒 Private")
        private_action.setCheckable(True)
        # TODO: Implement privacy settings
        
        menu.addSeparator()
        
        # Project actions
        display_menu = menu.addMenu("📺 Project to Display")
        display_group = QActionGroup(self)
        
        # Get layout display info
        display_info = self.manager.get_layout_display_info(layout_id)
        current_display = display_info.get("target_display", 0)
        
        # Add option for each display
        for i, display in enumerate(self.display_manager.displays):
            action = display_menu.addAction(display.display_name)
            action.setCheckable(True)
            action.setChecked(i == current_display)
            action.setData(i)
            action.triggered.connect(
                lambda checked, idx=i: self.project_to_display(layout_id, idx)
            )
            display_group.addAction(action)
            
        menu.exec(self.layout_library_list.mapToGlobal(position))
        
    def _duplicate_layout(self, layout_id):
        """Duplicate a layout."""
        # TODO: Implement layout duplication
        QMessageBox.information(self, "Duplicate", "Layout duplication coming soon!")
        
    def _rename_layout(self, item, layout_id):
        """Rename a layout."""
        old_name = item.text()
        # Remove icon from name
        if old_name.startswith("📐 "):
            old_name = old_name[2:]
        if "[" in old_name:
            old_name = old_name.split("[")[0].strip()
            
        name, ok = QInputDialog.getText(self, "Rename Layout", "New name:", text=old_name)
        if ok and name:
            # TODO: Save to storage
            self.populate_layout_library()
            
    def _delete_layout(self, layout_id):
        """Delete a layout."""
        reply = QMessageBox.question(self, "Delete Layout", 
                                   "Are you sure you want to delete this layout?",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement layout deletion
            QMessageBox.information(self, "Delete", "Layout deletion coming soon!")
            
    def project_to_display(self, layout_id: str, display_index: int):
        """Project layout to a specific display."""
        self.manager.project_layout(layout_id, display_index)
        
    def populate_layout_library(self):
        """Populate the layout library."""
        self.layout_library_list.clear()
        all_layouts = self.manager.storage.load_data().get("layouts", [])
        
        for layout_data in all_layouts:
            # Get display info
            display_info = self.manager.get_layout_display_info(layout_data['id'])
            display_name = display_info.get("display_name", "No Display")
            
            # Create item with display indicator
            item_text = f"📐 {layout_data['name']} [{display_name}]"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, layout_data['id'])
            
            # Add tooltip with more info
            tooltip = f"Layout: {layout_data['name']}\n"
            tooltip += f"Target Display: {display_name}\n"
            tooltip += f"Tiles: {len(layout_data.get('tile_instances', []))}"
            list_item.setToolTip(tooltip)
            
            self.layout_library_list.addItem(list_item)
            
    def on_layout_item_selected(self, item):
        """Handle layout selection."""
        layout_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Check if editor already exists
        if layout_id not in self.editors:
            layout_data = self.manager.get_layout_by_id(layout_id)
            if not layout_data:
                return
                
            # Create new editor
            self.editors[layout_id] = LayoutEditor(layout_data, self.manager)
            self.central_stack.addWidget(self.editors[layout_id])
            
            # Connect to display changes in the editor
            if hasattr(self.editors[layout_id], 'display_combo'):
                self.editors[layout_id].display_combo.currentIndexChanged.connect(
                    lambda idx: self._on_editor_display_changed(layout_id, idx)
                )
        
        # Switch to this editor
        self.central_stack.setCurrentWidget(self.editors[layout_id])
        
        # Update the editor's display selection to match saved layout settings
        layout_data = self.manager.get_layout_by_id(layout_id)
        if layout_data:
            display_settings = layout_data.get("display_settings", {})
            target_display = display_settings.get("target_display", 0)
            
            # Update the display combo in the editor
            editor = self.editors[layout_id]
            if hasattr(editor, 'display_combo'):
                # Block signals to prevent triggering save during load
                editor.display_combo.blockSignals(True)
                
                # Set the display if it exists
                if target_display < editor.display_combo.count():
                    editor.display_combo.setCurrentIndex(target_display)
                else:
                    # Display no longer exists, use primary
                    editor.display_combo.setCurrentIndex(0)
                    
                editor.display_combo.blockSignals(False)
                
                # Trigger display update in editor
                editor._on_display_selected(editor.display_combo.currentIndex())
                
    def _on_editor_display_changed(self, layout_id: str, display_index: int):
        """Handle when user changes display in the editor."""
        # Save the display selection to the layout
        self.manager.update_layout_display(layout_id, display_index)
        
        # Update the library to show new display
        self.populate_layout_library()
        
        # Keep the same item selected
        for i in range(self.layout_library_list.count()):
            item = self.layout_library_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == layout_id:
                item.setSelected(True)
                break
        
    def on_tile_selected(self, tile_id):
        """Handle tile selection from the library."""
        if tile_id not in self.editors:
            # Use plugin system to create appropriate editor
            editor = self.manager.create_tile_editor(tile_id)
            if editor:
                self.editors[tile_id] = editor
                self.central_stack.addWidget(editor)
            else:
                # No editor available for this tile type
                print(f"No editor available for tile {tile_id}")
                return
        self.central_stack.setCurrentWidget(self.editors[tile_id])
        
    def on_tile_data_changed(self, updated_tile_data: dict):
        """Handle tile data changes."""
        # Update the tile library
        self.tile_library.populate_tree()
        
        # Update layout editor if visible
        current_widget = self.central_stack.currentWidget()
        if isinstance(current_widget, LayoutEditor):
            if hasattr(current_widget, 'update_tile_display'):
                current_widget.update_tile_display(updated_tile_data)
                
    def on_tile_config_changed(self, updated_tile_data: dict):
        """Handle tile configuration changes."""
        self.tile_library.populate_tree()
        
    def create_new_layout(self):
        """Create a new layout."""
        self.manager.create_new_layout()
        self.populate_layout_library()
        
    def closeEvent(self, event):
        """Handle window close event."""
        if self.manager.shutting_down:
            event.accept()
        else:
            event.ignore()
            self.hide()