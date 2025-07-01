# tests/test_simple_verify.py
"""
Simple test to verify the test infrastructure is working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base_test import BaseTest


class TestSimpleVerification(BaseTest):
    """Simple test suite to verify infrastructure."""
    
    def test_basic_math(self):
        """Test basic arithmetic."""
        self.assert_equal(2 + 2, 4)
        self.assert_equal(10 - 5, 5)
        self.assert_equal(3 * 4, 12)
        
    def test_string_operations(self):
        """Test string operations."""
        self.assert_equal("hello" + " " + "world", "hello world")
        self.assert_in("Python", "Python is great")
        self.assert_true("HELLO".isupper())
        
    def test_list_operations(self):
        """Test list operations."""
        my_list = [1, 2, 3, 4, 5]
        self.assert_equal(len(my_list), 5)
        self.assert_in(3, my_list)
        self.assert_not_in(6, my_list)
        
    def test_assertions(self):
        """Test various assertion methods."""
        # Equality
        self.assert_equal(42, 42)
        
        # Truthiness
        self.assert_true(True)
        self.assert_false(False)
        self.assert_true([1, 2, 3])  # Non-empty list is truthy
        self.assert_false([])  # Empty list is falsy
        
        # None checks
        self.assert_none(None)
        self.assert_not_none("not none")
        
        # Comparisons
        self.assert_greater(10, 5)
        self.assert_less(5, 10)
        
        # Type checks
        self.assert_instance("string", str)
        self.assert_instance(123, int)
        self.assert_instance([1, 2, 3], list)