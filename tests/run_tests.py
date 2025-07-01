# tests/run_tests.py
"""
Simple script to run all tests and generate reports.
Can be run directly: python tests/run_tests.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check Python version
if sys.version_info < (3, 7):
    print(f"Error: Python 3.7+ required, you have {sys.version}")
    sys.exit(1)

from tests.runner import TestRunner
from core.logger import configure_global_logger, LogLevel


def main():
    """Run all tests and generate reports."""
    print("PinPoint Test Suite")
    print("=" * 60)
    
    # Configure logging (less verbose for cleaner output)
    configure_global_logger(level=LogLevel.WARNING)
    
    # Create test runner
    try:
        runner = TestRunner()
    except Exception as e:
        print(f"Error creating test runner: {e}")
        return 1
    
    # Run all tests
    print("Discovering and running tests...")
    try:
        results = runner.run_all()
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    runner.print_summary()
    
    # Generate reports
    if results:
        print("\nGenerating test reports...")
        try:
            report_paths = runner.generate_reports()
            
            print("\nReports generated:")
            for path in report_paths:
                print(f"  - {path}")
                
            # Also print location of reports directory
            reports_dir = Path(__file__).parent / "reports"
            print(f"\nAll reports saved to: {reports_dir}")
        except Exception as e:
            print(f"Error generating reports: {e}")
    else:
        print("\nNo tests were run!")
        
    # Return appropriate exit code
    total_failed = sum(r.failed_count for r in results) if results else 0
    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())