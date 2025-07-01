# tests/test_session7_simple.py
"""
Simple tests for Session 7: Error Handling.
Tests error boundaries and recovery mechanisms.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.error_boundary import (
    ErrorBoundary, ErrorContext, ErrorSeverity, 
    RecoveryStrategy, get_error_boundary
)
from core.recovery import (
    RecoveryManager, RetryAction, ResetAction,
    FallbackAction, IsolateAction, get_recovery_manager
)
from core.exceptions import TileError, ValidationError


def test_error_context():
    """Test ErrorContext creation and conversion."""
    # Create error
    error = ValueError("Test error")
    context = ErrorContext(
        error=error,
        component_type="tile",
        component_id="tile_123",
        operation="update",
        severity=ErrorSeverity.ERROR
    )
    
    # Check attributes
    assert context.error == error
    assert context.component_type == "tile"
    assert context.component_id == "tile_123"
    assert context.operation == "update"
    assert context.severity == ErrorSeverity.ERROR
    assert context.timestamp > 0
    assert len(context.traceback) > 0
    
    # Test to_dict
    data = context.to_dict()
    assert data["error_type"] == "ValueError"
    assert data["error_message"] == "Test error"
    assert data["component_type"] == "tile"
    
    print("✓ ErrorContext test passed")


def test_error_boundary_decorator():
    """Test error boundary decorator."""
    boundary = ErrorBoundary()
    
    # Function that fails
    @boundary.catch_errors(
        component_type="test",
        operation="divide",
        recovery=RecoveryStrategy.FALLBACK,
        fallback_value=0
    )
    def divide(a, b):
        return a / b
    
    # Normal operation
    assert divide(10, 2) == 5
    
    # Error case - should return fallback
    result = divide(10, 0)
    assert result == 0
    
    # Check error was recorded
    assert len(boundary.error_history) == 1
    assert type(boundary.error_history[0].error).__name__ == "ZeroDivisionError"
    
    print("✓ Error boundary decorator test passed")


def test_error_boundary_context_manager():
    """Test error boundary context manager."""
    boundary = ErrorBoundary()
    
    # Test with error
    with boundary.error_context(
        component_type="test",
        operation="risky_operation",
        recovery=RecoveryStrategy.IGNORE
    ):
        # This will be caught
        raise RuntimeError("Test error")
    
    # Should have recorded the error
    assert len(boundary.error_history) == 1
    assert "RuntimeError" in boundary.error_history[0].traceback
    
    print("✓ Error boundary context manager test passed")


def test_recovery_strategies():
    """Test different recovery strategies."""
    boundary = ErrorBoundary()
    events_received = []
    
    # Subscribe to events
    from core.events import get_event_bus
    event_bus = get_event_bus()
    
    def event_handler(event):
        events_received.append(event)
    
    event_bus.subscribe("component.reset", event_handler)
    event_bus.subscribe("component.disable", event_handler)
    
    # Test RESET strategy
    context1 = ErrorContext(
        error=ValueError("Test"),
        component_type="tile",
        component_id="tile_1"
    )
    boundary.handle_error(context1, RecoveryStrategy.RESET)
    
    # Should emit reset event
    assert len(events_received) >= 1
    assert any(e.get("event") == "component.reset" for e in events_received)
    
    # Clear events
    events_received.clear()
    
    # Test DISABLE strategy
    context2 = ErrorContext(
        error=ValueError("Test"),
        component_type="tile",
        component_id="tile_2"
    )
    boundary.handle_error(context2, RecoveryStrategy.DISABLE)
    
    # Should emit disable event
    assert len(events_received) >= 1
    assert any(e.get("event") == "component.disable" for e in events_received)
    
    print("✓ Recovery strategies test passed")


def test_error_statistics():
    """Test error statistics gathering."""
    boundary = ErrorBoundary()
    
    # Generate some errors
    errors = [
        (ValueError("Val1"), "tile", ErrorSeverity.ERROR),
        (TypeError("Type1"), "tile", ErrorSeverity.WARNING),
        (ValueError("Val2"), "layout", ErrorSeverity.ERROR),
        (RuntimeError("Run1"), "tile", ErrorSeverity.CRITICAL),
    ]
    
    for error, comp_type, severity in errors:
        context = ErrorContext(
            error=error,
            component_type=comp_type,
            severity=severity
        )
        boundary.handle_error(context)
    
    # Get stats
    stats = boundary.get_error_stats()
    
    assert stats["total_errors"] == 4
    assert stats["by_type"]["ValueError"] == 2
    assert stats["by_component"]["tile"] == 3
    assert stats["by_severity"]["error"] == 2
    assert len(stats["recent_errors"]) == 4
    
    print("✓ Error statistics test passed")


def test_retry_action():
    """Test retry recovery action."""
    retry = RetryAction(max_retries=3, base_delay=0.01)
    
    # Function that fails twice then succeeds
    attempt_count = 0
    def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("Network error")
        return "success"
    
    # Test retry
    context = {
        "operation": flaky_operation,
        "error_type": "ConnectionError"
    }
    
    assert retry.can_recover(context)
    assert retry.execute(context)
    assert context["result"] == "success"
    assert attempt_count == 3
    
    print("✓ Retry action test passed")


def test_fallback_action():
    """Test fallback recovery action."""
    fallback = FallbackAction({
        "tile.create": {"id": "fallback_tile", "content": ""}
    })
    
    # Test with explicit fallback value
    context1 = {
        "component_type": "tile",
        "operation": "create",
        "fallback_value": {"id": "custom_fallback"}
    }
    
    assert fallback.execute(context1)
    assert context1["result"]["id"] == "custom_fallback"
    
    # Test with registry fallback
    context2 = {
        "component_type": "tile",
        "operation": "create"
    }
    
    assert fallback.execute(context2)
    assert context2["result"]["id"] == "fallback_tile"
    
    # Test with type default
    context3 = {
        "component_type": "list"
    }
    
    assert fallback.execute(context3)
    assert context3["result"] == []
    
    print("✓ Fallback action test passed")


def test_isolate_action():
    """Test isolate recovery action."""
    isolate = IsolateAction()
    events_received = []
    
    # Subscribe to events
    from core.events import get_event_bus
    event_bus = get_event_bus()
    
    def event_handler(event):
        events_received.append(event)
    
    event_bus.subscribe("recovery.isolate", event_handler)
    
    # Test isolation
    context = {
        "component_type": "tile",
        "component_id": "tile_bad"
    }
    
    assert isolate.can_recover(context)
    assert isolate.execute(context)
    assert isolate.is_isolated("tile", "tile_bad")
    
    # Should emit event
    assert len(events_received) == 1
    assert events_received[0]["data"]["component_id"] == "tile_bad"
    
    # Test release
    isolate.release_isolation("tile", "tile_bad")
    assert not isolate.is_isolated("tile", "tile_bad")
    
    print("✓ Isolate action test passed")


def test_recovery_manager():
    """Test recovery manager."""
    manager = RecoveryManager()
    
    # Test auto recovery with fallback
    context = {
        "error_type": "ValueError",  # Not retriable
        "component_type": "tile",
        "fallback_value": "recovered"
    }
    
    # Should skip retry and use fallback
    assert manager.recover(context, "auto")
    assert context.get("result") == "recovered"
    
    # Test specific strategy
    reset_events = []
    from core.events import get_event_bus
    event_bus = get_event_bus()
    
    def reset_handler(event):
        reset_events.append(event)
    
    event_bus.subscribe("recovery.reset", reset_handler)
    
    context2 = {
        "component_type": "layout",
        "component_id": "layout_1"
    }
    
    assert manager.recover(context2, "reset")
    assert len(reset_events) == 1
    
    print("✓ Recovery manager test passed")


def test_global_instances():
    """Test global singleton instances."""
    boundary1 = get_error_boundary()
    boundary2 = get_error_boundary()
    assert boundary1 is boundary2
    
    manager1 = get_recovery_manager()
    manager2 = get_recovery_manager()
    assert manager1 is manager2
    
    print("✓ Global instances test passed")


# Run all tests
if __name__ == "__main__":
    print("Running Session 7 tests...")
    test_error_context()
    test_error_boundary_decorator()
    test_error_boundary_context_manager()
    test_recovery_strategies()
    test_error_statistics()
    test_retry_action()
    test_fallback_action()
    test_isolate_action()
    test_recovery_manager()
    test_global_instances()
    print("\n✅ All Session 7 tests passed!")