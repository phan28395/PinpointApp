# core/recovery.py
"""
Recovery mechanisms for PinPoint.
Provides strategies to recover from errors.
"""

from typing import Any, Callable, Optional, Dict
from abc import ABC, abstractmethod
import time
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger
from core.events import get_event_bus


class RecoveryAction(ABC):
    """Abstract base class for recovery actions."""
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Execute the recovery action.
        
        Args:
            context: Error context
            
        Returns:
            True if recovery succeeded
        """
        pass
        
    @abstractmethod
    def can_recover(self, context: Dict[str, Any]) -> bool:
        """
        Check if this action can handle the error.
        
        Args:
            context: Error context
            
        Returns:
            True if can recover
        """
        pass


class RetryAction(RecoveryAction):
    """Retry an operation with exponential backoff."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 0.1,
                 max_delay: float = 5.0):
        """
        Initialize retry action.
        
        Args:
            max_retries: Maximum retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = get_logger("retry_action")
        
    def execute(self, context: Dict[str, Any]) -> bool:
        """Execute retry with exponential backoff."""
        operation = context.get("operation")
        if not operation or not callable(operation):
            self.logger.error("No callable operation provided for retry")
            return False
            
        args = context.get("args", ())
        kwargs = context.get("kwargs", {})
        
        for attempt in range(self.max_retries):
            try:
                # Calculate delay
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                
                if attempt > 0:
                    self.logger.debug(f"Retry attempt {attempt + 1} after {delay}s")
                    time.sleep(delay)
                    
                # Try the operation
                result = operation(*args, **kwargs)
                context["result"] = result
                return True
                
            except Exception as e:
                self.logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return False
                    
        return False
        
    def can_recover(self, context: Dict[str, Any]) -> bool:
        """Check if retry is appropriate."""
        # Retry is appropriate for transient errors
        error_type = context.get("error_type", "")
        retriable_errors = [
            "ConnectionError", "TimeoutError",
            "TemporaryError", "TransientError"
        ]
        return any(err in error_type for err in retriable_errors)


class ResetAction(RecoveryAction):
    """Reset a component to initial state."""
    
    def __init__(self):
        """Initialize reset action."""
        self.logger = get_logger("reset_action")
        self.event_bus = get_event_bus()
        
    def execute(self, context: Dict[str, Any]) -> bool:
        """Execute component reset."""
        component_type = context.get("component_type")
        component_id = context.get("component_id")
        
        if not component_type:
            return False
            
        # Emit reset event
        self.event_bus.emit("recovery.reset", {
            "component_type": component_type,
            "component_id": component_id
        })
        
        self.logger.info(f"Reset {component_type} {component_id or ''}")
        return True
        
    def can_recover(self, context: Dict[str, Any]) -> bool:
        """Reset can handle most component errors."""
        return context.get("component_type") is not None


class FallbackAction(RecoveryAction):
    """Use fallback value or behavior."""
    
    def __init__(self, fallback_registry: Optional[Dict[str, Any]] = None):
        """
        Initialize fallback action.
        
        Args:
            fallback_registry: Registry of fallback values/functions
        """
        self.fallback_registry = fallback_registry or {}
        self.logger = get_logger("fallback_action")
        
    def execute(self, context: Dict[str, Any]) -> bool:
        """Execute fallback."""
        operation = context.get("operation")
        component_type = context.get("component_type")
        
        # Look for fallback in context first
        if "fallback_value" in context:
            context["result"] = context["fallback_value"]
            return True
            
        # Check registry
        fallback_key = f"{component_type}.{operation}"
        if fallback_key in self.fallback_registry:
            fallback = self.fallback_registry[fallback_key]
            
            if callable(fallback):
                try:
                    context["result"] = fallback(context)
                    return True
                except Exception as e:
                    self.logger.error(f"Fallback function failed: {e}")
                    return False
            else:
                context["result"] = fallback
                return True
                
        # Default fallbacks by type
        type_defaults = {
            "tile": {"width": 250, "height": 150, "content": ""},
            "layout": {"tile_instances": []},
            "string": "",
            "number": 0,
            "list": [],
            "dict": {}
        }
        
        if component_type in type_defaults:
            context["result"] = type_defaults[component_type]
            return True
            
        return False
        
    def can_recover(self, context: Dict[str, Any]) -> bool:
        """Fallback can handle most errors."""
        return True


class IsolateAction(RecoveryAction):
    """Isolate a failing component."""
    
    def __init__(self):
        """Initialize isolate action."""
        self.logger = get_logger("isolate_action")
        self.event_bus = get_event_bus()
        self.isolated_components: Dict[str, int] = {}
        
    def execute(self, context: Dict[str, Any]) -> bool:
        """Execute component isolation."""
        component_type = context.get("component_type")
        component_id = context.get("component_id")
        
        if not component_id:
            return False
            
        key = f"{component_type}.{component_id}"
        self.isolated_components[key] = time.time()
        
        # Emit isolation event
        self.event_bus.emit("recovery.isolate", {
            "component_type": component_type,
            "component_id": component_id
        })
        
        self.logger.warning(f"Isolated {component_type} {component_id}")
        return True
        
    def can_recover(self, context: Dict[str, Any]) -> bool:
        """Isolate components with IDs."""
        return context.get("component_id") is not None
        
    def is_isolated(self, component_type: str, component_id: str) -> bool:
        """Check if a component is isolated."""
        key = f"{component_type}.{component_id}"
        return key in self.isolated_components
        
    def release_isolation(self, component_type: str, component_id: str) -> None:
        """Release a component from isolation."""
        key = f"{component_type}.{component_id}"
        if key in self.isolated_components:
            del self.isolated_components[key]
            self.logger.info(f"Released {component_type} {component_id} from isolation")


class RecoveryManager:
    """Manages recovery strategies."""
    
    def __init__(self):
        """Initialize recovery manager."""
        self.logger = get_logger("recovery_manager")
        self.actions = {
            "retry": RetryAction(),
            "reset": ResetAction(),
            "fallback": FallbackAction(),
            "isolate": IsolateAction()
        }
        
    def recover(self, context: Dict[str, Any], strategy: str = "auto") -> bool:
        """
        Attempt recovery using specified strategy.
        
        Args:
            context: Error context
            strategy: Recovery strategy name or "auto"
            
        Returns:
            True if recovery succeeded
        """
        if strategy == "auto":
            # Try strategies in order - fallback before reset for better recovery
            for action_name in ["retry", "fallback", "reset", "isolate"]:
                action = self.actions[action_name]
                if action.can_recover(context):
                    if action.execute(context):
                        self.logger.info(f"Recovery succeeded with {action_name}")
                        return True
            return False
            
        elif strategy in self.actions:
            action = self.actions[strategy]
            if action.can_recover(context):
                return action.execute(context)
                
        self.logger.error(f"Unknown recovery strategy: {strategy}")
        return False
        
    def register_action(self, name: str, action: RecoveryAction) -> None:
        """Register a custom recovery action."""
        self.actions[name] = action
        self.logger.debug(f"Registered recovery action: {name}")
        
    def get_isolated_components(self) -> Dict[str, float]:
        """Get all isolated components."""
        isolate_action = self.actions.get("isolate")
        if isinstance(isolate_action, IsolateAction):
            return isolate_action.isolated_components.copy()
        return {}


# Global recovery manager
_global_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager() -> RecoveryManager:
    """Get the global recovery manager instance."""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = RecoveryManager()
    return _global_recovery_manager