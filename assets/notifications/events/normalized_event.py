from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from .event_type import EventType


@dataclass
class NormalizedEvent:
    """
    Normalized representation of various AWS events.

    This class provides a standardized structure for different types of AWS events,
    making them easier to process and format consistently.

    Attributes:
        event_type (str): The type of AWS event (e.g., 'cloudwatch_alarm',
            'securityhub')
        severity (str): The severity level of the event
        title (str): A human-readable title for the event
        description (str): A detailed description of the event
        timestamp (datetime): When the event occurred
        source (str): The AWS service that generated the event
        details (Dict[str, Any]): Additional event-specific details
        raw_event (Dict[str, Any]): The original, unprocessed event
    """

    event_type: EventType
    severity: str
    title: str
    region: str
    description: str
    timestamp: datetime
    source: str
    details: Dict[str, Any]
    raw_event: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the normalized event to a dictionary suitable for JSON serialization.
        """
        return {
            "event_type": str(self.event_type),
            "severity": self.severity,
            "title": self.title,
            "region": self.region,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "details": self.details,
            "raw_event": self.raw_event,
        }
