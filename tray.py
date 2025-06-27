# pinpoint/tray.py

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from pathlib import Path

class SystemTray(QSystemTrayIcon):
    """The SystemTray icon and menu for the application."""

    def __init__(self, app, manager, main_window, parent=None):
        super().__init__(parent)
        self.app = app
        self.manager = manager
        self.main_window = main_window

        icon_path = Path(__file__).parent / "assets/icon.png"
        self.setIcon(QIcon(str(icon_path)))

        self.menu = QMenu()
        quit_action = QAction("Quit PinPoint", self)
        quit_action.triggered.connect(self.app.quit)
        self.menu.addAction(quit_action)
        self.setContextMenu(self.menu)

        self.setToolTip("PinPoint")
        self.activated.connect(self.on_activated)

    def on_activated(self, reason):
        """Handles clicks on the tray icon."""
        # Show the main window on a left-click (Trigger)
        if reason == self.ActivationReason.Trigger:
            # Make the window visible
            self.main_window.show()

            # --- NEW LINE ---
            # Explicitly schedule a repaint of the window and all its children.
            # This should fix the graphical glitch.
            self.main_window.update()
            
            # Raise the window to the top and activate it.
            self.main_window.raise_() 
            self.main_window.activateWindow()