# tests/base_test.py
"""
Base test class for PinPoint tests.
Provides test reporting and common utilities.
"""

import time
import traceback
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration: float
    error: Optional[str] = None
    traceback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "passed": self.passed,
            "duration": self.duration,
            "error": self.error,
            "traceback": self.traceback
        }


@dataclass
class TestSuiteResult:
    """Result of a test suite."""
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    tests: List[TestResult] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """Get total duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
        
    @property
    def passed_count(self) -> int:
        """Get number of passed tests."""
        return sum(1 for t in self.tests if t.passed)
        
    @property
    def failed_count(self) -> int:
        """Get number of failed tests."""
        return sum(1 for t in self.tests if not t.passed)
        
    @property
    def pass_rate(self) -> float:
        """Get pass rate percentage."""
        if not self.tests:
            return 0.0
        return (self.passed_count / len(self.tests)) * 100
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "total_tests": len(self.tests),
            "passed": self.passed_count,
            "failed": self.failed_count,
            "pass_rate": self.pass_rate,
            "tests": [t.to_dict() for t in self.tests]
        }


class BaseTest:
    """
    Base class for all PinPoint tests.
    Provides test discovery, execution, and reporting.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize test suite.
        
        Args:
            name: Test suite name (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self.logger = get_logger(f"test.{self.name}")
        self.result = TestSuiteResult(
            name=self.name,
            start_time=datetime.now()
        )
        
    def setup(self) -> None:
        """Setup before all tests. Override in subclasses."""
        pass
        
    def teardown(self) -> None:
        """Teardown after all tests. Override in subclasses."""
        pass
        
    def setup_test(self) -> None:
        """Setup before each test. Override in subclasses."""
        pass
        
    def teardown_test(self) -> None:
        """Teardown after each test. Override in subclasses."""
        pass
        
    def get_test_methods(self) -> List[str]:
        """
        Get all test methods (starting with 'test_').
        
        Returns:
            List of test method names
        """
        methods = []
        for name in dir(self):
            if name.startswith('test_') and callable(getattr(self, name)):
                methods.append(name)
        return sorted(methods)
        
    def run_test(self, test_name: str) -> TestResult:
        """
        Run a single test method.
        
        Args:
            test_name: Name of test method
            
        Returns:
            Test result
        """
        start_time = time.time()
        error = None
        tb = None
        passed = False
        
        try:
            # Setup
            self.setup_test()
            
            # Run test
            test_method = getattr(self, test_name)
            test_method()
            
            # If we get here, test passed
            passed = True
            
        except AssertionError as e:
            error = str(e) or "Assertion failed"
            tb = traceback.format_exc()
            
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            tb = traceback.format_exc()
            
        finally:
            # Teardown
            try:
                self.teardown_test()
            except Exception as e:
                if not error:
                    error = f"Teardown failed: {e}"
                    tb = traceback.format_exc()
                    
        duration = time.time() - start_time
        
        return TestResult(
            name=test_name,
            passed=passed,
            duration=duration,
            error=error,
            traceback=tb
        )
        
    def run(self) -> TestSuiteResult:
        """
        Run all tests in the suite.
        
        Returns:
            Test suite result
        """
        self.logger.info(f"Running test suite: {self.name}")
        
        # Setup
        try:
            self.setup()
        except Exception as e:
            self.logger.error(f"Suite setup failed: {e}")
            # Still try to run tests
            
        # Discover and run tests
        test_methods = self.get_test_methods()
        self.logger.info(f"Found {len(test_methods)} tests")
        
        for test_name in test_methods:
            self.logger.debug(f"Running {test_name}")
            result = self.run_test(test_name)
            self.result.tests.append(result)
            
            # Log result
            if result.passed:
                self.logger.debug(f"✓ {test_name} ({result.duration:.3f}s)")
            else:
                self.logger.error(f"✗ {test_name}: {result.error}")
                if result.traceback:
                    self.logger.debug(result.traceback)
                    
        # Teardown
        try:
            self.teardown()
        except Exception as e:
            self.logger.error(f"Suite teardown failed: {e}")
            
        # Finalize result
        self.result.end_time = datetime.now()
        
        # Log summary
        self.logger.info(
            f"Test suite completed: {self.result.passed_count}/{len(self.result.tests)} passed "
            f"({self.result.pass_rate:.1f}%) in {self.result.duration:.2f}s"
        )
        
        return self.result
        
    def assert_equal(self, actual: Any, expected: Any, msg: Optional[str] = None):
        """Assert two values are equal."""
        if actual != expected:
            if msg:
                raise AssertionError(msg)
            else:
                raise AssertionError(f"Expected {expected!r}, got {actual!r}")
                
    def assert_true(self, value: Any, msg: Optional[str] = None):
        """Assert value is truthy."""
        if not value:
            raise AssertionError(msg or f"Expected truthy value, got {value!r}")
            
    def assert_false(self, value: Any, msg: Optional[str] = None):
        """Assert value is falsy."""
        if value:
            raise AssertionError(msg or f"Expected falsy value, got {value!r}")
            
    def assert_in(self, item: Any, container: Any, msg: Optional[str] = None):
        """Assert item is in container."""
        if item not in container:
            raise AssertionError(msg or f"{item!r} not found in {container!r}")
            
    def assert_not_in(self, item: Any, container: Any, msg: Optional[str] = None):
        """Assert item is not in container."""
        if item in container:
            raise AssertionError(msg or f"{item!r} found in {container!r}")
            
    def assert_raises(self, exception_type: type, func: Callable, *args, **kwargs):
        """Assert function raises specific exception."""
        try:
            func(*args, **kwargs)
            raise AssertionError(f"Expected {exception_type.__name__} to be raised")
        except exception_type:
            pass  # Expected
        except Exception as e:
            raise AssertionError(
                f"Expected {exception_type.__name__}, got {type(e).__name__}: {e}"
            )
            
    def assert_none(self, value: Any, msg: Optional[str] = None):
        """Assert value is None."""
        if value is not None:
            raise AssertionError(msg or f"Expected None, got {value!r}")
            
    def assert_not_none(self, value: Any, msg: Optional[str] = None):
        """Assert value is not None."""
        if value is None:
            raise AssertionError(msg or "Expected non-None value")
            
    def assert_greater(self, a: Any, b: Any, msg: Optional[str] = None):
        """Assert a > b."""
        if not a > b:
            raise AssertionError(msg or f"{a!r} is not greater than {b!r}")
            
    def assert_less(self, a: Any, b: Any, msg: Optional[str] = None):
        """Assert a < b."""
        if not a < b:
            raise AssertionError(msg or f"{a!r} is not less than {b!r}")
            
    def assert_instance(self, obj: Any, cls: type, msg: Optional[str] = None):
        """Assert object is instance of class."""
        if not isinstance(obj, cls):
            raise AssertionError(
                msg or f"Expected instance of {cls.__name__}, got {type(obj).__name__}"
            )


class TestReporter:
    """Generate test reports in various formats."""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize reporter.
        
        Args:
            output_dir: Directory for reports (default: tests/reports)
        """
        self.output_dir = output_dir or Path(__file__).parent / "reports"
        self.output_dir.mkdir(exist_ok=True)
        self.logger = get_logger("test_reporter")
        
    def generate_json_report(self, results: List[TestSuiteResult], filename: str = "report.json"):
        """Generate JSON report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_suites": len(results),
                "total_tests": sum(len(r.tests) for r in results),
                "total_passed": sum(r.passed_count for r in results),
                "total_failed": sum(r.failed_count for r in results),
                "overall_pass_rate": self._calculate_overall_pass_rate(results),
                "total_duration": sum(r.duration for r in results)
            },
            "suites": [r.to_dict() for r in results]
        }
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Generated JSON report: {output_path}")
        return output_path
        
    def generate_text_report(self, results: List[TestSuiteResult], filename: str = "report.txt"):
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("PINPOINT TEST REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        total_tests = sum(len(r.tests) for r in results)
        total_passed = sum(r.passed_count for r in results)
        total_failed = sum(r.failed_count for r in results)
        overall_rate = self._calculate_overall_pass_rate(results)
        total_duration = sum(r.duration for r in results)
        
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total Test Suites: {len(results)}")
        lines.append(f"Total Tests: {total_tests}")
        lines.append(f"Passed: {total_passed}")
        lines.append(f"Failed: {total_failed}")
        lines.append(f"Pass Rate: {overall_rate:.1f}%")
        lines.append(f"Total Duration: {total_duration:.2f}s")
        lines.append("")
        
        # Suite details
        for suite in results:
            lines.append("=" * 80)
            lines.append(f"Suite: {suite.name}")
            lines.append("-" * 40)
            lines.append(f"Tests: {len(suite.tests)} | Passed: {suite.passed_count} | Failed: {suite.failed_count}")
            lines.append(f"Pass Rate: {suite.pass_rate:.1f}% | Duration: {suite.duration:.2f}s")
            lines.append("")
            
            # Test details
            for test in suite.tests:
                if test.passed:
                    lines.append(f"  ✓ {test.name} ({test.duration:.3f}s)")
                else:
                    lines.append(f"  ✗ {test.name} ({test.duration:.3f}s)")
                    lines.append(f"    Error: {test.error}")
                    
            lines.append("")
            
        # Failed test details
        if total_failed > 0:
            lines.append("=" * 80)
            lines.append("FAILED TEST DETAILS")
            lines.append("=" * 80)
            
            for suite in results:
                for test in suite.tests:
                    if not test.passed:
                        lines.append(f"\n{suite.name}::{test.name}")
                        lines.append("-" * 40)
                        if test.traceback:
                            lines.append(test.traceback.rstrip())
                            
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        self.logger.info(f"Generated text report: {output_path}")
        return output_path
        
    def _calculate_overall_pass_rate(self, results: List[TestSuiteResult]) -> float:
        """Calculate overall pass rate."""
        total_tests = sum(len(r.tests) for r in results)
        if total_tests == 0:
            return 0.0
        total_passed = sum(r.passed_count for r in results)
        return (total_passed / total_tests) * 100