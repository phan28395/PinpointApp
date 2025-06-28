# pinpoint/main_window.py
from .display_manager import get_display_manager
from PySide6.QtGui import QActionGroup
import uuid
from PySide6.QtWidgets import (QMainWindow, QLabel, QSplitter, QListWidget, 
                              QListWidgetItem, QTabWidget, QPushButton, 
                              QVBoxLayout, QWidget, QMenu, QStackedWidget,
                              QTreeWidget, QTreeWidgetItem, QHBoxLayout,
                              QDialog, QDialogButtonBox, QTextEdit,
                              QToolBar, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon
from .layout_editor import LayoutEditor
from .draggable_list_widget import DraggableListWidget


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
    """Enhanced tile library with categorization and search."""
    
    tile_selected = Signal(str)  # tile_id
    
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.addItems(self.manager.get_tile_categories())
        self.category_combo.currentTextChanged.connect(self._filter_tiles)
        filter_layout.addWidget(self.category_combo)
        
        layout.addLayout(filter_layout)
        
        # Tile list
        self.tile_list = DraggableListWidget()
        self.tile_list.itemClicked.connect(self._on_item_clicked)
        self.tile_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tile_list.customContextMenuRequested.connect(self._show_tile_menu)
        layout.addWidget(self.tile_list)
        
        self.populate_tiles()
        
    def populate_tiles(self, category_filter=None):
        """Populate the tile list."""
        self.tile_list.clear()
        all_tiles = self.manager.get_all_tile_data()
        
        for tile_data in all_tiles:
            # Get metadata for this tile type
            tile_type = tile_data.get('type', 'note')
            metadata = self.manager.registry.get_metadata(tile_type)
            
            # Apply category filter
            if category_filter and category_filter != "All Categories":
                if not metadata or metadata.category != category_filter:
                    continue
            
            # Create list item
            content = tile_data.get('content', '')
            item_text = content.split('\n')[0][:30] or "Empty"
            
            if metadata:
                item_text = f"{metadata.icon} {item_text}"
                
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, tile_data['id'])
            list_item.setData(Qt.ItemDataRole.UserRole + 1, tile_type)
            
            # Add tooltip with tile info
            if metadata:
                tooltip = f"Type: {metadata.name}\nCategory: {metadata.category}"
                list_item.setToolTip(tooltip)
                
            self.tile_list.addItem(list_item)
            
    def _filter_tiles(self, category):
        """Filter tiles by category."""
        self.populate_tiles(category if category != "All Categories" else None)
        
    def _on_item_clicked(self, item):
        """Handle tile selection."""
        tile_id = item.data(Qt.ItemDataRole.UserRole)
        self.tile_selected.emit(tile_id)
        
    def _show_tile_menu(self, position):
        """Show context menu for tiles."""
        item = self.tile_list.itemAt(position)
        if not item:
            return
            
        tile_id = item.data(Qt.ItemDataRole.UserRole)
        tile_type = item.data(Qt.ItemDataRole.UserRole + 1)
        
        menu = QMenu()
        
        # Add actions based on capabilities
        metadata = self.manager.registry.get_metadata(tile_type)
        if metadata:
            if "can_edit" in metadata.capabilities:
                edit_action = menu.addAction("✏️ Edit")
                edit_action.triggered.connect(lambda: self.tile_selected.emit(tile_id))
                
            if "can_export" in metadata.capabilities:
                export_action = menu.addAction("📤 Export")
                # TODO: Implement export functionality
                
        menu.addSeparator()
        
        duplicate_action = menu.addAction("📋 Duplicate")
        duplicate_action.triggered.connect(lambda: self._duplicate_tile(tile_id))
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self._delete_tile(tile_id))
        
        menu.exec(self.tile_list.mapToGlobal(position))
        
    def _duplicate_tile(self, tile_id):
        """Duplicate a tile."""
        new_tile = self.manager.duplicate_tile(tile_id)
        if new_tile:
            self.populate_tiles(self.category_combo.currentText())
            
    def _delete_tile(self, tile_id):
        """Delete a tile after confirmation."""
        # TODO: Add confirmation dialog
        self.manager.delete_tile(tile_id)
        self.populate_tiles(self.category_combo.currentText())


