from abc import ABC, abstractmethod
from typing import Dict, Any, Callable
from notifications.events import NormalizedEvent
from notifications.events.event_type import EventType, EVENT_TYPE_MAPPING

class BaseFormatter(ABC):
    """
    Base formatter class that implements the strategy pattern for formatting different event types.
    Concrete implementations should provide platform-specific formatting methods.
    """

    def format_message(self, event: NormalizedEvent) -> Dict[str, Any]:
        """
        Main entry point for formatting messages. Determines the event type and calls
        the appropriate formatter method.

        Args:
            event (NormalizedEvent): The normalized event to format

        Returns:
            Dict[str, Any]: The formatted message for the specific platform
        """
        event_type = self._get_event_type(event.event_type)
        return self._format_by_event_type(event, event_type)

    def _get_event_type(self, event_type: str) -> EventType:
        """Get the EventType enum for a given event type string."""
        return EVENT_TYPE_MAPPING.get(event_type, EventType.UNKNOWN)

    @abstractmethod
    def _format_by_event_type(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Format the message based on event type"""
        pass

    @abstractmethod
    def _format_default(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Default formatter for unknown event types"""
        pass
