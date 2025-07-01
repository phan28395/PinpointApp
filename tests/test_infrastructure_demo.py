# tests/test_infrastructure_demo.py
"""
Demonstration of the test infrastructure.
Shows how to use BaseTest and various assertions.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base_test import BaseTest


class TestInfrastructureDemo(BaseTest):
    """Demo test suite to show infrastructure features."""
    
    def setup(self):
        """Suite-level setup."""
        self.shared_data = {"setup": True}
        
    def teardown(self):
        """Suite-level teardown."""
        self.shared_data = None
        
    def setup_test(self):
        """Test-level setup."""
        self.test_data = []
        
    def teardown_test(self):
        """Test-level teardown."""
        self.test_data = None
        
    def test_passing_example(self):
        """Example of a passing test."""
        # Basic assertions
        self.assert_equal(2 + 2, 4)
        self.assert_true(True)
        self.assert_false(False)
        
        # Collection assertions
        self.assert_in("a", ["a", "b", "c"])
        self.assert_not_in("d", ["a", "b", "c"])
        
        # Comparison assertions
        self.assert_greater(5, 3)
        self.assert_less(3, 5)
        
        # Type assertions
        self.assert_instance("hello", str)
        self.assert_instance(42, int)
        
        # None assertions
        self.assert_none(None)
        self.assert_not_none("not none")
        
    def test_with_timing(self):
        """Test that takes some time."""
        # Simulate some work
        time.sleep(0.1)
        
        # Still passes
        self.assert_true(True)
        
    def test_exception_handling(self):
        """Test exception assertions."""
        def raise_error():
            raise ValueError("Expected error")
            
        # This should pass
        self.assert_raises(ValueError, raise_error)
        
        # This would fail if we expected wrong exception
        # self.assert_raises(TypeError, raise_error)
        
    def test_custom_messages(self):
        """Test custom assertion messages."""
        x = 10
        y = 20
        
        # Custom message on failure
        self.assert_equal(x, 10, "x should be 10")
        self.assert_greater(y, x, f"{y} should be greater than {x}")
        
    def test_deliberate_failure(self):
        """Example of a failing test (commented out)."""
        # Uncomment to see failure in report
        # self.assert_equal(1, 2, "This will fail!")
        pass


class TestAnotherDemo(BaseTest):
    """Another demo suite to show multiple suites."""
    
    def test_quick_test(self):
        """A quick test in another suite."""
        result = sum([1, 2, 3, 4, 5])
        self.assert_equal(result, 15)
        
    def test_string_operations(self):
        """Test string operations."""
        text = "Hello World"
        self.assert_in("Hello", text)
        self.assert_equal(text.lower(), "hello world")
        self.assert_equal(len(text), 11)