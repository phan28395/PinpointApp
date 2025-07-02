# ========================================
# main_window_minimal.py (150 lines)
# ========================================
"""Minimal main window for PinPoint - structural only."""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QListWidget, QListWidgetItem, 
                              QSplitter, QLabel)
from PySide6.QtCore import Qt, Signal


class MinimalMainWindow(QMainWindow):
    """Minimal main window - just essential layout and tile management."""
    
    layout_selected = Signal(str)
    tile_selected = Signal(str)
    
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        
        self.setWindowTitle("PinPoint Studio - Minimal")
        self.setGeometry(100, 100, 800, 600)
        
        self.create_ui()
        self.load_data()
        
        # Connect manager signals
        self.manager.layouts_changed.connect(self.load_layouts)
        self.manager.tiles_changed.connect(self.load_tiles)
        
    def create_ui(self):
        """Create minimal UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Lists
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Layout list
        left_layout.addWidget(QLabel("Layouts:"))
        self.layout_list = QListWidget()
        self.layout_list.itemClicked.connect(self.on_layout_clicked)
        left_layout.addWidget(self.layout_list)
        
        # Layout buttons
        layout_buttons = QHBoxLayout()
        new_layout_btn = QPushButton("New Layout")
        new_layout_btn.clicked.connect(self.create_layout)
        delete_layout_btn = QPushButton("Delete")
        delete_layout_btn.clicked.connect(self.delete_layout)
        layout_buttons.addWidget(new_layout_btn)
        layout_buttons.addWidget(delete_layout_btn)
        left_layout.addLayout(layout_buttons)
        
        # Tile list
        left_layout.addWidget(QLabel("Tiles:"))
        self.tile_list = QListWidget()
        self.tile_list.itemClicked.connect(self.on_tile_clicked)
        left_layout.addWidget(self.tile_list)
        
        # Tile buttons
        tile_buttons = QHBoxLayout()
        new_tile_btn = QPushButton("New Tile")
        new_tile_btn.clicked.connect(self.create_tile)
        delete_tile_btn = QPushButton("Delete")
        delete_tile_btn.clicked.connect(self.delete_tile)
        tile_buttons.addWidget(new_tile_btn)
        tile_buttons.addWidget(delete_tile_btn)
        left_layout.addLayout(tile_buttons)
        
        # Right panel - Placeholder for editors
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.addWidget(QLabel("Select a layout or tile to edit"))
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
    def load_data(self):
        """Load layouts and tiles."""
        self.load_layouts()
        self.load_tiles()
        
    def load_layouts(self):
        """Load layout list."""
        self.layout_list.clear()
        layouts = self.manager.storage.load_data().get("layouts", [])
        for layout in layouts:
            item = QListWidgetItem(layout.get('name', 'Unnamed'))
            item.setData(Qt.UserRole, layout['id'])
            self.layout_list.addItem(item)
            
    def load_tiles(self):
        """Load tile list."""
        self.tile_list.clear()
        tiles = self.manager.storage.load_data().get("tiles", [])
        for tile in tiles:
            item = QListWidgetItem(f"{tile.get('name', 'Unnamed')} ({tile.get('tile_type', 'unknown')})")
            item.setData(Qt.UserRole, tile['id'])
            self.tile_list.addItem(item)
            
    def on_layout_clicked(self, item):
        """Handle layout selection."""
        layout_id = item.data(Qt.UserRole)
        self.layout_selected.emit(layout_id)
        
    def on_tile_clicked(self, item):
        """Handle tile selection."""
        tile_id = item.data(Qt.UserRole)
        self.tile_selected.emit(tile_id)
        
    def create_layout(self):
        """Create new layout."""
        self.manager.create_new_layout()
        
    def delete_layout(self):
        """Delete selected layout."""
        current = self.layout_list.currentItem()
        if current:
            layout_id = current.data(Qt.UserRole)
            self.manager.delete_layout(layout_id)
            
    def create_tile(self):
        """Create new tile."""
        # Create a simple note tile
        self.manager.create_new_tile("note")
        
    def delete_tile(self):
        """Delete selected tile."""
        current = self.tile_list.currentItem()
        if current:
            tile_id = current.data(Qt.UserRole)
            self.manager.delete_tile(tile_id)
            
    def closeEvent(self, event):
        """Handle window close."""
        if self.manager.shutting_down:
            event.accept()
        else:
            event.ignore()
            self.hide()