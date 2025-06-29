# pinpoint/tray_refactored.py
"""
Refactored system tray with complete separation of functionality and design.
All visual aspects are handled by the design layer.
"""

from PySide6.QtWidgets import (QSystemTrayIcon, QMenu, QWidgetAction, QWidget, 
                              QHBoxLayout, QSlider, QSpinBox, QLabel,
                              QVBoxLayout, QAction)
from PySide6.QtGui import QIcon, QActionGroup
from PySide6.QtCore import Qt, QSettings, Signal, QObject, QTimer
from pathlib import Path
import sys

from .design_layer import DesignLayer
from .widget_factory import WidgetFactory


class PersistentMenu(QMenu):
    """A menu that stays open when actions are triggered."""
    
    def __init__(self, parent=None, design_layer=None):
        super().__init__(parent)
        self.should_stay_open = True
        self.design = design_layer
        
        # Set object name for styling
        self.setObjectName("persistent_menu")
        
        # Timer for maintaining position
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._maintain_position)
        
    def showEvent(self, event):
        """When menu shows, apply design and start position maintenance."""
        super().showEvent(event)
        if self.design:
            self.design.apply_design(self)
        self.position_timer.start(1000)  # Check every second
        
    def hideEvent(self, event):
        """When menu hides, stop position maintenance."""
        super().hideEvent(event)
        self.position_timer.stop()
        
    def _maintain_position(self):
        """Maintain menu position if needed."""
        if self.isVisible() and not self.isActiveWindow():
            self.raise_()
            
    def mouseReleaseEvent(self, event):
        """Override to prevent menu from closing on action clicks."""
        action = self.actionAt(event.pos())
        if action and action.isEnabled() and self.should_stay_open:
            # Check if this action should close the menu
            if hasattr(action, 'should_close_menu') and action.should_close_menu:
                super().mouseReleaseEvent(event)
                return
                
            # Trigger the action without closing
            action.trigger()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def close_menu(self):
        """Manually close the menu."""
        self.position_timer.stop()
        self.should_stay_open = False
        self.close()


class OpacityControl(QWidget):
    """Opacity control widget with no hardcoded styling."""
    
    opacity_changed = Signal(int)
    
    def __init__(self, design_layer, parent=None):
        super().__init__(parent)
        self.design = design_layer
        self.setObjectName("opacity_control")
        
        # Create structure
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        self.label = QLabel()
        self.label.setObjectName("opacity_label")
        self.label.setText(self.design.get_text("menu.opacity", "Opacity:"))
        layout.addWidget(self.label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setObjectName("opacity_slider")
        self.slider.setRange(10, 100)
        self.slider.setValue(100)
        layout.addWidget(self.slider)
        
        # SpinBox
        self.spinbox = QSpinBox()
        self.spinbox.setObjectName("opacity_spinbox")
        self.spinbox.setRange(10, 100)
        self.spinbox.setValue(100)
        self.spinbox.setSuffix("%")
        layout.addWidget(self.spinbox)
        
        # Connect without styling
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.opacity_changed.emit)


