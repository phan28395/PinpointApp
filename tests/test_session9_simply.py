# tests/test_session9_simple.py
"""
Simple tests for Session 9: Platform Support.
Tests platform abstraction and OS-specific functionality.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support import (
    get_platform, get_platform_name, is_windows, is_mac, is_linux,
    PlatformSupport, SystemInfo, DisplayInfo
)
from platform_support.base import PlatformSupport as BasePlatform


def test_platform_detection():
    """Test platform detection functions."""
    platform_name = get_platform_name()
    
    # Should return one of the expected values
    assert platform_name in ["windows", "darwin", "linux", sys.platform]
    
    # Boolean checks should be consistent
    if platform_name == "windows":
        assert is_windows()
        assert not is_mac()
        assert not is_linux()
    elif platform_name == "darwin":
        assert not is_windows()
        assert is_mac()
        assert not is_linux()
    elif platform_name == "linux":
        assert not is_windows()
        assert not is_mac()
        assert is_linux()
        
    print("✓ Platform detection test passed")


def test_get_platform_instance():
    """Test getting platform instance."""
    platform = get_platform()
    
    # Should return a PlatformSupport instance
    assert isinstance(platform, BasePlatform)
    
    # Should be a singleton
    platform2 = get_platform()
    assert platform is platform2
    
    # Should have correct platform name
    assert platform.get_platform_name() in ["windows", "darwin", "linux"]
    
    print("✓ Platform instance test passed")


def test_system_info():
    """Test system information retrieval."""
    platform = get_platform()
    info = platform.get_system_info()
    
    # Should return SystemInfo instance
    assert isinstance(info, SystemInfo)
    
    # Should have required fields
    assert info.platform in ["windows", "darwin", "linux"]
    assert len(info.version) > 0
    assert len(info.architecture) > 0
    assert len(info.python_version) > 0
    
    # Test to_dict
    info_dict = info.to_dict()
    assert "platform" in info_dict
    assert "version" in info_dict
    assert "architecture" in info_dict
    assert "python_version" in info_dict
    
    print("✓ System info test passed")


def test_directory_paths():
    """Test platform-specific directory paths."""
    platform = get_platform()
    
    # Get all paths
    app_data = platform.get_app_data_dir()
    user_config = platform.get_user_config_dir()
    log_dir = platform.get_log_dir()
    
    # Should return Path objects
    assert isinstance(app_data, Path)
    assert isinstance(user_config, Path)
    assert isinstance(log_dir, Path)
    
    # Paths should be absolute
    assert app_data.is_absolute()
    assert user_config.is_absolute()
    assert log_dir.is_absolute()
    
    # Should contain PinPoint or pinpoint
    assert "pinpoint" in str(app_data).lower()
    assert "pinpoint" in str(user_config).lower()
    assert "pinpoint" in str(log_dir).lower()
    
    # Test default paths
    paths = platform.get_default_paths()
    assert "app_data" in paths
    assert "user_config" in paths
    assert "logs" in paths
    assert "data_file" in paths
    assert "config_file" in paths
    assert "log_file" in paths
    
    print("✓ Directory paths test passed")


def test_display_info():
    """Test display information retrieval."""
    platform = get_platform()
    
    # Get displays
    displays = platform.get_displays()
    
    # Should have at least one display
    assert len(displays) >= 1
    
    # Check first display
    display = displays[0]
    assert isinstance(display, DisplayInfo)
    assert display.index >= 0
    assert display.width > 0
    assert display.height > 0
    assert display.scale_factor > 0
    
    # Test resolution string
    assert "x" in display.resolution_string
    
    # Get primary display
    primary = platform.get_primary_display()
    assert primary is not None
    assert isinstance(primary, DisplayInfo)
    
    print("✓ Display info test passed")


def test_startup_registration():
    """Test startup registration (non-destructive)."""
    platform = get_platform()
    
    # Use a unique app name to avoid conflicts
    test_app_name = "PinPointTest_12345"
    
    # Check initial state
    initial_registered = platform.is_startup_registered(test_app_name)
    assert not initial_registered  # Should not be registered initially
    
    # Test registration (may fail on some systems without permissions)
    try:
        # Register
        success = platform.register_startup(sys.executable, test_app_name)
        
        if success:
            # Check if registered
            assert platform.is_startup_registered(test_app_name)
            
            # Unregister
            assert platform.unregister_startup(test_app_name)
            
            # Check if unregistered
            assert not platform.is_startup_registered(test_app_name)
        else:
            # Registration failed (permissions, etc.)
            print("  (Startup registration not available on this system)")
            
    finally:
        # Ensure cleanup
        platform.unregister_startup(test_app_name)
        
    print("✓ Startup registration test passed")


def test_window_operations():
    """Test window operations (may not work without actual window)."""
    platform = get_platform()
    
    # Test with fake window handle
    fake_handle = 12345
    
    # These may return False if not implemented or no window
    result1 = platform.set_window_always_on_top(fake_handle, True)
    result2 = platform.set_window_click_through(fake_handle, True)
    
    # Should return boolean
    assert isinstance(result1, bool)
    assert isinstance(result2, bool)
    
    # Test window handle conversion
    handle = platform.get_window_handle_from_qt(fake_handle)
    # Should return something (may be None)
    
    print("✓ Window operations test passed")


def test_notifications():
    """Test notification display."""
    platform = get_platform()
    
    # Try to show notification (may not work in test environment)
    result = platform.show_notification(
        "Test Notification",
        "This is a test message from PinPoint"
    )
    
    # Should return boolean
    assert isinstance(result, bool)
    
    if not result:
        print("  (Notifications not available in test environment)")
        
    print("✓ Notification test passed")


def test_platform_specific_features():
    """Test platform-specific features."""
    platform = get_platform()
    platform_name = platform.get_platform_name()
    
    if platform_name == "windows":
        # Windows-specific tests
        from platform_support.windows import WindowsPlatform
        assert isinstance(platform, WindowsPlatform)
        
        # Check environment variables are handled
        app_data = platform.get_app_data_dir()
        assert "AppData" in str(app_data) or "Users" in str(app_data)
        
    elif platform_name == "darwin":
        # macOS-specific tests
        from platform_support.mac import MacPlatform
        assert isinstance(platform, MacPlatform)
        
        # Check Library paths
        app_data = platform.get_app_data_dir()
        assert "Library" in str(app_data)
        
    elif platform_name == "linux":
        # Linux-specific tests
        from platform_support.linux import LinuxPlatform
        assert isinstance(platform, LinuxPlatform)
        
        # Check XDG paths
        config_dir = platform.get_user_config_dir()
        assert ".config" in str(config_dir) or "XDG" in str(config_dir)
        
    print("✓ Platform-specific features test passed")


def test_ensure_directories():
    """Test directory creation."""
    # Create temporary platform instance with temp paths
    platform = get_platform()
    
    # The platform should have already ensured directories on creation
    # Check that they can be created
    paths = platform.get_default_paths()
    
    # Log directory should exist or be creatable
    log_dir = paths["logs"]
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            assert log_dir.exists()
            # Clean up
            log_dir.rmdir()
        except Exception:
            # May not have permissions in test environment
            pass
            
    print("✓ Directory creation test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 9 tests...")
    test_platform_detection()
    test_get_platform_instance()
    test_system_info()
    test_directory_paths()
    test_display_info()
    test_startup_registration()
    test_window_operations()
    test_notifications()
    test_platform_specific_features()
    test_ensure_directories()
    print("\n✅ All Session 9 tests passed!")