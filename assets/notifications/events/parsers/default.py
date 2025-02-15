from typing import Dict, Any
import json
from datetime import datetime
from notifications.events.normalized_event import NormalizedEvent
from notifications.events.parsers.base import BaseParser

class DefaultParser(BaseParser):
    """ 
    Default parser for handling unknown event types. Attempts to extract
    meaningful information from any AWS event structure.
    """
    
    def parse(self, event: Dict[Any, Any]) -> NormalizedEvent:
        message = self._get_message_body(event)
        source = self._extract_source(message)
        title = self._extract_title(message)
        description = self._extract_description(message)
        timestamp = self._extract_timestamp(message)
        severity = self._extract_severity(message)
        details = self._extract_details(message)
        region = message.get("TopicArn", ":::unknown:::").split(":")[3]
        subject = message.get("Subject")

        return NormalizedEvent(
            event_type="unknown",
            severity=severity,
            subject=subject,
            title=title,
            region=region,
            description=description,
            timestamp=timestamp,
            source=source,
            details=details,
            raw_event=event,
        )
    
    def _extract_source(self, message: Dict[str, Any]) -> str:
        """
        Extract the source of the event from various possible fields in the message.

        Args:
            message (Dict[str, Any]): The event message to analyze

        Returns:
            str: The identified source of the event, or 'Unknown Source' if not found
        """
        # Try common AWS event source fields
        for field in [
            "source",
            "eventSource",
            "detail-type",
            "configurationItem",
            "Service",
        ]:
            if field in message:
                return str(message[field])

        # If no source found, check if it's in a nested structure
        if "detail" in message and isinstance(message["detail"], dict):
            for field in ["eventSource", "service", "source"]:
                if field in message["detail"]:
                    return str(message["detail"][field])

        return "Unknown Source"

    def _extract_title(self, message: Dict[str, Any]) -> str:
        """
        Extract a meaningful title from the event message by checking various common fields.

        Args:
            message (Dict[str, Any]): The event message to analyze

        Returns:
            str: The extracted title, or 'Unknown Event' if no suitable title found
        """
        # Try common title fields
        for field in ["eventName", "detail-type", "configurationItemStatus", "Event"]:
            if field in message:
                return str(message[field])

        # Check in detail
        if "detail" in message and isinstance(message["detail"], dict):
            for field in ["eventName", "eventType", "name"]:
                if field in message["detail"]:
                    return str(message["detail"][field])

        return "Unknown Event"

    def _extract_description(self, message: Dict[str, Any]) -> str:
        """
        Create a meaningful description from the event message.
        For events with 'detail' field, formats it as JSON. Otherwise, creates a basic description.

        Args:
            message (Dict[str, Any]): The event message to analyze

        Returns:
            str: A formatted description of the event
        """
        # Try to create a meaningful description from available fields
        if "detail" in message and isinstance(message["detail"], dict):
            return f"Event details: {json.dumps(message['detail'], indent=2)}"

        # If no detail field, use the message itself
        return f"Raw event received from {self._extract_source(message)}"

    def _extract_timestamp(self, message: Dict[str, Any]) -> datetime:
        """
        Extract the timestamp from the event message, handling various AWS timestamp formats.

        Args:
            message (Dict[str, Any]): The event message to analyze

        Returns:
            datetime: The extracted timestamp, or current UTC time if no timestamp found
        """
        # Try common timestamp fields
        for field in ["time", "eventTime", "timestamp", "configurationItemCaptureTime"]:
            if field in message:
                try:
                    # Handle different timestamp formats
                    timestamp_str = message[field].replace("Z", "+00:00")
                    return datetime.fromisoformat(timestamp_str)
                except (ValueError, AttributeError):
                    continue

        # If no timestamp found, use current time
        return datetime.utcnow()

    def _extract_severity(self, message: Dict[str, Any]) -> str:
        """
        Extract the severity level from the event message by checking various
        severity-related fields.

        Args:
            message (Dict[str, Any]): The event message to analyze

        Returns:
            str: The extracted severity level, or 'info' if no severity found
        """
        # Try common severity/criticality fields
        for field in ["severity", "criticality", "priority"]:
            if field in message:
                return str(message[field])

            # Check in detail
            if "detail" in message and isinstance(message["detail"], dict):
                if field in message["detail"]:
                    return str(message["detail"][field])

        return "info"  # Default severity

    def _extract_details(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant details from the event message, including AWS-specific fields.
        Collects information such as region, account, and various event-specific fields.

        Args:
            message (Dict[str, Any]): The event message to analyze

        Returns:
            Dict[str, Any]: A dictionary of relevant event details
        """
        details = {}

        # Add relevant fields to details
        if "detail" in message and isinstance(message["detail"], dict):
            details.update(message["detail"])

        # Add region if available
        if "region" in message:
            details["region"] = message["region"]

        # Add account if available
        if "account" in message:
            details["account"] = message["account"]

        # Add any other relevant top-level fields
        relevant_fields = [
            "eventType",
            "eventName",
            "userIdentity",
            "requestParameters",
            "responseElements",
        ]
        for field in relevant_fields:
            if field in message:
                details[field] = message[field]

        return details