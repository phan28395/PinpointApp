# core/error_boundary.py
"""
Error boundary system for PinPoint.
Catches and handles errors in tiles and other components.
"""

from typing import Any, Callable, Optional, Dict, List
from enum import Enum
from contextlib import contextmanager
from pathlib import Path
import traceback
import time

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.exceptions import PinPointError, TileError
from core.events import get_event_bus
from core.logger import get_logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorContext:
    """Context for an error occurrence."""
    
    def __init__(self, 
                 error: Exception,
                 component_type: str,
                 component_id: Optional[str] = None,
                 operation: Optional[str] = None,
                 severity: ErrorSeverity = ErrorSeverity.ERROR):
        """
        Initialize error context.
        
        Args:
            error: The exception that occurred
            component_type: Type of component (tile, layout, etc.)
            component_id: ID of the component
            operation: Operation being performed
            severity: Error severity
        """
        self.error = error
        self.component_type = component_type
        self.component_id = component_id
        self.operation = operation
        self.severity = severity
        self.timestamp = time.time()
        
        # Get traceback if we're in an exception context
        try:
            self.traceback = traceback.format_exc()
            # If no current exception, create one from the error
            if self.traceback == "NoneType: None\n":
                self.traceback = f"{type(error).__name__}: {str(error)}"
        except:
            self.traceback = f"{type(error).__name__}: {str(error)}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "component_type": self.component_type,
            "component_id": self.component_id,
            "operation": self.operation,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "traceback": self.traceback
        }


class RecoveryStrategy(Enum):
    """Recovery strategies for errors."""
    RETRY = "retry"
    RESET = "reset"
    DISABLE = "disable"
    IGNORE = "ignore"
    FALLBACK = "fallback"


class ErrorBoundary:
    """
    Catches and handles errors in components.
    Provides recovery mechanisms.
    """
    
    def __init__(self):
        """Initialize error boundary."""
        self.logger = get_logger("error_boundary")
        self.event_bus = get_event_bus()
        self.error_history: List[ErrorContext] = []
        self.recovery_handlers: Dict[str, Callable] = {}
        self.max_history_size = 100
        
    def catch_errors(self, 
                    component_type: str,
                    component_id: Optional[str] = None,
                    operation: Optional[str] = None,
                    recovery: RecoveryStrategy = RecoveryStrategy.IGNORE,
                    fallback_value: Any = None):
        """
        Decorator to catch errors in functions.
        
        Args:
            component_type: Type of component
            component_id: Component ID
            operation: Operation name
            recovery: Recovery strategy
            fallback_value: Value to return on error
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Create error context
                    context = ErrorContext(
                        error=e,
                        component_type=component_type,
                        component_id=component_id,
                        operation=operation or func.__name__
                    )
                    
                    # Handle the error
                    return self.handle_error(context, recovery, fallback_value)
                    
            return wrapper
        return decorator
        
    @contextmanager
    def error_context(self,
                     component_type: str,
                     component_id: Optional[str] = None,
                     operation: Optional[str] = None,
                     recovery: RecoveryStrategy = RecoveryStrategy.IGNORE,
                     fallback_value: Any = None):
        """
        Context manager for error handling.
        
        Args:
            component_type: Type of component
            component_id: Component ID
            operation: Operation name
            recovery: Recovery strategy
            fallback_value: Value to return on error
        """
        try:
            yield
        except Exception as e:
            context = ErrorContext(
                error=e,
                component_type=component_type,
                component_id=component_id,
                operation=operation
            )
            self.handle_error(context, recovery, fallback_value)
            
    def handle_error(self,
                    context: ErrorContext,
                    recovery: RecoveryStrategy = RecoveryStrategy.IGNORE,
                    fallback_value: Any = None) -> Any:
        """
        Handle an error with recovery.
        
        Args:
            context: Error context
            recovery: Recovery strategy
            fallback_value: Fallback value
            
        Returns:
            Recovery result or fallback value
        """
        # Log the error
        self.logger.error(
            f"Error in {context.component_type}",
            context.to_dict()
        )
        
        # Add to history
        self._add_to_history(context)
        
        # Emit event
        self.event_bus.emit("error.occurred", context.to_dict())
        
        # Apply recovery strategy
        if recovery == RecoveryStrategy.RETRY:
            # Would need the original function to retry
            # For now, just return fallback
            return fallback_value
            
        elif recovery == RecoveryStrategy.RESET:
            # Emit reset event
            self.event_bus.emit("component.reset", {
                "component_type": context.component_type,
                "component_id": context.component_id
            })
            return fallback_value
            
        elif recovery == RecoveryStrategy.DISABLE:
            # Emit disable event
            self.event_bus.emit("component.disable", {
                "component_type": context.component_type,
                "component_id": context.component_id
            })
            return fallback_value
            
        elif recovery == RecoveryStrategy.FALLBACK:
            return fallback_value
            
        else:  # IGNORE
            # Check if it's a critical error
            if isinstance(context.error, (SystemExit, KeyboardInterrupt)):
                raise context.error
            return fallback_value
            
    def register_recovery_handler(self,
                                error_type: type,
                                handler: Callable[[ErrorContext], Any]) -> None:
        """
        Register a custom recovery handler for an error type.
        
        Args:
            error_type: Type of error to handle
            handler: Recovery handler function
        """
        self.recovery_handlers[error_type.__name__] = handler
        self.logger.debug(f"Registered recovery handler for {error_type.__name__}")
        
    def _add_to_history(self, context: ErrorContext) -> None:
        """Add error to history with size limit."""
        self.error_history.append(context)
        
        # Trim history if too large
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
            
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Error statistics
        """
        if not self.error_history:
            return {
                "total_errors": 0,
                "by_type": {},
                "by_component": {},
                "by_severity": {}
            }
            
        by_type = {}
        by_component = {}
        by_severity = {}
        
        for context in self.error_history:
            # By error type
            error_type = type(context.error).__name__
            by_type[error_type] = by_type.get(error_type, 0) + 1
            
            # By component
            comp_type = context.component_type
            by_component[comp_type] = by_component.get(comp_type, 0) + 1
            
            # By severity
            severity = context.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
        return {
            "total_errors": len(self.error_history),
            "by_type": by_type,
            "by_component": by_component,
            "by_severity": by_severity,
            "recent_errors": [
                ctx.to_dict() for ctx in self.error_history[-5:]
            ]
        }
        
    def clear_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()
        self.logger.info("Cleared error history")


# Global error boundary instance
_global_error_boundary: Optional[ErrorBoundary] = None


def get_error_boundary() -> ErrorBoundary:
    """Get the global error boundary instance."""
    global _global_error_boundary
    if _global_error_boundary is None:
        _global_error_boundary = ErrorBoundary()
    return _global_error_boundary