# ========================================
# tray_minimal.py (100 lines)
# ========================================
"""Minimal system tray for PinPoint - structural only."""

import sys
from pathlib import Path
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QSettings


class MinimalSystemTray(QSystemTrayIcon):
    """Minimal system tray - just essential functions."""
    
    def __init__(self, app, manager, main_window, parent=None):
        super().__init__(parent)
        self.app = app
        self.manager = manager
        self.main_window = main_window
        self.settings = QSettings("PinPoint", "PinPoint")
        
        # Set icon
        icon_path = Path(__file__).parent / "assets/icon.png"
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        
        # Create minimal menu
        self.create_menu()
        
        # Connect activation
        self.activated.connect(self.on_activated)
        
    def create_menu(self):
        """Create minimal context menu."""
        self.menu = QMenu()
        
        # Show/Hide main window
        show_action = QAction("Show/Hide Studio", self)
        show_action.triggered.connect(self.toggle_main_window)
        self.menu.addAction(show_action)
        
        # Project first layout (if any)
        self.menu.addSeparator()
        project_action = QAction("Project Layout", self)
        project_action.triggered.connect(self.project_first_layout)
        self.menu.addAction(project_action)
        
        # Clear projected tiles
        clear_action = QAction("Clear All Tiles", self)
        clear_action.triggered.connect(self.clear_tiles)
        self.menu.addAction(clear_action)
        
        # Quit
        self.menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(quit_action)
        
        self.setContextMenu(self.menu)
        
    def on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == self.ActivationReason.Trigger:  # Left click
            self.toggle_main_window()
            
    def toggle_main_window(self):
        """Toggle main window visibility."""
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
    def project_first_layout(self):
        """Project the first available layout."""
        layouts = self.manager.storage.load_data().get("layouts", [])
        if layouts:
            self.manager.project_layout(layouts[0]['id'], 0)
            
    def clear_tiles(self):
        """Clear all projected tiles."""
        self.manager.clear_live_tiles()
        
    def quit_app(self):
        """Quit the application."""
        self.manager.on_app_quit()
        self.app.quit()
