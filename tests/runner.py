# tests/runner.py
"""
Test runner for PinPoint.
Discovers and runs all tests with reporting.
"""

import sys
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import List, Optional, Type
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base_test import BaseTest, TestSuiteResult, TestReporter
from core.logger import get_logger, LogLevel, configure_global_logger


class TestRunner:
    """
    Discovers and runs test suites.
    """
    
    def __init__(self, test_dir: Path = None, pattern: str = "test_*.py"):
        """
        Initialize test runner.
        
        Args:
            test_dir: Directory containing tests
            pattern: File pattern for test files
        """
        self.test_dir = test_dir or Path(__file__).parent
        self.pattern = pattern
        self.logger = get_logger("test_runner")
        self.results: List[TestSuiteResult] = []
        
    def discover_tests(self) -> List[Type[BaseTest]]:
        """
        Discover test classes in test directory.
        
        Returns:
            List of test classes
        """
        test_classes = []
        
        # Find test files
        test_files = list(self.test_dir.glob(self.pattern))
        self.logger.info(f"Found {len(test_files)} test files")
        
        for test_file in sorted(test_files):
            # Skip runner itself and __pycache__
            if test_file.name == "runner.py" or "__pycache__" in str(test_file):
                continue
                
            self.logger.debug(f"Loading test file: {test_file}")
                
            try:
                # Import module
                module_name = f"test_module_{test_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, test_file)
                if not spec or not spec.loader:
                    self.logger.warning(f"Could not create spec for {test_file}")
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Find test classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTest) and 
                        obj is not BaseTest and
                        obj.__module__ == module_name):  # Only from this module
                        test_classes.append(obj)
                        self.logger.debug(f"Found test class: {obj.__name__} in {test_file.name}")
                        
            except Exception as e:
                self.logger.error(f"Failed to load {test_file}: {type(e).__name__}: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
                
        self.logger.info(f"Discovered {len(test_classes)} test classes")
        return test_classes
        
    def run_suite(self, test_class: Type[BaseTest]) -> TestSuiteResult:
        """
        Run a single test suite.
        
        Args:
            test_class: Test class to run
            
        Returns:
            Test suite result
        """
        self.logger.info(f"Running suite: {test_class.__name__}")
        
        try:
            # Create instance and run
            suite = test_class()
            result = suite.run()
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to run suite {test_class.__name__}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            
            # Return empty result with error
            result = TestSuiteResult(
                name=test_class.__name__,
                start_time=datetime.now()
            )
            result.end_time = datetime.now()
            return result
            
    def run_all(self, filter_pattern: Optional[str] = None) -> List[TestSuiteResult]:
        """
        Run all discovered tests.
        
        Args:
            filter_pattern: Optional pattern to filter test names
            
        Returns:
            List of test results
        """
        # Discover tests
        test_classes = self.discover_tests()
        
        if filter_pattern:
            # Filter by pattern
            test_classes = [
                tc for tc in test_classes 
                if filter_pattern.lower() in tc.__name__.lower()
            ]
            self.logger.info(f"Filtered to {len(test_classes)} test classes")
            
        # Run each suite
        for test_class in test_classes:
            result = self.run_suite(test_class)
            self.results.append(result)
            
        return self.results
        
    def run_specific(self, test_names: List[str]) -> List[TestSuiteResult]:
        """
        Run specific test suites by name.
        
        Args:
            test_names: List of test class names
            
        Returns:
            List of test results
        """
        # Discover all tests
        all_tests = self.discover_tests()
        
        # Find requested tests
        test_map = {tc.__name__: tc for tc in all_tests}
        
        for name in test_names:
            if name in test_map:
                result = self.run_suite(test_map[name])
                self.results.append(result)
            else:
                self.logger.warning(f"Test class not found: {name}")
                
        return self.results
        
    def generate_reports(self, formats: List[str] = None) -> List[Path]:
        """
        Generate test reports.
        
        Args:
            formats: Report formats (json, text)
            
        Returns:
            List of generated report paths
        """
        if not formats:
            formats = ["json", "text"]
            
        reporter = TestReporter()
        paths = []
        
        if "json" in formats:
            path = reporter.generate_json_report(self.results)
            paths.append(path)
            
        if "text" in formats:
            path = reporter.generate_text_report(self.results)
            paths.append(path)
            
        return paths
        
    def print_summary(self):
        """Print test summary to console."""
        if not self.results:
            print("No test results to display")
            return
            
        # Calculate totals
        total_suites = len(self.results)
        total_tests = sum(len(r.tests) for r in self.results)
        total_passed = sum(r.passed_count for r in self.results)
        total_failed = sum(r.failed_count for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Suites:   {total_suites}")
        print(f"Tests:    {total_tests}")
        print(f"Passed:   {total_passed} ✓")
        print(f"Failed:   {total_failed} ✗")
        print(f"Duration: {total_duration:.2f}s")
        
        if total_tests > 0:
            pass_rate = (total_passed / total_tests) * 100
            print(f"Pass Rate: {pass_rate:.1f}%")
            
        # Print failed tests
        if total_failed > 0:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for suite in self.results:
                for test in suite.tests:
                    if not test.passed:
                        print(f"  ✗ {suite.name}::{test.name}")
                        print(f"    {test.error}")
                        
        print("=" * 60)


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="PinPoint Test Runner")
    parser.add_argument(
        "--filter", "-f",
        help="Filter test suites by pattern"
    )
    parser.add_argument(
        "--tests", "-t",
        nargs="+",
        help="Run specific test suites by name"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation"
    )
    parser.add_argument(
        "--format",
        nargs="+",
        choices=["json", "text"],
        default=["json", "text"],
        help="Report formats to generate"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        configure_global_logger(level=LogLevel.DEBUG)
    else:
        configure_global_logger(level=LogLevel.INFO)
        
    # Create runner
    runner = TestRunner()
    
    # Run tests
    if args.tests:
        runner.run_specific(args.tests)
    else:
        runner.run_all(filter_pattern=args.filter)
        
    # Print summary
    runner.print_summary()
    
    # Generate reports
    if not args.no_report and runner.results:
        paths = runner.generate_reports(formats=args.format)
        print(f"\nGenerated {len(paths)} report(s):")
        for path in paths:
            print(f"  - {path}")
            
    # Exit with appropriate code
    total_failed = sum(r.failed_count for r in runner.results)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    from datetime import datetime  # Import needed for error handling
    main()