from typing import Dict, Any
import json
from datetime import datetime
from .normalized_event import NormalizedEvent


class EventParser:
    """
    Parses and normalizes different types of AWS events into a
    consistent format. This class handles various AWS event types
    and provides a default parser for unknown events.
    """

    def __init__(self):
        self._parser_cache = {}

    def parse_event(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """Parse event with proper timestamp validation"""
        # Validate timestamp first
        if "timestamp" not in event:
            raise ValueError("Missing timestamp in event")
            
        try:
            timestamp = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError("Invalid timestamp format")

        try:
            event_type = self._determine_event_type(event)
            
            if event_type not in self._parser_cache:
                parser_name = f"_parse_{event_type}"
                self._parser_cache[event_type] = getattr(self, parser_name, self._parse_default)
            
            return self._parser_cache[event_type](event)
            
        except ValueError as e:
            # Only catch event type determination errors
            print(f"Warning: {str(e)}. Using default parser.")
            return self._parse_default(event)

    def _determine_event_type(self, event: Dict[Any, Any]) -> str:
        """
        Determine the type of incoming AWS event based on its structure and content.

        Args:
            event (Dict[Any, Any]): The raw event to analyze

        Returns:
            str: The identified event type (e.g., 'cloudwatch_alarm', 'securityhub', etc.)

        Raises:
            ValueError: If the event type cannot be determined
        """
        # Check if it's an SNS wrapped message
        if "Records" in event and event["Records"][0]["EventSource"] == "aws:sns":
            message = json.loads(event["Records"][0]["Sns"]["Message"])
        else:
            message = event

        if "AlarmName" in message:
            return "cloudwatch_alarm"
        elif (
            "detail-type" in message
            and message["detail-type"] == "Security Hub Findings - Imported"
        ):
            return "securityhub"
        elif "anomalyDetectorArn" in str(message):
            return "cost_anomaly"
        elif "budgetType" in str(message):
            return "aws_budgets"
        elif (
            "detail-type" in message
            and "AWS API Call via CloudTrail" in message["detail-type"]
        ):
            return "cloudtrail"

        raise ValueError("Unknown event type")

    def _parse_default(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Default parser for handling unknown event types. Attempts to extract
        meaningful information from any AWS event structure.

        Args:
            event (Dict[Any, Any]): The raw event to parse

        Returns:
            NormalizedEvent: A normalized representation of the unknown event
        """
        message = self._get_message_body(event)
        source = self._extract_source(message)
        title = self._extract_title(message)
        description = self._extract_description(message)
        timestamp = self._extract_timestamp(message)
        severity = self._extract_severity(message)
        details = self._extract_details(message)

        return NormalizedEvent(
            event_type="unknown",
            severity=severity,
            title=title,
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
        return NormalizedEvent(
            event_type="cloudwatch_alarm",
            severity="critical" if message.get("NewStateValue") == "ALARM" else "info",
            title=message.get("AlarmName", "Unknown Alarm"),
            description=message.get("AlarmDescription", "No description provided"),
            timestamp=datetime.fromisoformat(
                message.get("StateChangeTime").replace("Z", "+00:00")
            ),
            source="CloudWatch",
            details={
                "reason": message.get("NewStateReason"),
                "previous_state": message.get("OldStateValue"),
                "current_state": message.get("NewStateValue"),
                "region": message.get("Region"),
            },
            raw_event=event,
        )

    def _parse_securityhub(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse a SecurityHub finding event into a normalized format.
        Extracts security-specific information such as severity, findings, and compliance status.

        Args:
            event (Dict[Any, Any]): The SecurityHub event to parse

        Returns:
            NormalizedEvent: A normalized representation of the SecurityHub event
        """
        finding = event["detail"]["findings"][0]
        return NormalizedEvent(
            event_type="securityhub",
            severity=finding.get("Severity", {}).get("Label", "UNKNOWN"),
            title=finding.get("Title"),
            description=finding.get("Description"),
            timestamp=datetime.fromisoformat(
                finding.get("UpdatedAt").replace("Z", "+00:00")
            ),
            source="SecurityHub",
            details={
                "resource": finding.get("Resources", [{}])[0].get("Type"),
                "region": finding.get("Region"),
                "compliance_status": finding.get("Compliance", {}).get("Status"),
            },
            raw_event=event,
        )

    def _parse_cost_anomaly(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """Parse Cost Anomaly event"""
        # Implementation needed
        raise NotImplementedError("Cost Anomaly parsing not implemented")

    def _parse_aws_budgets(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """Parse AWS Budgets event"""
        # Implementation needed
        raise NotImplementedError("AWS Budgets parsing not implemented")

    def _get_message_body(self, event: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Extract the message body from an event, handling SNS message wrapping if present.

        Args:
            event (Dict[Any, Any]): The event to process

        Returns:
            Dict[str, Any]: The extracted message body
        """
        if "Records" in event and event["Records"][0]["EventSource"] == "aws:sns":
            return json.loads(event["Records"][0]["Sns"]["Message"])
        return event