class MainWindow(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.display_manager = get_display_manager()
        self.manager = manager
        self.editors = {}
        
        self.setWindowTitle("PinPoint Studio")
        self.setMinimumSize(1000, 700)
        
        # Create toolbar
        self._create_toolbar()
        
        # --- Left Sidebar Setup ---
        left_sidebar_widget = QWidget()
        left_sidebar_layout = QVBoxLayout(left_sidebar_widget)
        left_sidebar_layout.setContentsMargins(5, 5, 5, 5)
        left_sidebar_layout.setSpacing(5)
        
        # Layout controls
        layout_controls = QHBoxLayout()
        self.new_layout_button = QPushButton("📑 New Layout")
        self.new_layout_button.clicked.connect(self.create_new_layout)
        layout_controls.addWidget(self.new_layout_button)
        left_sidebar_layout.addLayout(layout_controls)
        
        # Tile controls
        tile_controls = QHBoxLayout()
        self.new_tile_button = QPushButton("➕ New Tile")
        self.new_tile_button.clicked.connect(self.create_new_tile)
        tile_controls.addWidget(self.new_tile_button)
        left_sidebar_layout.addLayout(tile_controls)
        
        # Splitter for library lists
        sidebar_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Layout list
        self.layout_library_list = QListWidget()
        self.layout_library_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layout_library_list.customContextMenuRequested.connect(self.show_layout_context_menu)
        
        # Enhanced tile library
        self.tile_library = TileLibraryWidget(self.manager)
        self.tile_library.tile_selected.connect(self.on_tile_selected)
        
        sidebar_splitter.addWidget(self.layout_library_list)
        sidebar_splitter.addWidget(self.tile_library)
        sidebar_splitter.setSizes([300, 400])
        
        left_sidebar_layout.addWidget(sidebar_splitter)
        
        # Plugin info at bottom
        self.plugin_info_label = QLabel()
        self._update_plugin_info()
        left_sidebar_layout.addWidget(self.plugin_info_label)
        
        # --- Central Area with QStackedWidget ---
        self.central_stack = QStackedWidget()
        self.placeholder_widget = QLabel("Select an item from the library")
        self.placeholder_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_stack.addWidget(self.placeholder_widget)
        
        # --- Main Splitter ---
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_sidebar_widget)
        main_splitter.addWidget(self.central_stack)
        main_splitter.setSizes([300, 700])
        self.setCentralWidget(main_splitter)
        
        # Populate libraries
        self.populate_all_libraries()
        
        # --- Connect Signals ---
        self.layout_library_list.itemClicked.connect(self.on_layout_item_selected)
        self.manager.tile_updated_in_studio.connect(self.on_tile_data_changed)
        self.manager.tile_config_updated.connect(self.on_tile_config_changed)
        
    def _create_toolbar(self):
        """Create the main toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Refresh plugins action
        refresh_action = QAction("🔄 Refresh Plugins", self)
        refresh_action.setToolTip("Reload all plugins")
        refresh_action.triggered.connect(self._refresh_plugins)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Plugin folder action
        plugin_folder_action = QAction("📁 Open Plugin Folder", self)
        plugin_folder_action.setToolTip("Open the user plugins folder")
        plugin_folder_action.triggered.connect(self._open_plugin_folder)
        toolbar.addAction(plugin_folder_action)
        
    def _refresh_plugins(self):
        """Refresh the plugin registry."""
        # Re-initialize the registry
        self.manager.registry.initialize()
        self._update_plugin_info()
        self.populate_all_libraries()
        
    def _open_plugin_folder(self):
        """Open the user plugins folder."""
        from pathlib import Path
        import os
        import platform
        
        plugin_dir = Path.home() / ".pinpoint" / "plugins"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Open folder in system file manager
        if platform.system() == 'Windows':
            os.startfile(str(plugin_dir))
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open "{plugin_dir}"')
        else:  # Linux
            os.system(f'xdg-open "{plugin_dir}"')
            
    def _update_plugin_info(self):
        """Update the plugin info label."""
        plugin_count = len(self.manager.registry.get_all_metadata())
        categories = len(self.manager.get_tile_categories())
        self.plugin_info_label.setText(
            f"📦 {plugin_count} plugins in {categories} categories"
        )
        
    def create_new_tile(self):
        """Show dialog to create a new tile with type selection."""
        dialog = NewTileDialog(self.manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_type:
            self.manager.create_new_tile_definition(dialog.selected_type)
            self.populate_tile_library()
            
    def on_tile_data_changed(self, updated_tile_data: dict):
        """Handle tile data changes."""
        # Only refresh the tile library item, not the entire library
        tile_id = updated_tile_data.get('id')
        if not tile_id:
            return
            
        # Update the specific item in the library
        for i in range(self.tile_library.tile_list.count()):
            item = self.tile_library.tile_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tile_id:
                # Update just this item's text
                content = updated_tile_data.get('content', '')
                item_text = content.split('\n')[0][:30] or "Empty"
                
                # Get metadata for icon
                tile_type = updated_tile_data.get('type', 'note')
                metadata = self.manager.registry.get_metadata(tile_type)
                if metadata:
                    item_text = f"{metadata.icon} {item_text}"
                    
                item.setText(item_text)
                break
        
        # Only refresh layout editor items if it's currently visible
        current_widget = self.central_stack.currentWidget()
        if isinstance(current_widget, LayoutEditor):
            # Use the more efficient update method if available
            if hasattr(current_widget, 'update_tile_display'):
                current_widget.update_tile_display(updated_tile_data)
            else:
                current_widget.load_items()
            
    def on_tile_config_changed(self, updated_tile_data: dict):
        """Handle tile configuration changes."""
        # Config changes also refresh the library
        self.populate_tile_library()
        
    def show_layout_context_menu(self, position):
        """Creates and shows a right-click menu for layout items."""
        item = self.layout_library_list.itemAt(position)
        if not item:
            return

        layout_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu()
        
        # Get layout display info
        display_info = self.manager.get_layout_display_info(layout_id)
        current_display = display_info.get("target_display", 0)
        
        # Create display submenu
        display_menu = menu.addMenu("📺 Project to Display")
        display_group = QActionGroup(self)
        
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
        
        display_menu.addSeparator()
        
        # Add "All Displays" option
        all_displays_action = display_menu.addAction("🖥️ All Displays (Span)")
        all_displays_action.triggered.connect(
            lambda: self.manager.project_layout_to_all_displays(layout_id)
        )
        
        menu.exec(self.layout_library_list.mapToGlobal(position))
                    
    def project_selected_layout(self):
        """Calls the manager to show the selected layout's tiles live."""
        selected_item = self.layout_library_list.currentItem()
        if not selected_item:
            return
        layout_id = selected_item.data(Qt.ItemDataRole.UserRole)
        print(f"Projecting layout {layout_id}...")
        self.manager.project_layout(layout_id)

    def project_to_display(self, layout_id: str, display_index: int):
        """Project layout to a specific display."""
        print(f"Projecting layout {layout_id} to display {display_index}")
        self.manager.project_layout(layout_id, display_index)

    def populate_all_libraries(self):
        """Populate both layout and tile libraries."""
        self.populate_layout_library()
        self.populate_tile_library()
        
    def populate_tile_library(self):
        """Refresh the tile library."""
        current_category = self.tile_library.category_combo.currentText()
        self.tile_library.populate_tiles(
            current_category if current_category != "All Categories" else None
        )
        
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