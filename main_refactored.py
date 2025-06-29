# pinpoint/main_refactored.py
"""
Refactored main entry point that initializes the design layer.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from .tile_manager_refactored import TileManager  # This will also need refactoring
from .tray_refactored import SystemTray  # This will also need refactoring
from .main_window_refactored import MainWindow
from .design_layer import DesignLayer


def main():
    """Initializes and runs the PinPoint application with design layer."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Determine design path
    # Users can have custom designs in their home directory
    user_design_path = Path.home() / ".pinpoint" / "designs"
    default_design_path = Path(__file__).parent / "designs"
    
    # Use user design if exists, otherwise use default
    if user_design_path.exists() and (user_design_path / "main.json").exists():
        design_path = user_design_path
        print(f"Loading user design from: {design_path}")
    else:
        design_path = default_design_path
        print(f"Loading default design from: {design_path}")
    
    # Create design layer
    design_layer = DesignLayer(design_path)
    
    # Apply global application style
    app_style = design_layer.get_style("QApplication", "application")
    if app_style:
        app.setStyleSheet(app_style)
    
    # Create instances of main components
    manager = TileManager(design_layer)  # Pass design layer to manager
    main_window = MainWindow(manager, design_layer)
    
    # Create system tray (also needs design layer)
    tray = SystemTray(app, manager, main_window, design_layer)
    
    tray.show()
    main_window.show()
    
    print("PinPoint Studio is running with design layer.")
    print(f"Design version: {design_layer.design_data.get('version', 'unknown')}")
    
    return app.exec()