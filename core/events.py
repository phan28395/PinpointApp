# core/events.py
"""
Basic event bus for PinPoint.
Layer 2: Uses exceptions only.
"""

from typing import Dict, List, Callable, Any, Optional
import weakref
from .exceptions import PinPointError


class EventError(PinPointError):
    """Raised when event operations fail."""
    pass


class EventBus:
    """
    Simple event bus for decoupled communication.
    No logger dependency - uses print for debugging if enabled.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the event bus.
        
        Args:
            debug: If True, print debug messages
        """
        self._subscribers: Dict[str, List[weakref.ref]] = {}
        self._debug = debug
        
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event
            callback: Function to call when event is emitted
            
        Raises:
            EventError: If callback is not callable
        """
        if not callable(callback):
            raise EventError(f"Callback must be callable, got {type(callback)}")
            
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
            
        # Create weak reference to the callback
        # Note: This won't work with bound methods directly
        weak_callback = weakref.ref(callback)
        self._subscribers[event_name].append(weak_callback)
        
        if self._debug:
            print(f"EventBus: Subscribed to '{event_name}'")
            
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Name of the event
            callback: Function to unsubscribe
        """
        if event_name not in self._subscribers:
            return
            
        # Remove dead references and the specific callback
        cleaned_refs = []
        for ref in self._subscribers[event_name]:
            func = ref()
            if func is not None and func != callback:
                cleaned_refs.append(ref)
                
        self._subscribers[event_name] = cleaned_refs
        
        if self._debug:
            print(f"EventBus: Unsubscribed from '{event_name}'")
            
    def emit(self, event_name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event_name: Name of the event
            data: Optional data to pass to callbacks
        """
        if event_name not in self._subscribers:
            if self._debug:
                print(f"EventBus: No subscribers for '{event_name}'")
            return
            
        data = data or {}
        
        # Clean up dead references and call live ones
        live_refs = []
        for ref in self._subscribers[event_name]:
            callback = ref()
            if callback is not None:
                try:
                    callback({"event": event_name, "data": data})
                    live_refs.append(ref)
                except Exception as e:
                    if self._debug:
                        print(f"EventBus: Error in callback for '{event_name}': {e}")
                    # Continue with other callbacks
                    
        # Update subscribers list with only live references
        self._subscribers[event_name] = live_refs
        
        if self._debug:
            print(f"EventBus: Emitted '{event_name}' to {len(live_refs)} subscribers")
            
    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscribers.clear()
        if self._debug:
            print("EventBus: Cleared all subscriptions")
            
    def get_subscriber_count(self, event_name: str) -> int:
        """
        Get the number of active subscribers for an event.
        
        Args:
            event_name: Name of the event
            
        Returns:
            Number of active subscribers
        """
        if event_name not in self._subscribers:
            return 0
            
        # Count only live references
        count = 0
        for ref in self._subscribers[event_name]:
            if ref() is not None:
                count += 1
                
        return count
    

# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus

