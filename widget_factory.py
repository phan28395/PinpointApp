# pinpoint/widget_factory.py
"""
Factory for creating widgets without any styling.
All widgets are created with structure and functionality only.
Visual appearance is handled by the design layer.
"""

from typing import Dict, Any, Optional, List, Callable
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel, QTextEdit, QLineEdit,
                              QComboBox, QSpinBox, QCheckBox, QRadioButton,
                              QSlider, QProgressBar, QListWidget, QTreeWidget,
                              QFrame, QGroupBox, QTabWidget, QStackedWidget,
                              QToolBar, QMenuBar, QMenu, QStatusBar,
                              QVBoxLayout, QHBoxLayout, QGridLayout,
                              QListWidgetItem, QTreeWidgetItem)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QAction


class WidgetFactory(QObject):
    """
    Creates widgets with pure functionality, no styling.
    Works in conjunction with DesignLayer for visual appearance.
    """
    
    def __init__(self, design_layer):
        super().__init__()
        self.design = design_layer
        
    # Main Window Components
    
    def create_main_sidebar(self, button_configs: List[Dict[str, Any]]) -> QWidget:
        """Create the main sidebar with navigation buttons."""
        sidebar = QWidget()
        sidebar.setObjectName("main_sidebar")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create buttons from config
        buttons = {}
        for config in button_configs:
            btn = self.create_icon_button(
                icon_name=config.get('icon'),
                tooltip=config.get('tooltip', ''),
                widget_id=config.get('id'),
                checkable=config.get('checkable', True)
            )
            
            buttons[config['id']] = btn
            layout.addWidget(btn)
        
        # Add stretch at the end
        layout.addStretch()
        
        # Store buttons for easy access
        sidebar.buttons = buttons
        
        return sidebar
    
    def create_icon_button(self, icon_name: str, tooltip: str = "", 
                          widget_id: str = None, checkable: bool = False) -> QPushButton:
        """Create an icon button without styling."""
        # Get icon text from design
        icon_text = self.design.get_icon_text(icon_name)
        
        btn = QPushButton(icon_text)
        if widget_id:
            btn.setObjectName(widget_id)
        
        btn.setToolTip(tooltip)
        btn.setCheckable(checkable)
        
        return btn
    
    def create_tile_library_tree(self) -> QTreeWidget:
        """Create the tile library tree widget."""
        tree = QTreeWidget()
        tree.setObjectName("tile_library_tree")
        tree.setHeaderHidden(True)
        tree.setFrameShape(QFrame.Shape.NoFrame)
        tree.setRootIsDecorated(False)
        tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        tree.setDragEnabled(True)
        tree.setAcceptDrops(False)
        tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        tree.setDefaultDropAction(Qt.DropAction.CopyAction)
        
        return tree
    
    def create_layout_list(self) -> QListWidget:
        """Create the layout library list widget."""
        list_widget = QListWidget()
        list_widget.setObjectName("layout_library_list")
        list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        return list_widget
    
    def create_content_stack(self) -> QStackedWidget:
        """Create the central content stack widget."""
        stack = QStackedWidget()
        stack.setObjectName("central_content_stack")
        
        # Add placeholder
        placeholder = QLabel()
        placeholder.setObjectName("content_placeholder")
        placeholder.setText(self.design.get_text("placeholder.select_item", "Select an item to edit"))
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        stack.addWidget(placeholder)
        
        return stack
    
    # Tile Components
    
    def create_tile_container(self, tile_id: str, tile_type: str) -> QWidget:
        """Create a tile container without styling."""
        container = QFrame()
        container.setObjectName(f"tile_container_{tile_type}")
        
        # Main layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        return container
    
    def create_tile_header(self, tile_id: str) -> QWidget:
        """Create tile header with controls."""
        header = QWidget()
        header.setObjectName("tile_header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Drag handle (invisible but functional)
        drag_handle = QFrame()
        drag_handle.setObjectName("tile_drag_handle")
        drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(drag_handle, 1)  # Takes remaining space
        
        # Control buttons container
        controls = QWidget()
        controls.setObjectName("tile_controls")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        
        # Pin button
        pin_btn = QPushButton()
        pin_btn.setObjectName("tile_pin_button")
        pin_btn.setText(self.design.get_icon_text("pin"))
        pin_btn.setCheckable(True)
        controls_layout.addWidget(pin_btn)
        
        # Close button
        close_btn = QPushButton()
        close_btn.setObjectName("tile_close_button")
        close_btn.setText(self.design.get_icon_text("close"))
        controls_layout.addWidget(close_btn)
        
        layout.addWidget(controls)
        
        # Store references
        header.drag_handle = drag_handle
        header.pin_button = pin_btn
        header.close_button = close_btn
        
        return header
    
    # Dialog Components
    
    def create_dialog_buttons(self, buttons: List[str]) -> QWidget:
        """Create dialog button bar."""
        container = QWidget()
        container.setObjectName("dialog_buttons")
        
        layout = QHBoxLayout(container)
        layout.addStretch()
        
        button_widgets = {}
        for btn_type in buttons:
            btn = QPushButton()
            btn.setObjectName(f"dialog_button_{btn_type}")
            btn.setText(self.design.get_text(f"button.{btn_type}", btn_type.title()))
            button_widgets[btn_type] = btn
            layout.addWidget(btn)
        
        container.buttons = button_widgets
        return container
    
    # Menu Creation
    
    def create_menu(self, menu_spec: Dict[str, Any], parent: QWidget = None) -> QMenu:
        """Create a menu from specification."""
        menu = QMenu(parent)
        
        if 'id' in menu_spec:
            menu.setObjectName(menu_spec['id'])
        
        if 'title' in menu_spec:
            menu.setTitle(menu_spec['title'])
        
        # Add items
        for item_spec in menu_spec.get('items', []):
            if item_spec.get('type') == 'separator':
                menu.addSeparator()
            elif item_spec.get('type') == 'submenu':
                submenu = self.create_menu(item_spec, menu)
                menu.addMenu(submenu)
            else:
                action = self.create_action(item_spec)
                menu.addAction(action)
        
        return menu
    
    def create_action(self, action_spec: Dict[str, Any]) -> QAction:
        """Create an action from specification."""
        text = self.design.get_text(action_spec.get('text_key', ''), 
                                   action_spec.get('text', 'Action'))
        
        action = QAction(text)
        
        if 'id' in action_spec:
            action.setObjectName(action_spec['id'])
        
        if 'icon' in action_spec:
            icon_text = self.design.get_icon_text(action_spec['icon'])
            if icon_text:
                action.setText(f"{icon_text} {text}")
        
        if 'shortcut' in action_spec:
            action.setShortcut(action_spec['shortcut'])
        
        if 'checkable' in action_spec:
            action.setCheckable(action_spec['checkable'])
        
        if 'checked' in action_spec:
            action.setChecked(action_spec['checked'])
        
        if 'enabled' in action_spec:
            action.setEnabled(action_spec['enabled'])
        
        return action
    
    # Layout Creators
    
    def create_layout_from_spec(self, spec: Dict[str, Any]) -> Optional[QVBoxLayout]:
        """Create a layout from specification."""
        return self.design.create_layout(spec)
    
    # Utility Methods
    
    def configure_widget(self, widget: QWidget, config: Dict[str, Any]):
        """Configure widget properties (non-visual)."""
        # Set functional properties only
        if 'enabled' in config:
            widget.setEnabled(config['enabled'])
        
        if 'visible' in config:
            widget.setVisible(config['visible'])
        
        if 'checkable' in config and hasattr(widget, 'setCheckable'):
            widget.setCheckable(config['checkable'])
        
        if 'checked' in config and hasattr(widget, 'setChecked'):
            widget.setChecked(config['checked'])
        
        if 'text' in config and hasattr(widget, 'setText'):
            widget.setText(config['text'])
        
        if 'tooltip' in config:
            widget.setToolTip(config['tooltip'])
        
        if 'editable' in config and hasattr(widget, 'setEditable'):
            widget.setEditable(config['editable'])
        
        if 'read_only' in config and hasattr(widget, 'setReadOnly'):
            widget.setReadOnly(config['read_only'])
        
        # Set data properties
        if 'user_data' in config:
            widget.setProperty('user_data', config['user_data'])
    
    def create_tree_item(self, text: str, data: Any = None, 
                        icon_name: str = None) -> QTreeWidgetItem:
        """Create a tree widget item."""
        item = QTreeWidgetItem([text])
        
        if data is not None:
            item.setData(0, Qt.ItemDataRole.UserRole, data)
        
        if icon_name:
            icon_text = self.design.get_icon_text(icon_name)
            if icon_text:
                item.setText(0, f"{icon_text} {text}")
        
        return item
    
    def create_list_item(self, text: str, data: Any = None,
                        icon_name: str = None) -> QListWidgetItem:
        """Create a list widget item."""
        if icon_name:
            icon_text = self.design.get_icon_text(icon_name)
            if icon_text:
                text = f"{icon_text} {text}"
        
        item = QListWidgetItem(text)
        
        if data is not None:
            item.setData(Qt.ItemDataRole.UserRole, data)
        
        return item
    
    def create_label(self, text: str, widget_id: str = None) -> QLabel:
        """Create a label widget."""
        label = QLabel(text)
        if widget_id:
            label.setObjectName(widget_id)
        return label
    
    def create_button(self, text: str, widget_id: str = None) -> QPushButton:
        """Create a button widget."""
        button = QPushButton(text)
        if widget_id:
            button.setObjectName(widget_id)
        return button
    
    def create_separator(self, widget_id: str = None) -> QFrame:
        """Create a separator widget."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        if widget_id:
            separator.setObjectName(widget_id)
        return separator