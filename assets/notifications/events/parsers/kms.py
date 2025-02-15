from typing import Dict, Any
from datetime import datetime
from notifications.events.normalized_event import NormalizedEvent
from notifications.events.event_type import EventType, Severity
from notifications.events.parsers.base import BaseParser

class KMSParser(BaseParser):
    """ 
    Parses KMS deletion events into a normalized format.
    """
    
    def parse(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse a KMS deletion event into a normalized format.
        """
        
        message = self._get_message_body(event)
        detail = message.get("detail", {})
        
        return NormalizedEvent(
            event_type=EventType.KMS_DELETION, 
            severity=Severity.CRITICAL.value, 
            region=message.get("Region", "unknown"), 
            title="KMS CMK Deletion",
            description=message.get("Description", "No description provided"), 
            timestamp=datetime.fromisoformat(message.get("Time", datetime.now().isoformat()).replace("Z", "+00:00")), 
            source="KMS", 
            details={
                "key_arn": message.get("resources", [])[0],
                "key_id": detail.get("key-id"),
            }, 
            raw_event=event
        ) 