class SystemTray(QSystemTrayIcon):
    """System tray with complete design separation."""
    
    def __init__(self, app, manager, main_window, design_layer: DesignLayer):
        super().__init__()
        self.app = app
        self.manager = manager
        self.main_window = main_window
        self.design = design_layer
        self.factory = WidgetFactory(design_layer)
        
        # Settings (functionality, not appearance)
        self.settings = QSettings("PinPoint", "PinPoint")
        
        # State tracking (functionality)
        self.tiles_visible = True
        self.tiles_interactive = True
        self.global_opacity = 100
        self.show_all_layouts = False
        
        # Set icon from design system
        self._set_tray_icon()
        
        # Create menu structure (no styling)
        self.create_menu()
        
        # Set tooltip from design
        self.setToolTip(self.design.get_text("tray.tooltip", "PinPoint - Click to show/hide studio"))
        
        # Connect signals (functionality only)
        self.activated.connect(self.on_activated)
        
        # Load functional settings
        self.load_settings()
        
        # Timer for menu updates
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_project_menu)
        self.refresh_timer.start(5000)
        
    def _set_tray_icon(self):
        """Set tray icon from design system."""
        # Try to get icon from design system
        icon = self.design.get_icon("tray_icon")
        if icon.isNull():
            # Fallback to file icon
            icon_path = self.design.get_value("assets.tray_icon")
            if icon_path:
                full_path = self.design.design_path / icon_path
                if full_path.exists():
                    icon = QIcon(str(full_path))
            else:
                # Final fallback
                icon_path = Path(__file__).parent / "assets/icon.png"
                if icon_path.exists():
                    icon = QIcon(str(icon_path))
                    
        self.setIcon(icon)
        
    def create_menu(self):
        """Create menu structure without any styling."""
        # Main menu
        self.menu = PersistentMenu(design_layer=self.design)
        self.menu.setObjectName("tray_menu")
        
        # Project Layout submenu
        self.project_menu = PersistentMenu(self.menu, design_layer=self.design)
        self.project_menu.setObjectName("project_submenu")
        self.project_menu.setTitle(self.design.get_text("menu.project_layout", "📐 Project Layout"))
        self.menu.addMenu(self.project_menu)
        self.update_project_menu()
        
        self.menu.addSeparator()
        
        # Show/Hide All Tiles
        self.toggle_tiles_action = self._create_action(
            "toggle_tiles",
            self.design.get_text("menu.show_hide_tiles", "👁️ Show/Hide All Tiles"),
            checkable=True,
            checked=True,
            shortcut="Ctrl+Shift+H"
        )
        self.toggle_tiles_action.triggered.connect(self.toggle_all_tiles)
        self.menu.addAction(self.toggle_tiles_action)
        
        # Make Interactive/Non-interactive
        self.toggle_interactive_action = self._create_action(
            "toggle_interactive",
            self.design.get_text("menu.make_interactive", "🖱️ Make Interactive"),
            checkable=True,
            checked=True,
            shortcut="Ctrl+Shift+I"
        )
        self.toggle_interactive_action.triggered.connect(self.toggle_interactive)
        self.menu.addAction(self.toggle_interactive_action)
        
        # Switch Monitor submenu
        self.monitor_menu = PersistentMenu(self.menu, design_layer=self.design)
        self.monitor_menu.setObjectName("monitor_submenu")
        self.monitor_menu.setTitle(self.design.get_text("menu.switch_monitor", "🖥️ Switch Monitor"))
        self.monitor_menu.setEnabled(False)
        self.menu.addMenu(self.monitor_menu)
        self.update_monitor_menu()
        
        self.menu.addSeparator()
        
        # Opacity control
        self.opacity_widget = OpacityControl(self.design)
        opacity_action = QWidgetAction(self)
        opacity_action.setDefaultWidget(self.opacity_widget)
        self.opacity_widget.opacity_changed.connect(self.set_global_opacity)
        self.menu.addAction(opacity_action)
        
        self.menu.addSeparator()
        
        # Start at Startup
        self.startup_action = self._create_action(
            "start_at_startup",
            self.design.get_text("menu.start_at_startup", "🚀 Start at Startup"),
            checkable=True,
            checked=self.get_startup_enabled()
        )
        self.startup_action.triggered.connect(self.toggle_startup)
        self.menu.addAction(self.startup_action)
        
        # Settings
        self.settings_action = self._create_action(
            "settings",
            self.design.get_text("menu.settings", "⚙️ Settings..."),
            enabled=False  # For future implementation
        )
        self.settings_action.triggered.connect(self.show_settings)
        self.settings_action.should_close_menu = True
        self.menu.addAction(self.settings_action)
        
        self.menu.addSeparator()
        
        # Close Menu
        close_action = self._create_action(
            "close_menu",
            self.design.get_text("menu.close_menu", "✕ Close Menu")
        )
        close_action.triggered.connect(self.menu.close_menu)
        close_action.should_close_menu = True
        self.menu.addAction(close_action)
        
        # Quit
        quit_action = self._create_action(
            "quit",
            self.design.get_text("menu.quit", "❌ Quit PinPoint")
        )
        quit_action.triggered.connect(self.quit_app)
        quit_action.should_close_menu = True
        self.menu.addAction(quit_action)
        
        # Set the menu
        self.setContextMenu(self.menu)
        
    def _create_action(self, object_name: str, text: str, **kwargs) -> QAction:
        """Create an action with no styling."""
        action = QAction(text, self)
        action.setObjectName(object_name)
        
        # Set functional properties only
        if 'checkable' in kwargs:
            action.setCheckable(kwargs['checkable'])
        if 'checked' in kwargs:
            action.setChecked(kwargs['checked'])
        if 'enabled' in kwargs:
            action.setEnabled(kwargs['enabled'])
        if 'shortcut' in kwargs:
            action.setShortcut(kwargs['shortcut'])
            
        return action
        
    def update_project_menu(self):
        """Update project menu with layouts."""
        self.project_menu.clear()
        
        # Get all layouts
        layouts = self.manager.storage.load_data().get("layouts", [])
        
        if not layouts:
            no_layouts_action = self._create_action(
                "no_layouts",
                self.design.get_text("menu.no_layouts", "No layouts available"),
                enabled=False
            )
            self.project_menu.addAction(no_layouts_action)
            return
            
        # Sort layouts
        sorted_layouts = sorted(layouts, key=lambda x: x.get('name', ''))
        
        # Determine how many to show
        if self.show_all_layouts:
            layouts_to_show = sorted_layouts
            expand_text = self.design.get_text("menu.show_less", "▲ Show Less")
        else:
            layouts_to_show = sorted_layouts[:5]
            expand_text = self.design.get_text("menu.show_all", "▼ Show All") if len(sorted_layouts) > 5 else None
            
        # Add layout actions
        for layout in layouts_to_show:
            display_info = self.manager.get_layout_display_info(layout['id'])
            display_name = display_info.get("display_name", "Unknown")
            
            action_text = f"{layout['name']} → {display_name}"
            action = self._create_action(
                f"layout_{layout['id']}",
                action_text
            )
            action.setData(layout['id'])
            action.triggered.connect(lambda checked, lid=layout['id']: self.quick_project_layout(lid))
            self.project_menu.addAction(action)
            
        # Add expand/collapse option
        if len(sorted_layouts) > 5:
            self.project_menu.addSeparator()
            expand_action = self._create_action(
                "expand_layouts",
                expand_text
            )
            expand_action.triggered.connect(self.toggle_layout_list)
            self.project_menu.addAction(expand_action)
            
        # Add management options
        self.project_menu.addSeparator()
        
        manage_action = self._create_action(
            "manage_layouts",
            self.design.get_text("menu.manage_layouts", "⚙️ Manage Layouts...")
        )
        manage_action.triggered.connect(self.show_main_window_and_close_menu)
        manage_action.should_close_menu = True
        self.project_menu.addAction(manage_action)
        
        # Close submenu option
        close_submenu_action = self._create_action(
            "close_submenu",
            self.design.get_text("menu.close_menu", "✕ Close Menu")
        )
        close_submenu_action.triggered.connect(self.project_menu.close_menu)
        close_submenu_action.should_close_menu = True
        self.project_menu.addAction(close_submenu_action)
        
    def update_monitor_menu(self):
        """Update monitor menu."""
        self.monitor_menu.clear()
        
        # Create action group
        monitor_group = QActionGroup(self)
        
        # Get current display
        current_display_index = self.manager.display_manager.selected_display_index or 0
        
        # Add action for each display
        for i, display in enumerate(self.manager.display_manager.displays):
            action = self._create_action(
                f"monitor_{i}",
                display.display_name,
                checkable=True,
                checked=(i == current_display_index)
            )
            action.setData(i)
            action.triggered.connect(lambda checked, idx=i: self.switch_to_monitor(idx))
            monitor_group.addAction(action)
            self.monitor_menu.addAction(action)
            
        # Add close option
        if self.manager.display_manager.displays:
            self.monitor_menu.addSeparator()
            close_action = self._create_action(
                "close_monitor_menu",
                self.design.get_text("menu.close_menu", "✕ Close Menu")
            )
            close_action.triggered.connect(self.monitor_menu.close_menu)
            close_action.should_close_menu = True
            self.monitor_menu.addAction(close_action)
            
    # All functional methods remain the same
    def toggle_layout_list(self):
        """Toggle between showing few/all layouts."""
        self.show_all_layouts = not self.show_all_layouts
        self.update_project_menu()
        
    def quick_project_layout(self, layout_id: str):
        """Project a layout."""
        display_info = self.manager.get_layout_display_info(layout_id)
        display_index = display_info.get("target_display", 0)
        
        self.manager.project_layout(layout_id, display_index)
        self.monitor_menu.setEnabled(True)
        self.update_monitor_menu()
        self.update_tiles_interactive_state()
        
        # Update tooltip
        layout_data = self.manager.get_layout_by_id(layout_id)
        if layout_data:
            layout_name = layout_data.get('name', 'Layout')
            tooltip = self.design.get_text("tray.tooltip_projecting", "PinPoint - Projecting: {layout}")
            self.setToolTip(tooltip.format(layout=layout_name))
            
    def show_main_window_and_close_menu(self):
        """Show main window and close menus."""
        self.project_menu.close_menu()
        self.menu.close_menu()
        self.show_main_window()
        
    def show_main_window(self):
        """Show the main window."""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
    def toggle_all_tiles(self):
        """Toggle visibility of all tiles."""
        self.tiles_visible = not self.tiles_visible
        
        for tile_window in self.manager.active_live_tiles.values():
            if self.tiles_visible:
                tile_window.show()
            else:
                tile_window.hide()
                
        # Update action text from design
        if self.tiles_visible:
            text = self.design.get_text("menu.hide_all_tiles", "👁️ Hide All Tiles")
        else:
            text = self.design.get_text("menu.show_all_tiles", "👁️ Show All Tiles")
        self.toggle_tiles_action.setText(text)
        
    def toggle_interactive(self):
        """Toggle tile interactivity."""
        self.tiles_interactive = not self.tiles_interactive
        
        # Update action text from design
        if self.tiles_interactive:
            text = self.design.get_text("menu.make_non_interactive", "🖱️ Make Non-interactive")
            flag_value = False
        else:
            text = self.design.get_text("menu.make_interactive", "🖱️ Make Interactive")
            flag_value = True
            
        self.toggle_interactive_action.setText(text)
        
        # Apply to all tiles
        for tile_window in self.manager.active_live_tiles.values():
            tile_window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, flag_value)
            
    def update_tiles_interactive_state(self):
        """Update interactive state of tiles."""
        if not self.tiles_interactive:
            for tile_window in self.manager.active_live_tiles.values():
                tile_window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                
    def switch_to_monitor(self, display_index: int):
        """Switch tiles to another monitor."""
        if not self.manager.active_live_tiles:
            return
            
        self.manager.clear_live_tiles()
        self.manager.display_manager.select_display(display_index)
        self.update_monitor_menu()
        
    def set_global_opacity(self, opacity: int):
        """Set opacity for all tiles."""
        self.global_opacity = opacity
        opacity_float = opacity / 100.0
        
        for tile_window in self.manager.active_live_tiles.values():
            tile_window.setWindowOpacity(opacity_float)
            
        self.settings.setValue("global_opacity", opacity)
        
    def get_startup_enabled(self) -> bool:
        """Check if startup is enabled."""
        return self.settings.value("start_at_startup", False, type=bool)
        
    def toggle_startup(self):
        """Toggle startup setting."""
        enabled = not self.get_startup_enabled()
        self.settings.setValue("start_at_startup", enabled)
        
        if enabled:
            self.register_startup()
        else:
            self.unregister_startup()
            
    def register_startup(self):
        """Register for system startup."""
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
                
    def unregister_startup(self):
        """Unregister from system startup."""
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
        """Show settings dialog."""
        # TODO: Implement settings dialog
        pass
        
    def load_settings(self):
        """Load saved settings."""
        opacity = self.settings.value("global_opacity", 100, type=int)
        self.opacity_widget.slider.setValue(opacity)
        
    def quit_app(self):
        """Quit the application."""
        self.manager.on_app_quit()
        self.app.quit()
        
    def on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == self.ActivationReason.Trigger:  # Left click
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
                self.main_window.update()
                self.main_window.raise_()
                self.main_window.activateWindow()