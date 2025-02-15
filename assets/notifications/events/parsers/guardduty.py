from typing import Dict, Any
from datetime import datetime
from notifications.events.normalized_event import NormalizedEvent
from notifications.events.event_type import EventType, Severity
from notifications.events.parsers.base import BaseParser

class GuardDutyParser(BaseParser):
    """
    Parses GuardDuty events into a normalized format.
    """
    
    def parse(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse a GuardDuty finding event into a normalized format.
        Extracts security-specific information such as severity, findings details, and affected resources.

        Args:
            event (Dict[Any, Any]): The GuardDuty event to parse

        Returns:
            NormalizedEvent: A normalized representation of the GuardDuty event
        """

        # Map GuardDuty severity levels to our severity levels
        severity_mapping = {
            1.0: Severity.LOW.value,
            2.0: Severity.LOW.value,
            3.0: Severity.LOW.value,
            4.0: Severity.MEDIUM.value,
            5.0: Severity.MEDIUM.value,
            6.0: Severity.HIGH.value,
            7.0: Severity.HIGH.value,
            8.0: Severity.CRITICAL.value,
            9.0: Severity.CRITICAL.value,
            10.0: Severity.CRITICAL.value,
        }

        message = self._get_message_body(event)
        finding = message.get("detail", {})
        severity = severity_mapping.get(finding.get("severity", 1.0), Severity.LOW.value)

        return NormalizedEvent(
            event_type=EventType.GUARDDUTY,
            severity=severity,
            region=finding.get("region"),
            title=finding.get("title", "Unknown GuardDuty Finding"),
            description=finding.get("description", "No description provided"),
            timestamp=datetime.fromisoformat(
                finding.get("updatedAt", finding.get("createdAt")).replace(
                    "Z", "+00:00"
                )
            ),
            source="GuardDuty",
            details={
                "finding_id": finding.get("id"),
                "finding_type": finding.get("type"),
                "region": finding.get("region"),
                "account_id": finding.get("accountId"),
                "resource_type": finding.get("resource", {}).get("resourceType"),
                "resource_id": finding.get("resource", {}).get("resourceId"),
            },
            raw_event=event,
        )
    