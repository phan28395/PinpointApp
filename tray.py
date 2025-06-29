# pinpoint/tray.py

from PySide6.QtWidgets import (QSystemTrayIcon, QMenu, QWidgetAction, QWidget, 
                              QHBoxLayout, QSlider, QSpinBox, QLabel
                              )
from PySide6.QtGui import QIcon, QAction, QKeySequence, QActionGroup
from PySide6.QtCore import Qt, QSettings, Signal, QObject, QTimer
from pathlib import Path
import sys


class PersistentMenu(QMenu):
    """A menu that stays open when actions are triggered."""
    
    def __init__(self, parent=None, tray_instance=None):
        super().__init__(parent)
        self.should_stay_open = True
        self.tray_instance = tray_instance
        self.is_topmost_set = False
        
        # Timer to check if we need to regain top position (less aggressive)
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_if_need_raise)
        
        # Single-shot timer for delayed forcing to top
        self.force_timer = QTimer()
        self.force_timer.setSingleShot(True)
        self.force_timer.timeout.connect(self.force_to_top_once)
    
    def showEvent(self, event):
        """When menu shows, set it to topmost once."""
        super().showEvent(event)
        self.force_to_top_once()
        # Start monitoring but less aggressively (every 1 second)
        self.monitor_timer.start(1000)
    
    def hideEvent(self, event):
        """When menu hides, stop monitoring."""
        super().hideEvent(event)
        self.monitor_timer.stop()
        self.force_timer.stop()
        self.is_topmost_set = False
    
    def check_if_need_raise(self):
        """Check if we actually need to raise (only if not currently active)."""
        if self.isVisible() and not self.isActiveWindow():
            # Only raise if we've lost focus/position
            self.force_timer.stop()
            self.force_timer.start(50)  # Small delay to avoid flicker
    
    def force_to_top_once(self):
        """Force this menu to top, but only once per call."""
        if not self.isVisible():
            return
            
        # Set topmost using Windows API (more stable than raise_())
        try:
            import platform
            if platform.system() == "Windows":
                import ctypes
                hwnd = int(self.winId())
                HWND_TOPMOST = -1
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040
                
                if not self.is_topmost_set:
                    ctypes.windll.user32.SetWindowPos(
                        hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                    )
                    self.is_topmost_set = True
            else:
                # Fallback for non-Windows platforms
                if not self.is_topmost_set:
                    self.raise_()
                    self.is_topmost_set = True
        except Exception:
            # Final fallback
            if not self.is_topmost_set:
                self.raise_()
                self.is_topmost_set = True
    
    def mouseReleaseEvent(self, event):
        """Override to prevent menu from closing on action clicks."""
        action = self.actionAt(event.pos())
        if action and action.isEnabled() and self.should_stay_open:
            # Check if this action should close the menu
            if hasattr(action, 'should_close_menu') and action.should_close_menu:
                # This action wants to close the menu
                super().mouseReleaseEvent(event)
                return
            
            # Trigger the action without closing the menu
            action.trigger()
            # Don't call parent's mouseReleaseEvent to prevent closing
            event.accept()
            
            # Only force back to top if we might have lost position
            if not self.isActiveWindow():
                self.force_timer.stop()
                self.force_timer.start(100)
        else:
            # For non-layout actions or when we want normal behavior
            super().mouseReleaseEvent(event)
    
    def close_menu(self):
        """Manually close the menu."""
        self.monitor_timer.stop()
        self.force_timer.stop()
        self.should_stay_open = False
        self.close()


class OpacityWidget(QWidget):
    """Custom widget for opacity control in the menu."""
    
    opacity_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        
        # Label
        layout.addWidget(QLabel("Opacity:"))
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(10, 100)  # 10% to 100%
        self.slider.setValue(100)
        self.slider.setFixedWidth(100)
        layout.addWidget(self.slider)
        
        # SpinBox
        self.spinbox = QSpinBox()
        self.spinbox.setRange(10, 100)
        self.spinbox.setValue(100)
        self.spinbox.setSuffix("%")
        self.spinbox.setFixedWidth(60)
        layout.addWidget(self.spinbox)
        
        # Connect slider and spinbox
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.opacity_changed.emit)


