# tests/test_session9_simple.py
"""
Simple tests for Session 9: Platform Support.
Tests platform abstraction and OS-specific implementations.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from platform_support import get_current_platform
from platform_support.base import PlatformBase
from core.constants import APP_NAME


def test_platform_instance():
    """Test getting platform instance."""
    plat = get_current_platform()
    
    # Should return a platform instance
    assert plat is not None
    assert isinstance(plat, PlatformBase)
    
    # Should be singleton
    plat2 = get_current_platform()
    assert plat is plat2
    
    print(f"✓ Platform instance test passed - Platform: {plat.get_platform_name()}")


def test_platform_directories():
    """Test platform directory methods."""
    plat = get_current_platform()
    
    # All directory methods should return Path objects
    dirs = {
        "user_data": plat.get_user_data_dir(),
        "config": plat.get_config_dir(),
        "cache": plat.get_cache_dir(),
        "logs": plat.get_log_dir(),
        "documents": plat.get_documents_dir()
    }
    
    for name, path in dirs.items():
        assert isinstance(path, Path)
        assert APP_NAME in str(path) or name == "documents"
        print(f"  {name}: {path}")
        
    print("✓ Platform directories test passed")


def test_platform_capabilities():
    """Test platform capability queries."""
    plat = get_current_platform()
    
    # These should all return boolean values
    capabilities = {
        "system_tray": plat.supports_system_tray(),
        "always_on_top": plat.supports_always_on_top(),
        "transparency": plat.supports_transparency()
    }
    
    for name, supported in capabilities.items():
        assert isinstance(supported, bool)
        print(f"  {name}: {supported}")
        
    print("✓ Platform capabilities test passed")


def test_screen_info():
    """Test screen information methods."""
    plat = get_current_platform()
    
    # Get screen count
    screen_count = plat.get_screen_count()
    assert isinstance(screen_count, int)
    assert screen_count >= 1
    
    # Get primary screen size
    width, height = plat.get_primary_screen_size()
    assert isinstance(width, int)
    assert isinstance(height, int)
    assert width > 0
    assert height > 0
    
    print(f"  Screens: {screen_count}")
    print(f"  Primary size: {width}x{height}")
    print("✓ Screen info test passed")


def test_tray_icon_size():
    """Test system tray icon size."""
    plat = get_current_platform()
    
    width, height = plat.get_tray_icon_size()
    assert isinstance(width, int)
    assert isinstance(height, int)
    assert 16 <= width <= 32  # Reasonable icon sizes
    assert 16 <= height <= 32
    
    print(f"  Tray icon size: {width}x{height}")
    print("✓ Tray icon size test passed")


def test_startup_registration():
    """Test startup registration methods."""
    plat = get_current_platform()
    
    test_app = "PinPointTest"
    test_path = str(Path(sys.executable).absolute())
    
    # Check if registered (should be False initially)
    is_registered = plat.is_startup_registered(test_app)
    assert isinstance(is_registered, bool)
    
    # Try to register
    success = plat.register_startup(test_app, test_path)
    assert isinstance(success, bool)
    
    if success:
        # If registration worked, check it's registered
        assert plat.is_startup_registered(test_app)
        
        # Unregister
        unregister_success = plat.unregister_startup(test_app)
        assert unregister_success
        
        # Should no longer be registered
        assert not plat.is_startup_registered(test_app)
        
    print(f"  Registration tested: {success}")
    print("✓ Startup registration test passed")


def test_file_operations():
    """Test file operations."""
    plat = get_current_platform()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        test_file = Path(f.name)
        f.write("Test content")
        
    try:
        # Test show in file manager (just check it returns bool)
        show_result = plat.show_in_file_manager(test_file)
        assert isinstance(show_result, bool)
        
        # Don't actually trash the file in tests
        # Just verify the method exists and returns bool
        # trash_result = plat.trash_file(test_file)
        # assert isinstance(trash_result, bool)
        
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
            
    print("✓ File operations test passed")


def test_system_info():
    """Test system info gathering."""
    plat = get_current_platform()
    
    info = plat.get_system_info()
    assert isinstance(info, dict)
    
    # Check required keys
    required_keys = [
        "platform", "system", "release", "version",
        "machine", "processor", "python_version",
        "supports_tray", "supports_transparency", "screen_count"
    ]
    
    for key in required_keys:
        assert key in info
        print(f"  {key}: {info[key]}")
        
    print("✓ System info test passed")


def test_keyboard_shortcuts():
    """Test keyboard shortcut formatting."""
    plat = get_current_platform()
    
    # Test modifier key names
    modifiers = ["ctrl", "alt", "shift", "meta"]
    for mod in modifiers:
        name = plat.get_modifier_key_name(mod)
        assert isinstance(name, str)
        assert len(name) > 0
        
    # Test shortcut formatting
    shortcut = plat.format_shortcut(["ctrl", "shift"], "S")
    assert isinstance(shortcut, str)
    assert "S" in shortcut
    
    print(f"  Example shortcut: {shortcut}")
    print("✓ Keyboard shortcuts test passed")


def test_ensure_directories():
    """Test directory creation."""
    plat = get_current_platform()
    
    # This should create all necessary directories
    plat.ensure_directories()
    
    # Verify some directories exist
    dirs = [
        plat.get_user_data_dir(),
        plat.get_config_dir(),
        plat.get_cache_dir(),
        plat.get_log_dir()
    ]
    
    for dir_path in dirs:
        assert dir_path.exists()
        assert dir_path.is_dir()
        
    print("✓ Ensure directories test passed")


# Run all tests
if __name__ == "__main__":
    print(f"Running Session 9 tests on {sys.platform}...")
    test_platform_instance()
    test_platform_directories()
    test_platform_capabilities()
    test_screen_info()
    test_tray_icon_size()
    test_startup_registration()
    test_file_operations()
    test_system_info()
    test_keyboard_shortcuts()
    test_ensure_directories()
    print("\n✅ All Session 9 tests passed!")