# pinpoint/main_window_refactored.py
"""
Refactored main window with complete separation of design and functionality.
This file contains ONLY structure and behavior, NO visual styling.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QStackedWidget, QButtonGroup,
                              QDialog, QMessageBox, QInputDialog, QVBoxLayout,
                              QHBoxLayout, QSplitter, QTreeWidgetItem, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QActionGroup

from .design_layer import DesignLayer
from .widget_factory import WidgetFactory
from .display_manager import get_display_manager

# These imports remain the same as they're functional components
from .layout_editor_refactored import LayoutEditor  # Will need refactoring too
from .draggable_list_widget import DraggableListWidget  # Already functional


class MainWindow(QMainWindow):
    """
    Main application window.
    All visual aspects are handled by the design layer.
    """
    
    def __init__(self, manager, design_layer: DesignLayer):
        super().__init__()
        self.manager = manager
        self.design = design_layer
        self.factory = WidgetFactory(design_layer)
        self.display_manager = get_display_manager()
        self.editors = {}
        
        # Window identification for design system
        self.setObjectName("main_window")
        
        # Set window title from design
        self.setWindowTitle(self.design.get_text("window_title", "PinPoint Studio"))
        
        # Create UI structure (no styling)
        self._create_ui()
        
        # Connect signals (functionality only)
        self._connect_signals()
        
        # Apply all design/styling
        self.design.apply_design(self)
        
        # Load initial content
        self._show_editor_panel()
        
        # Connect to design reload for live updates
        self.design.design_reloaded.connect(self._on_design_reloaded)
    
    def _create_ui(self):
        """Create the UI structure without any styling."""
        # Create main container
        main_widget = QWidget()
        main_widget.setObjectName("main_container")
        
        # Create layout from design specification
        layout_spec = self.design.get_layout("main_window")
        if layout_spec:
            # Use design layer to create the layout structure
            main_layout = self.factory.create_layout_from_spec(layout_spec)
        else:
            # Fallback to simple layout
            main_layout = QHBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
        
        main_widget.setLayout(main_layout)
        
        # Create sidebar with navigation buttons
        self._create_sidebar()
        
        # Create content area
        self._create_content_area()
        
        # Add to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        self.setCentralWidget(main_widget)
    
    def _create_sidebar(self):
        """Create sidebar structure."""
        # Define button configurations (functionality, not style)
        button_configs = [
            {'id': 'editor_btn', 'icon': 'editor', 'tooltip': 'Editor', 'checkable': True},
            {'id': 'library_btn', 'icon': 'library', 'tooltip': 'Library', 'checkable': True},
            {'id': 'marketplace_btn', 'icon': 'marketplace', 'tooltip': 'Marketplace (Coming Soon)', 'checkable': True, 'enabled': False},
            {'id': 'account_btn', 'icon': 'account', 'tooltip': 'Account (Coming Soon)', 'checkable': True, 'enabled': False},
            {'id': 'settings_btn', 'icon': 'settings', 'tooltip': 'Settings (Coming Soon)', 'checkable': True, 'enabled': False}
        ]
        
        # Create sidebar using factory
        self.sidebar = self.factory.create_main_sidebar(button_configs)
        
        # Create button group for exclusive selection
        self.sidebar_button_group = QButtonGroup()
        for i, (btn_id, btn) in enumerate(self.sidebar.buttons.items()):
            self.sidebar_button_group.addButton(btn, i)
            if not btn.isEnabled():
                btn.setEnabled(False)
    
    def _create_content_area(self):
        """Create content area structure."""
        self.content_area = QWidget()
        self.content_area.setObjectName("content_area")
        
        # Create layout
        content_layout = QHBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left panel (for editor panel content)
        self.left_panel = QWidget()
        self.left_panel.setObjectName("left_panel")
        
        # Stack for left panel content
        self.left_panel_stack = QStackedWidget()
        self.left_panel_stack.setObjectName("left_panel_content")
        
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.left_panel_stack)
        
        # Create panels
        self._create_editor_panel()
        self._create_library_panel()
        
        # Add panels to stack
        self.left_panel_stack.addWidget(self.editor_panel)
        self.left_panel_stack.addWidget(self.library_panel)
        
        # Central content stack
        self.central_stack = self.factory.create_content_stack()
        
        # Add to content layout
        content_layout.addWidget(self.left_panel)
        content_layout.addWidget(self.central_stack)
    
    def _create_editor_panel(self):
        """Create the editor panel (layouts and tiles)."""
        self.editor_panel = QWidget()
        self.editor_panel.setObjectName("editor_panel")
        
        layout = QVBoxLayout(self.editor_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for layouts and tiles
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setObjectName("editor_splitter")
        
        # Layouts section
        layouts_widget = QWidget()
        layouts_widget.setObjectName("layouts_section")
        layouts_layout = QVBoxLayout(layouts_widget)
        
        # Layout controls
        layout_toolbar = QWidget()
        layout_toolbar.setObjectName("layout_toolbar")
        toolbar_layout = QHBoxLayout(layout_toolbar)
        
        # Layout label
        layouts_label = self.factory.create_label("Layouts", "layouts_label")
        toolbar_layout.addWidget(layouts_label)
        toolbar_layout.addStretch()
        
        # New layout button
        self.new_layout_btn = self.factory.create_icon_button(
            icon_name="add",
            tooltip="Create new layout",
            widget_id="new_layout_button"
        )
        toolbar_layout.addWidget(self.new_layout_btn)
        
        layouts_layout.addWidget(layout_toolbar)
        
        # Layout list
        self.layout_library_list = self.factory.create_layout_list()
        layouts_layout.addWidget(self.layout_library_list)
        
        # Tiles section
        self.tile_library = TileLibraryWidget(self.manager, self.design, self.factory)
        
        # Add to splitter
        splitter.addWidget(layouts_widget)
        splitter.addWidget(self.tile_library)
        splitter.setSizes([300, 400])  # Default sizes
        
        layout.addWidget(splitter)
    
    def _create_library_panel(self):
        """Create the library panel."""
        self.library_panel = QWidget()
        self.library_panel.setObjectName("library_panel")
        
        layout = QVBoxLayout(self.library_panel)
        
        # Library header
        header = self.factory.create_label(
            self.design.get_text("library.header", "📚 Tile Library"),
            "library_header"
        )
        layout.addWidget(header)
        
        # Categories tree
        self.library_tree = self.factory.create_tile_library_tree()
        self.library_tree.setObjectName("library_categories_tree")
        self.library_tree.setHeaderLabel("Available Tile Types")
        
        # Populate with available tile types
        self._populate_library_tree()
        
        layout.addWidget(self.library_tree)
    
    def _connect_signals(self):
        """Connect all signals (functionality only)."""
        # Sidebar navigation
        self.sidebar_button_group.buttonClicked.connect(self._on_sidebar_button_clicked)
        
        # Layout controls
        self.new_layout_btn.clicked.connect(self.create_new_layout)
        self.layout_library_list.itemClicked.connect(self.on_layout_item_selected)
        self.layout_library_list.customContextMenuRequested.connect(self.show_layout_context_menu)
        
        # Tile library
        self.tile_library.tile_selected.connect(self.on_tile_selected)
        
        # Manager signals
        self.manager.tile_updated_in_studio.connect(self.on_tile_data_changed)
        self.manager.tile_config_updated.connect(self.on_tile_config_changed)
        
        # Load initial data
        self.populate_layout_library()
    
    def _on_sidebar_button_clicked(self, button):
        """Handle sidebar button clicks."""
        index = self.sidebar_button_group.id(button)
        
        if index == 0:  # Editor
            self._show_editor_panel()
        elif index == 1:  # Library
            self._show_library_panel()
    
    def _show_editor_panel(self):
        """Show the editor panel."""
        self.left_panel_stack.setCurrentWidget(self.editor_panel)
        
    def _show_library_panel(self):
        """Show the library panel."""
        self.left_panel_stack.setCurrentWidget(self.library_panel)
    
    def _populate_library_tree(self):
        """Populate the library tree with tile types."""
        registry = self.manager.registry
        for category in registry.get_categories():
            category_item = QTreeWidgetItem([category])
            category_item.setExpanded(True)
            self.library_tree.addTopLevelItem(category_item)
            
            for metadata in registry.get_plugins_by_category(category):
                # Create item with icon from design
                tile_item = self.factory.create_tree_item(
                    text=metadata.name,
                    data=metadata,
                    icon_name=metadata.tile_id
                )
                category_item.addChild(tile_item)
    
    def populate_layout_library(self):
        """Populate the layout library list."""
        self.layout_library_list.clear()
        all_layouts = self.manager.storage.load_data().get("layouts", [])
        
        for layout_data in all_layouts:
            # Get display info
            display_info = self.manager.get_layout_display_info(layout_data['id'])
            display_name = display_info.get("display_name", "No Display")
            
            # Create item
            item_text = f"{layout_data['name']} [{display_name}]"
            list_item = self.factory.create_list_item(
                text=item_text,
                data=layout_data['id'],
                icon_name="layout"
            )
            
            # Add tooltip
            tooltip = f"Layout: {layout_data['name']}\n"
            tooltip += f"Target Display: {display_name}\n"
            tooltip += f"Tiles: {len(layout_data.get('tile_instances', []))}"
            list_item.setToolTip(tooltip)
            
            self.layout_library_list.addItem(list_item)
    
    def show_layout_context_menu(self, position):
        """Show context menu for layouts."""
        item = self.layout_library_list.itemAt(position)
        if not item:
            return
        
        layout_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Create menu from specification
        menu_spec = self.design.get_component("layout_context_menu")
        if not menu_spec:
            # Fallback menu structure
            menu_spec = {
                "items": [
                    {"id": "duplicate_layout", "text": "Duplicate", "icon": "duplicate"},
                    {"id": "rename_layout", "text": "Rename", "icon": "rename"},
                    {"id": "delete_layout", "text": "Delete", "icon": "delete"},
                    {"type": "separator"},
                    {"id": "private_layout", "text": "Private", "checkable": True},
                    {"type": "separator"},
                    {"id": "project_menu", "text": "Project to Display", "type": "submenu"}
                ]
            }
        
        menu = self.factory.create_menu(menu_spec, self)
        
        # Connect actions
        self._connect_layout_menu_actions(menu, layout_id)
        
        # Show menu
        menu.exec(self.layout_library_list.mapToGlobal(position))
    
    def _connect_layout_menu_actions(self, menu, layout_id):
        """Connect layout context menu actions."""
        # Find actions by object name
        duplicate_action = menu.findChild(QAction, "duplicate_layout")
        if duplicate_action:
            duplicate_action.triggered.connect(lambda: self._duplicate_layout(layout_id))
        
        rename_action = menu.findChild(QAction, "rename_layout")
        if rename_action:
            rename_action.triggered.connect(lambda: self._rename_layout(layout_id))
        
        delete_action = menu.findChild(QAction, "delete_layout")
        if delete_action:
            delete_action.triggered.connect(lambda: self._delete_layout(layout_id))
        
        # Handle project submenu
        project_menu = menu.findChild(QMenu, "project_menu")
        if project_menu:
            self._populate_project_menu(project_menu, layout_id)
    
    def _populate_project_menu(self, menu, layout_id):
        """Populate the project submenu with displays."""
        display_group = QActionGroup(self)
        
        # Get layout display info
        display_info = self.manager.get_layout_display_info(layout_id)
        current_display = display_info.get("target_display", 0)
        
        # Add option for each display
        for i, display in enumerate(self.display_manager.displays):
            action = menu.addAction(display.display_name)
            action.setCheckable(True)
            action.setChecked(i == current_display)
            action.setData(i)
            action.triggered.connect(
                lambda checked, idx=i: self.project_to_display(layout_id, idx)
            )
            display_group.addAction(action)
    
    def _duplicate_layout(self, layout_id):
        """Duplicate a layout."""
        # TODO: Implement layout duplication
        QMessageBox.information(self, "Duplicate", "Layout duplication coming soon!")
    
    def _rename_layout(self, layout_id):
        """Rename a layout."""
        # Find the item
        for i in range(self.layout_library_list.count()):
            item = self.layout_library_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == layout_id:
                old_name = item.text()
                # Remove icon and display info from name
                if " [" in old_name:
                    old_name = old_name.split(" [")[0]
                # Remove icon
                parts = old_name.split(" ", 1)
                if len(parts) > 1:
                    old_name = parts[1]
                
                name, ok = QInputDialog.getText(
                    self, 
                    "Rename Layout", 
                    "New name:", 
                    text=old_name
                )
                if ok and name:
                    # TODO: Save to storage
                    self.populate_layout_library()
                break
    
    def _delete_layout(self, layout_id):
        """Delete a layout."""
        reply = QMessageBox.question(
            self, 
            "Delete Layout",
            "Are you sure you want to delete this layout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement layout deletion
            QMessageBox.information(self, "Delete", "Layout deletion coming soon!")
    
    def project_to_display(self, layout_id: str, display_index: int):
        """Project layout to a specific display."""
        self.manager.project_layout(layout_id, display_index)
    
    def on_layout_item_selected(self, item):
        """Handle layout selection."""
        layout_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Check if editor already exists
        if layout_id not in self.editors:
            layout_data = self.manager.get_layout_by_id(layout_id)
            if not layout_data:
                return
            
            # Create new editor (this will also need refactoring)
            self.editors[layout_id] = LayoutEditor(layout_data, self.manager)
            self.central_stack.addWidget(self.editors[layout_id])
        
        # Switch to this editor
        self.central_stack.setCurrentWidget(self.editors[layout_id])
    
    def on_tile_selected(self, tile_id):
        """Handle tile selection from the library."""
        if tile_id not in self.editors:
            # Use plugin system to create appropriate editor
            editor = self.manager.create_tile_editor(tile_id)
            if editor:
                self.editors[tile_id] = editor
                self.central_stack.addWidget(editor)
            else:
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
    
    def _on_design_reloaded(self):
        """Handle design reload for live updates."""
        print("Design reloaded - UI updated automatically")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.manager.shutting_down:
            event.accept()
        else:
            event.ignore()
            self.hide()


class TileLibraryWidget(QWidget):
    """Refactored tile library widget with design separation."""
    
    tile_selected = Signal(str)  # tile_id
    
    def __init__(self, manager, design_layer, widget_factory, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.design = design_layer
        self.factory = widget_factory
        
        self.setObjectName("tile_library_widget")
        
        # Create structure
        self._create_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Populate initial data
        self.populate_tree()
    
    def _create_ui(self):
        """Create UI structure without styling."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header section
        header_widget = QWidget()
        header_widget.setObjectName("tile_library_header")
        header_layout = QHBoxLayout(header_widget)
        
        # New tile button
        self.new_tile_btn = self.factory.create_button(
            text=self.design.get_text("button.new_tile", "New Tile"),
            widget_id="new_tile_button"
        )
        self.new_tile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self.new_tile_btn)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)
        
        # Separator
        separator = self.factory.create_separator("tile_library_separator")
        layout.addWidget(separator)
        
        # Tree widget
        self.tree = self.factory.create_tile_library_tree()
        self.tree.setObjectName("tile_tree")
        layout.addWidget(self.tree)
    
    def _connect_signals(self):
        """Connect signals."""
        self.new_tile_btn.clicked.connect(self._create_tile)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
    
    def _create_tile(self):
        """Create a new tile."""
        # Use NewTileDialog (also needs refactoring)
        from .dialogs import NewTileDialog  # Assume this exists
        dialog = NewTileDialog(self.manager, self.design, self)
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
        """Show context menu."""
        item = self.tree.itemAt(position)
        if not item:
            return
        
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type != "tile":
            return
        
        # Create menu from design specification
        menu_spec = self.design.get_component("tile_context_menu")
        if not menu_spec:
            # Fallback menu structure
            menu_spec = {
                "items": [
                    {"id": "duplicate_tile", "text": "Duplicate", "icon": "duplicate"},
                    {"id": "rename_tile", "text": "Rename", "icon": "rename"},
                    {"type": "separator"},
                    {"id": "delete_tile", "text": "Delete", "icon": "delete"}
                ]
            }
        
        menu = self.factory.create_menu(menu_spec, self)
        
        # Connect actions
        duplicate_action = menu.findChild(QAction, "duplicate_tile")
        if duplicate_action:
            duplicate_action.triggered.connect(lambda: self._duplicate_item(item))
        
        rename_action = menu.findChild(QAction, "rename_tile")
        if rename_action:
            rename_action.triggered.connect(lambda: self._rename_item(item))
        
        delete_action = menu.findChild(QAction, "delete_tile")
        if delete_action:
            delete_action.triggered.connect(lambda: self._delete_item(item))
        
        menu.exec(self.tree.mapToGlobal(position))
    
    def _duplicate_item(self, item):
        """Duplicate a tile."""
        tile_id = item.data(0, Qt.ItemDataRole.UserRole)
        if tile_id:
            self.manager.duplicate_tile(tile_id)
            self.populate_tree()
    
    def _rename_item(self, item):
        """Rename a tile."""
        old_name = item.text(0)
        # Remove icon from name if present
        parts = old_name.split(' ', 1)
        if len(parts) > 1:
            old_name = parts[1]
        
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and name:
            tile_id = item.data(0, Qt.ItemDataRole.UserRole)
            if tile_id:
                # Update the tile's display name in storage
                tile_data = self.manager.get_tile_by_id(tile_id)
                if tile_data:
                    tile_data['custom_name'] = name
                    self.manager._cache_dirty = True
                    self.manager._save_cached_data()
                    self.populate_tree()
    
    def _delete_item(self, item):
        """Delete a tile with confirmation."""
        reply = QMessageBox.question(
            self,
            "Delete Tile",
            "Are you sure you want to delete this tile?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            tile_id = item.data(0, Qt.ItemDataRole.UserRole)
            if tile_id:
                self.manager.delete_tile(tile_id)
                self.populate_tree()
    
    def populate_tree(self):
        """Populate the tree with tiles."""
        self.tree.clear()
        
        # Get all tiles
        all_tiles = self.manager.get_all_tile_data()
        
        for tile_data in all_tiles:
            # Get metadata for this tile type
            tile_type = tile_data.get('type', 'note')
            metadata = self.manager.registry.get_metadata(tile_type)
            
            # Create tree item
            content = tile_data.get('content', '')
            custom_name = tile_data.get('custom_name', '')
            
            if custom_name:
                item_text = custom_name
            else:
                item_text = content.split('\n')[0][:30] or "Empty"
            
            # Create item with icon
            tree_item = self.factory.create_tree_item(
                text=item_text,
                data=tile_data['id'],
                icon_name=tile_type if metadata else None
            )
            
            # Store additional data
            tree_item.setData(0, Qt.ItemDataRole.UserRole + 1, "tile")
            tree_item.setData(0, Qt.ItemDataRole.UserRole + 2, tile_type)
            
            # Make draggable
            tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
            
            # Add tooltip
            if metadata:
                tooltip = f"{metadata.name} • {metadata.category}"
                tree_item.setToolTip(0, tooltip)
            
            self.tree.addTopLevelItem(tree_item)