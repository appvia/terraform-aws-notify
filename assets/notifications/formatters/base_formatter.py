from abc import ABC, abstractmethod
from typing import Dict, Any, Callable
from notifications.events import NormalizedEvent
from notifications.events.event_type import EventType, EVENT_TYPE_MAPPING

class BaseFormatter(ABC):
    """
    Base formatter class that implements the strategy pattern for formatting different event types.
    Concrete implementations should provide platform-specific formatting methods.
    """

    @abstractmethod
    def format(self, event: NormalizedEvent) -> Dict[str, Any]:
        """Format the message based on event type"""
        pass