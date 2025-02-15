from typing import Dict, Any
from datetime import datetime
from notifications.events.normalized_event import NormalizedEvent
from notifications.events.event_type import EventType, Severity
from notifications.events.parsers.base import BaseParser

class SecurityParser(BaseParser):
    """
    Parses SecurityHub and GuardDuty events into a normalized format.
    """
    
    def parse(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse a SecurityHub finding event into a normalized format.
        Extracts security-specific information such as severity, findings, and compliance status.

        Args:
            event (Dict[Any, Any]): The SecurityHub event to parse

        Returns:
            NormalizedEvent: A normalized representation of the SecurityHub event
        """
        message = self._get_message_body(event)
        finding = message["detail"]["findings"][0]
        details = {}
        
        if finding.get("Remediation", {}).get("Recommendation", {}).get("Text"):
            details["remediation"] = finding.get("Remediation", {}).get("Recommendation", {}).get("Text")
       
        if finding.get("Workflow", {}).get("Status") is not None:
            details["status"] = finding.get("Workflow", {}).get("Status")   
       
        if finding.get("Resources", None) is not None: 
            details["resources"] = []
            for resource in finding.get("Resources", []):
                details["resources"].append({
                    "type": resource.get("Type"),
                    "region": resource.get("Region"),
                    "resource_id": resource.get("Id"),
                })
        
        return NormalizedEvent(
            event_type=EventType.SECURITY_HUB,
            severity=finding.get("Severity", {}).get("Label", Severity.UNKNOWN.value).lower(),
            region=finding.get("Region"),
            title=finding.get("Title"),
            description=finding.get("Description"),
            timestamp=datetime.fromisoformat(
                finding.get("UpdatedAt", datetime.now().isoformat()).replace("Z", "+00:00")
            ),
            source="SecurityHub",
            details=details,
            raw_event=event,
        )