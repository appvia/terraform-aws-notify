from typing import Dict, Any
from abc import ABC, abstractmethod
from notifications.events.normalized_event import NormalizedEvent
import json

class BaseParser:
    def _get_message_body(self, event: Dict[Any, Any]) -> Dict[str, Any]:
        """Extract the message body from an event, handling SNS message wrapping if present."""
        if "Records" in event and event["Records"][0]["EventSource"] == "aws:sns":
            return json.loads(event["Records"][0]["Sns"]["Message"])
        return event 
    
    @abstractmethod
    def parse(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """Parse an event into a normalized format."""
        pass
