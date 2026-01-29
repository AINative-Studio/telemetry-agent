"""
Event System for State Changes

Handles synchronous, local-only events when state changes occur.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Callable, Dict, Any, List
from datetime import datetime


class EventType(Enum):
    """Event types emitted by the agent"""
    MODEL_CHANGED = "model_changed"
    WORKSPACE_CHANGED = "workspace_changed"
    BRANCH_CHANGED = "branch_changed"
    CONTEXT_THRESHOLD = "context_threshold"
    STATE_UPDATED = "state_updated"


@dataclass
class StateChangeEvent:
    """State change event"""
    event_type: EventType
    timestamp: str
    old_value: Any
    new_value: Any
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "metadata": self.metadata or {}
        }


class EventEmitter:
    """
    Event emitter for state changes

    Supports synchronous callbacks for local event handling.
    """

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }

    def on(self, event_type: EventType, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Register event handler

        Args:
            event_type: Type of event to listen for
            callback: Callback function that receives StateChangeEvent
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Unregister event handler

        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self._handlers and callback in self._handlers[event_type]:
            self._handlers[event_type].remove(callback)

    def emit(self, event: StateChangeEvent) -> None:
        """
        Emit event to all registered handlers

        Args:
            event: StateChangeEvent to emit
        """
        handlers = self._handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Gracefully handle callback errors
                print(f"Error in event handler: {e}")

    def clear(self, event_type: EventType = None) -> None:
        """
        Clear event handlers

        Args:
            event_type: Optional specific event type to clear (if None, clears all)
        """
        if event_type:
            self._handlers[event_type] = []
        else:
            for et in EventType:
                self._handlers[et] = []
