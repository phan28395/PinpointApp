# In pinpoint/main.py

import sys
from PySide6.QtWidgets import QApplication

from .tile_manager import TileManager
from .tray import SystemTray
from .main_window import MainWindow # <-- NEW IMPORT

def main():
    """Initializes and runs the PinPoint application."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Create instances of our main components
    manager = TileManager()
    main_window = MainWindow(manager) # <-- CREATE THE MAIN WINDOW
    
    # We now pass the main_window to the tray, so it can control it
    tray = SystemTray(app, manager, main_window) 
    
    tray.show()
    main_window.show() # <-- SHOW THE MAIN WINDOW ON STARTUP

    print("PinPoint Studio is running.")
    return app.exec()