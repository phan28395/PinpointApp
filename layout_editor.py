
# ========================================
# layout_editor_minimal.py (200 lines)
# ========================================
"""Minimal layout editor for PinPoint - structural only."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                              QLabel, QPushButton, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal


class MinimalLayoutEditor(QWidget):
    """Minimal layout editor - just tile arrangement basics."""
    
    def __init__(self, layout_data, manager, parent=None):
        super().__init__(parent)
        self.layout_data = layout_data
        self.manager = manager
        
        self.create_ui()
        self.load_data()
        
    def create_ui(self):
        """Create minimal UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel(f"Layout: {self.layout_data.get('name', 'Unnamed')}"))
        
        # Display selector
        header.addWidget(QLabel("Display:"))
        self.display_combo = QComboBox()
        self.display_combo.currentIndexChanged.connect(self.on_display_changed)
        header.addWidget(self.display_combo)
        
        # Project button
        project_btn = QPushButton("Project Layout")
        project_btn.clicked.connect(self.project_layout)
        header.addWidget(project_btn)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Main content - two lists
        content = QHBoxLayout()
        
        # Available tiles
        available_panel = QVBoxLayout()
        available_panel.addWidget(QLabel("Available Tiles:"))
        self.available_list = QListWidget()
        available_panel.addWidget(self.available_list)
        
        # Add button
        add_btn = QPushButton("Add to Layout →")
        add_btn.clicked.connect(self.add_tile_to_layout)
        available_panel.addWidget(add_btn)
        
        # Layout tiles
        layout_panel = QVBoxLayout()
        layout_panel.addWidget(QLabel("Tiles in Layout:"))
        self.layout_list = QListWidget()
        layout_panel.addWidget(self.layout_list)
        
        # Remove button
        remove_btn = QPushButton("← Remove from Layout")
        remove_btn.clicked.connect(self.remove_tile_from_layout)
        layout_panel.addWidget(remove_btn)
        
        content.addLayout(available_panel)
        content.addLayout(layout_panel)
        
        layout.addLayout(content)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def load_data(self):
        """Load displays and tiles."""
        # Load displays
        self.display_combo.clear()
        displays = self.manager.display_manager.get_all_displays()
        for i, display in enumerate(displays):
            self.display_combo.addItem(f"Display {i}: {display['width']}x{display['height']}")
            
        # Set current display
        target_display = self.layout_data.get("display_settings", {}).get("target_display", 0)
        self.display_combo.setCurrentIndex(target_display)
        
        # Load tiles
        self.load_tiles()
        
    def load_tiles(self):
        """Load available and layout tiles."""
        # Clear lists
        self.available_list.clear()
        self.layout_list.clear()
        
        # Get all tiles
        all_tiles = self.manager.storage.load_data().get("tiles", [])
        
        # Get tiles in this layout
        layout_tiles = self.layout_data.get("tile_instances", [])
        layout_tile_ids = [t.get("tile_id") for t in layout_tiles]
        
        # Populate lists
        for tile in all_tiles:
            item = QListWidgetItem(f"{tile.get('name', 'Unnamed')} ({tile.get('tile_type', 'unknown')})")
            item.setData(Qt.UserRole, tile['id'])
            
            if tile['id'] not in layout_tile_ids:
                self.available_list.addItem(item)
                
        for instance in layout_tiles:
            tile = next((t for t in all_tiles if t['id'] == instance['tile_id']), None)
            if tile:
                item = QListWidgetItem(f"{tile.get('name', 'Unnamed')} at ({instance['x']}, {instance['y']})")
                item.setData(Qt.UserRole, instance['instance_id'])
                self.layout_list.addItem(item)
                
    def on_display_changed(self, index):
        """Handle display change."""
        self.manager.update_layout_display(self.layout_data['id'], index)
        self.status_label.setText(f"Display changed to {index}")
        
    def add_tile_to_layout(self):
        """Add selected tile to layout."""
        current = self.available_list.currentItem()
        if current:
            tile_id = current.data(Qt.UserRole)
            # Add at default position
            self.manager.add_tile_to_layout(self.layout_data['id'], tile_id, 100, 100)
            self.load_tiles()
            self.status_label.setText("Tile added to layout")
            
    def remove_tile_from_layout(self):
        """Remove selected tile from layout."""
        current = self.layout_list.currentItem()
        if current:
            instance_id = current.data(Qt.UserRole)
            self.manager.remove_tile_from_layout(self.layout_data['id'], instance_id)
            self.load_tiles()
            self.status_label.setText("Tile removed from layout")
            
    def project_layout(self):
        """Project the current layout."""
        display_index = self.display_combo.currentIndex()
        self.manager.project_layout(self.layout_data['id'], display_index)
        self.status_label.setText(f"Layout projected to display {display_index}")