class SystemTray(QSystemTrayIcon):
    """Enhanced system tray with advanced menu features."""
    
    def __init__(self, app, manager, main_window, parent=None):
        super().__init__(parent)
        self.app = app
        self.manager = manager
        self.main_window = main_window
        
        # Settings
        self.settings = QSettings("PinPoint", "PinPoint")
        
        # State tracking
        self.tiles_visible = True
        self.tiles_interactive = True
        self.global_opacity = 100
        
        # Project menu state
        self.show_all_layouts = False
        
        # Set icon
        icon_path = Path(__file__).parent / "assets/icon.png"
        self.setIcon(QIcon(str(icon_path)))
        
        # Create menu
        self.create_menu()
        
        # Set tooltip
        self.setToolTip("PinPoint - Click to show/hide studio")
        
        # Connect activation signal
        self.activated.connect(self.on_activated)
        
        # Load settings
        self.load_settings()
        
        # Timer to refresh menus periodically
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_project_menu)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def create_menu(self):
        """Create the enhanced context menu."""
        self.menu = PersistentMenu(tray_instance=self)
        
        # Project Layout submenu (also persistent)
        self.project_menu = PersistentMenu(self.menu, tray_instance=self)
        self.project_menu.setTitle("📐 Project Layout")
        self.menu.addMenu(self.project_menu)
        self.update_project_menu()
        
        self.menu.addSeparator()
        
        # Show/Hide All Projected Tiles
        self.toggle_tiles_action = QAction("👁️ Show/Hide All Tiles", self)
        self.toggle_tiles_action.setCheckable(True)
        self.toggle_tiles_action.setChecked(True)
        self.toggle_tiles_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        self.toggle_tiles_action.triggered.connect(self.toggle_all_tiles)
        self.menu.addAction(self.toggle_tiles_action)
        
        # Make Interactive/Non-interactive
        self.toggle_interactive_action = QAction("🖱️ Make Interactive", self)
        self.toggle_interactive_action.setCheckable(True)
        self.toggle_interactive_action.setChecked(True)
        self.toggle_interactive_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.toggle_interactive_action.triggered.connect(self.toggle_interactive)
        self.menu.addAction(self.toggle_interactive_action)
        
        # Switch to Another Monitor submenu (also persistent)
        self.monitor_menu = PersistentMenu(self.menu, tray_instance=self)
        self.monitor_menu.setTitle("🖥️ Switch Monitor")
        self.monitor_menu.setEnabled(False)  # Will be enabled when tiles are projected
        self.menu.addMenu(self.monitor_menu)
        self.update_monitor_menu()
        
        self.menu.addSeparator()
        
        # Opacity control
        self.opacity_widget = OpacityWidget()
        self.opacity_widget.opacity_changed.connect(self.set_global_opacity)
        opacity_action = QWidgetAction(self)
        opacity_action.setDefaultWidget(self.opacity_widget)
        self.menu.addAction(opacity_action)
        
        self.menu.addSeparator()
        
        # Start at Startup
        self.startup_action = QAction("🚀 Start at Startup", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.get_startup_enabled())
        self.startup_action.triggered.connect(self.toggle_startup)
        self.menu.addAction(self.startup_action)
        
        # Settings
        self.settings_action = QAction("⚙️ Settings...", self)
        self.settings_action.triggered.connect(self.show_settings)
        self.settings_action.setEnabled(False)  # For future implementation
        # Mark settings as should close menu
        self.settings_action.should_close_menu = True
        self.menu.addAction(self.settings_action)
        
        self.menu.addSeparator()
        
        # Close Menu option
        close_action = QAction("✕ Close Menu", self)
        close_action.triggered.connect(self.menu.close_menu)
        close_action.should_close_menu = True
        self.menu.addAction(close_action)
        
        # Quit
        quit_action = QAction("❌ Quit PinPoint", self)
        quit_action.triggered.connect(self.quit_app)
        quit_action.should_close_menu = True
        self.menu.addAction(quit_action)
        
        # Set the menu
        self.setContextMenu(self.menu)
        
    def update_project_menu(self):
        """Update the project layout submenu with expandable list."""
        self.project_menu.clear()
        
        # Get all layouts
        layouts = self.manager.storage.load_data().get("layouts", [])
        
        if not layouts:
            no_layouts_action = QAction("No layouts available", self)
            no_layouts_action.setEnabled(False)
            self.project_menu.addAction(no_layouts_action)
            return
            
        # Sort layouts by name
        sorted_layouts = sorted(layouts, key=lambda x: x.get('name', ''))
        
        # Determine how many to show
        if self.show_all_layouts:
            layouts_to_show = sorted_layouts
            expand_text = "▲ Show Less"
        else:
            layouts_to_show = sorted_layouts[:5]  # Show first 5
            expand_text = "▼ Show All" if len(sorted_layouts) > 5 else None
        
        # Add layout actions
        for layout in layouts_to_show:
            # Get display info
            display_info = self.manager.get_layout_display_info(layout['id'])
            display_name = display_info.get("display_name", "Unknown")
            
            action_text = f"{layout['name']} → {display_name}"
            action = QAction(action_text, self)
            action.setData(layout['id'])
            action.triggered.connect(lambda checked, lid=layout['id']: self.quick_project_layout(lid))
            self.project_menu.addAction(action)
        
        # Add expand/collapse option if there are more than 5 layouts
        if len(sorted_layouts) > 5:
            self.project_menu.addSeparator()
            expand_action = QAction(expand_text, self)
            expand_action.triggered.connect(self.toggle_layout_list)
            self.project_menu.addAction(expand_action)
            
        # Add separator and management options
        self.project_menu.addSeparator()
        
        # Manage Layouts option
        manage_action = QAction("⚙️ Manage Layouts...", self)
        manage_action.triggered.connect(self.show_main_window_and_close_menu)
        manage_action.should_close_menu = True
        self.project_menu.addAction(manage_action)
        
        # Close submenu option
        close_submenu_action = QAction("✕ Close Menu", self)
        close_submenu_action.triggered.connect(self.project_menu.close_menu)
        close_submenu_action.should_close_menu = True
        self.project_menu.addAction(close_submenu_action)
        
    def toggle_layout_list(self):
        """Toggle between showing few layouts vs all layouts."""
        self.show_all_layouts = not self.show_all_layouts
        self.update_project_menu()
        
    def update_monitor_menu(self):
        """Update the monitor switch submenu."""
        self.monitor_menu.clear()
        
        # Create action group for exclusive selection
        monitor_group = QActionGroup(self)
        
        # Get current display
        current_display_index = self.manager.display_manager.selected_display_index or 0
        
        # Add action for each display
        for i, display in enumerate(self.manager.display_manager.displays):
            action = QAction(display.display_name, self)
            action.setCheckable(True)
            action.setChecked(i == current_display_index)
            action.setData(i)
            action.triggered.connect(lambda checked, idx=i: self.switch_to_monitor(idx))
            monitor_group.addAction(action)
            self.monitor_menu.addAction(action)
            
        # Add close submenu option
        if self.manager.display_manager.displays:
            self.monitor_menu.addSeparator()
            close_submenu_action = QAction("✕ Close Menu", self)
            close_submenu_action.triggered.connect(self.monitor_menu.close_menu)
            close_submenu_action.should_close_menu = True
            self.monitor_menu.addAction(close_submenu_action)
            
    def quick_project_layout(self, layout_id: str):
        """Quickly project a layout from the tray menu."""
        # Get layout's preferred display
        display_info = self.manager.get_layout_display_info(layout_id)
        display_index = display_info.get("target_display", 0)
        
        # Project the layout
        self.manager.project_layout(layout_id, display_index)
        
        # Enable monitor switching
        self.monitor_menu.setEnabled(True)
        self.update_monitor_menu()
        
        # Update interactive state
        self.update_tiles_interactive_state()
        
        # Update tooltip
        layout_data = self.manager.get_layout_by_id(layout_id)
        if layout_data:
            layout_name = layout_data.get('name', 'Layout')
            self.setToolTip(f"PinPoint - Projecting: {layout_name}")
        
    def show_main_window_and_close_menu(self):
        """Show the main window and close all menus."""
        self.project_menu.close_menu()
        self.menu.close_menu()
        self.show_main_window()
        
    def show_main_window(self):
        """Show the main window for layout management."""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
    def toggle_all_tiles(self):
        """Show or hide all projected tiles."""
        self.tiles_visible = not self.tiles_visible
        
        for tile_window in self.manager.active_live_tiles.values():
            if self.tiles_visible:
                tile_window.show()
            else:
                tile_window.hide()
                
        # Update action text
        if self.tiles_visible:
            self.toggle_tiles_action.setText("👁️ Hide All Tiles")
        else:
            self.toggle_tiles_action.setText("👁️ Show All Tiles")
            
    def toggle_interactive(self):
        """Toggle whether tiles are interactive or click-through."""
        self.tiles_interactive = not self.tiles_interactive
        
        # Update action text based on new state
        if self.tiles_interactive:
            self.toggle_interactive_action.setText("🖱️ Make Non-interactive")
            flag_value = False
        else:
            self.toggle_interactive_action.setText("🖱️ Make Interactive")
            flag_value = True
            
        # Apply to all tiles
        for tile_window in self.manager.active_live_tiles.values():
            tile_window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, flag_value)
            
    def update_tiles_interactive_state(self):
        """Update the interactive state of newly projected tiles."""
        if not self.tiles_interactive:
            for tile_window in self.manager.active_live_tiles.values():
                tile_window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                
    def switch_to_monitor(self, display_index: int):
        """Switch all projected tiles to another monitor."""
        # Get the currently projected layout (if any)
        if not self.manager.active_live_tiles:
            return
            
        # We need to find which layout is currently projected
        # For now, we'll re-project to the new display
        # This is a simplified implementation
        
        # Clear current tiles
        self.manager.clear_live_tiles()
        
        # Update display selection
        self.manager.display_manager.select_display(display_index)
        
        # Note: In a full implementation, you'd track the current layout
        # and re-project it to the new display
        
        self.update_monitor_menu()
        
    def set_global_opacity(self, opacity: int):
        """Set opacity for all projected tiles."""
        self.global_opacity = opacity
        opacity_float = opacity / 100.0
        
        for tile_window in self.manager.active_live_tiles.values():
            tile_window.setWindowOpacity(opacity_float)
            
        # Save setting
        self.settings.setValue("global_opacity", opacity)
        
    def get_startup_enabled(self) -> bool:
        """Check if auto-start is enabled."""
        return self.settings.value("start_at_startup", False, type=bool)
        
    def toggle_startup(self):
        """Toggle start at startup setting."""
        enabled = not self.get_startup_enabled()
        self.settings.setValue("start_at_startup", enabled)
        
        # Platform-specific startup registration
        if enabled:
            self.register_startup()
        else:
            self.unregister_startup()
            
    def register_startup(self):
        """Register the application to start at system startup."""
        import platform
        import os
        
        if platform.system() == "Windows":
            import winreg
            
            app_path = os.path.abspath(sys.argv[0])
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "PinPoint", 0, winreg.REG_SZ, app_path)
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Failed to register startup: {e}")
                
        # TODO: Add macOS and Linux support
        
    def unregister_startup(self):
        """Unregister the application from system startup."""
        import platform
        
        if platform.system() == "Windows":
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "PinPoint")
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Failed to unregister startup: {e}")
                
    def show_settings(self):
        """Show the settings dialog (for future implementation)."""
        # TODO: Implement settings dialog
        pass
        
    def load_settings(self):
        """Load saved settings."""
        # Load opacity
        opacity = self.settings.value("global_opacity", 100, type=int)
        self.opacity_widget.slider.setValue(opacity)
        
    def quit_app(self):
        """Quit the application."""
        # Notify manager about shutdown
        self.manager.on_app_quit()
        # Quit the application
        self.app.quit()
        
    def on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == self.ActivationReason.Trigger:  # Left click
            # Toggle main window visibility
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
                self.main_window.update()
                self.main_window.raise_()
                self.main_window.activateWindow()