from typing import Dict, Any
from datetime import datetime
from notifications.events.normalized_event import NormalizedEvent
from notifications.events.event_type import EventType, Severity
from notifications.events.parsers.base import BaseParser

class CloudWatchParser(BaseParser):
    """ 
    Parses CloudWatch events into a normalized format.
    """
    def parse(self, event: Dict[Any, Any]) -> NormalizedEvent:
        message = self._get_message_body(event)
        
        if "AlarmName" in message:
            return self._parse_cloudwatch_alarm(event)
        return self._parse_cloudwatch_eventbridge(event)
    
    def _parse_cloudwatch_alarm(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse a CloudWatch Alarm event into a normalized format.
        Extracts alarm-specific information such as state changes and reasons.

        Args:
            event (Dict[Any, Any]): The CloudWatch Alarm event to parse

        Returns:
            NormalizedEvent: A normalized representation of the CloudWatch Alarm event
        """
        message = self._get_message_body(event)
        severity = (Severity.CRITICAL if message.get("NewStateValue") == "ALARM" else Severity.INFO).value

        return NormalizedEvent(
            event_type=EventType.CLOUDWATCH,
            severity=severity,
            region=message.get("Region", "unknown"),
            title=message.get("AlarmName", "Unknown Alarm"),
            description=message.get("AlarmDescription", "No description provided22"),
            timestamp=datetime.fromisoformat(
                message.get("StateChangeTime").replace("Z", "+00:00")
            ),
            source="CloudWatch",
            details={
                "reason": message.get("NewStateReason"),
                "previous_state": message.get("OldStateValue"),
                "current_state": message.get("NewStateValue"),
            },
            raw_event=event,
        )

    def _parse_cloudwatch_eventbridge(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse a CloudWatch EventBridge event into a normalized format.
        """
        message = self._get_message_body(event) 
        detail = message.get("detail", {})
        configuration = detail.get("configuration", {})
        state = detail.get("state", {})
        previous_state = detail.get("previousState", {})
        severity=(Severity.CRITICAL if state.get("value") == "ALARM" else Severity.INFO).value
       
        return NormalizedEvent(
            event_type=EventType.CLOUDWATCH,
            severity=severity,
            region=message.get("region", "unknown"),
            title=detail.get("alarmName", "Unknown Alarm"),
            description=configuration.get("description", "No description provided121"),
            timestamp=datetime.fromisoformat(
                state.get("timestamp", datetime.now().isoformat()).replace("Z", "+00:00")
            ),
            source="CloudWatch",
            details={
                "reason": state.get("reason"),
                "previous_state": previous_state.get("value"),
                "current_state": state.get("value"),
                "resources": message.get("resources", []),
            },
            raw_event=event,
        )   