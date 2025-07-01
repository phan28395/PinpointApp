# main.py
"""
PinPoint main entry point - Updated for new architecture.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app import get_app
from platform_support import get_platform


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PinPoint - Floating Widget Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pinpoint                    # Start with GUI
  pinpoint --no-gui           # Start in headless mode
  pinpoint --config ~/config  # Use custom config directory
  pinpoint --export backup.json  # Export configuration
  pinpoint --import-config backup.json  # Import configuration
  pinpoint --info             # Show system information
        """
    )
    
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run without GUI (headless mode)"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Custom configuration directory"
    )
    
    parser.add_argument(
        "--export",
        type=Path,
        help="Export configuration to file"
    )
    
    parser.add_argument(
        "--import-config",
        type=Path,
        dest="import_file",
        help="Import configuration from file"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show system information and exit"
    )
    
    parser.add_argument(
        "--theme",
        choices=["dark", "light", "high_contrast"],
        help="Set theme on startup"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    return parser.parse_args()


def show_system_info():
    """Display system information."""
    app = get_app()
    app.initialize()
    
    info = app.get_system_info()
    
    print("PinPoint System Information")
    print("=" * 40)
    
    # Platform info
    platform = info["platform"]
    print(f"\nPlatform: {platform['platform']}")
    print(f"Version: {platform['version']}")
    print(f"Architecture: {platform['architecture']}")
    print(f"Python: {platform['python_version']}")
    
    # Display info
    print(f"\nDisplays: {len(info['displays'])}")
    for i, display in enumerate(info['displays']):
        print(f"  Display {i}: {display['width']}x{display['height']} at ({display['x']}, {display['y']})")
        if display.get('scale_factor', 1.0) != 1.0:
            print(f"    Scale: {display['scale_factor']}")
            
    # Application info
    print(f"\nTheme: {info['theme']}")
    print(f"Plugins loaded: {info['plugins']['loaded']}")
    print(f"Tiles: {info['tiles']['count']}")
    print(f"Tile types: {', '.join(info['tiles']['types'])}")
    print(f"Layouts: {info['layouts']['count']}")
    
    # Error statistics
    errors = info['errors']
    print(f"\nTotal errors: {errors['total']}")
    if errors['recent']:
        print("Recent errors:")
        for error in errors['recent']:
            print(f"  - {error['error_type']}: {error['message']}")


def run_headless(app, args):
    """Run application in headless mode."""
    print("Starting PinPoint in headless mode...")
    
    if not app.initialize():
        print("Failed to initialize application")
        return 1
        
    if args.export:
        print(f"Exporting configuration to {args.export}")
        app.export_configuration(args.export)
        
    if args.import_file:
        print(f"Importing configuration from {args.import_file}")
        app.import_configuration(args.import_file)
        
    print("PinPoint running in headless mode. Press Ctrl+C to exit.")
    
    try:
        # In a real implementation, this would run an event loop
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        
    app.shutdown()
    return 0


def run_gui(app, args):
    """Run application with GUI."""
    # Check if PyQt6 is available
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("PyQt6 not found. Please install it to run the GUI.")
        print("Run: pip install PyQt6")
        return 1
        
    # Initialize application
    if not app.initialize():
        print("Failed to initialize application")
        return 1
        
    # Apply theme if specified
    if args.theme:
        from design.theme import get_theme_manager
        theme_manager = get_theme_manager()
        theme_manager.set_theme(args.theme)
        
    # Handle import/export before starting GUI
    if args.export:
        app.export_configuration(args.export)
        print(f"Configuration exported to {args.export}")
        
    if args.import_file:
        app.import_configuration(args.import_file)
        print(f"Configuration imported from {args.import_file}")
        
    # Create Qt application
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("PinPoint")
    qt_app.setOrganizationName("PinPoint")
    
    # Here we would create and show the main window
    # For now, just show a message
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.information(
        None,
        "PinPoint",
        "PinPoint is running with the new architecture!\n\n"
        "This is a placeholder UI. The actual interface would be created here."
    )
    
    # In a real implementation:
    # main_window = MainWindow(app)
    # main_window.show()
    # return qt_app.exec()
    
    app.shutdown()
    return 0


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Show info and exit if requested
    if args.info:
        show_system_info()
        return 0
        
    # Create application instance
    app = get_app()
    
    # Set custom config path if provided
    if args.config:
        app = get_app.__wrapped__(args.config)  # Create new instance with custom path
        
    # Configure debug logging
    if args.debug:
        from core.logger import get_logger, LogLevel
        logger = get_logger()
        logger.level = LogLevel.DEBUG
        
    # Run in appropriate mode
    if args.no_gui:
        return run_headless(app, args)
    else:
        return run_gui(app, args)


if __name__ == "__main__":
    sys.exit(main())