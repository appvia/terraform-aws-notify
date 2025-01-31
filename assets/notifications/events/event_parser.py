from typing import Dict, Any
import json
from datetime import datetime
from .normalized_event import NormalizedEvent
from .event_type import EventType


class EventParser:
    """
    Parses and normalizes different types of AWS events into a
    consistent format. This class handles various AWS event types
    and provides a default parser for unknown events.
    """

    def __init__(self):
        self._parser_cache = {
            EventType.AWS_BUDGETS: self._parse_aws_budgets, 
            EventType.CLOUDWATCH: self._parse_cloudwatch_alarm,
            EventType.COST_ANOMALY: self._parse_cost_anomaly,
            EventType.SECURITY_HUB: self._parse_securityhub,
            EventType.GUARD_DUTY: self._parse_guardduty,
        }

    def parse_event(self, event: Dict[Any, Any]) -> NormalizedEvent:
        event_type = self._determine_event_type(event)
        
        # step: we always use the default parser if the event type is not in the cache
        if not event_type in self._parser_cache:
            return self._parse_default(event)
        
        return self._parser_cache[event_type](event)
    
    def _is_sns_event(self, event: Dict[Any, Any]) -> bool:
        """Check if the event is an SNS event"""
        if not "Records" in event or len(event["Records"]) <= 0:
            return False
        if not "EventSource" in event["Records"][0] or event["Records"][0]["EventSource"] != "aws:sns":
           return False
        if not "Sns" in event["Records"][0]:
            return False
        
        return True

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
        if not self._is_sns_event(event):
            raise ValueError("Unknown event source, not aws:sns")
        
        message = json.loads(event["Records"][0]["Sns"]["Message"])
        
        if "AlarmName" in message:
            return EventType.CLOUDWATCH
        elif message.get("source") == "aws.securityhub":
            return EventType.SECURITY_HUB
        elif message.get("source") == "aws.budgets":
            return EventType.AWS_BUDGETS
        elif message.get("source") == "aws.ce":
            return EventType.COST_ANOMALY
        elif message.get("source") == "aws.guardduty":
            return EventType.GUARD_DUTY 
        
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
            event_type=EventType.CLOUDWATCH,
            severity="critical" if message.get("NewStateValue") == "ALARM" else "info",
            region=message.get("Region", "unknown"),
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
        message = self._get_message_body(event)
        finding = message["detail"]["findings"][0]
        return NormalizedEvent(
            event_type=EventType.SECURITY_HUB,
            severity=finding.get("Severity", {}).get("Label", "UNKNOWN").lower(),
            region=finding.get("Region"), 
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
        """
        Parse a Cost Anomaly event into a normalized format.
        Extracts cost-specific information such as impact, root causes, and anomaly details.

        Args:
            event (Dict[Any, Any]): The Cost Anomaly event to parse

        Returns:
            NormalizedEvent: A normalized representation of the Cost Anomaly event
        """
        message = self._get_message_body(event)
        detail = message.get("detail", {})
        anomaly_details = detail.get("anomalyDetails", {})
        
        # Calculate total impact
        total_impact = float(anomaly_details.get("totalImpact", 0))
        
        # Determine severity based on cost impact
        severity = "low"
        if total_impact >= 1000:
            severity = "critical"
        elif total_impact >= 100:
            severity = "high"
        elif total_impact >= 10:
            severity = "medium"

        return NormalizedEvent(
            event_type=EventType.COST_ANOMALY,
            severity=severity,
            region=anomaly_details.get("region", "Unknown"),
            title=f"Cost Anomaly: ${total_impact:,.2f} Impact Detected",
            description=anomaly_details.get("rootCauses", ["No root cause identified"])[0],
            timestamp=datetime.fromisoformat(
                anomaly_details.get("anomalyStartTime").replace("Z", "+00:00")
            ),
            source="AWS Cost Anomaly Detection",
            details={
                "impact": total_impact,
                "region": anomaly_details.get("region", "Unknown"),
                "service": anomaly_details.get("service", "Unknown"),
                "anomaly_end_time": anomaly_details.get("anomalyEndTime"),
                "root_causes": anomaly_details.get("rootCauses", []),
                "monitor_arn": detail.get("monitorArn"),
            },
            raw_event=event,
        )

    def _parse_aws_budgets(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse an AWS Budgets event into a normalized format.
        Extracts budget-specific information such as threshold, actual/forecasted spend, and budget details.

        Args:
            event (Dict[Any, Any]): The AWS Budgets event to parse

        Returns:
            NormalizedEvent: A normalized representation of the AWS Budgets event
        """
        message = self._get_message_body(event)
        
        # Extract account ID from the budgetNotification
        account_id = message.get("account")
        
        # Get budget details
        detail = message.get("detail", {})
        budget_name = detail.get("budgetName", "Unknown Budget")
        actual_spend = float(detail.get("actualSpend", {}).get("amount", 0))
        budget_limit = float(detail.get("budgetLimit", {}).get("amount", 0))
        threshold = float(detail.get("thresholdExceeded", 0))
        
        # Calculate percentage of budget used
        budget_percentage = (actual_spend / budget_limit * 100) if budget_limit > 0 else 0
        
        # Determine severity based on threshold
        severity = "low"
        if threshold >= 100:
            severity = "critical"
        elif threshold >= 90:
            severity = "high"
        elif threshold >= 80:
            severity = "medium"

        return NormalizedEvent(
            event_type=EventType.AWS_BUDGETS,
            severity=severity,
            region=message.get("region"),
            title=f"Budget Alert: {budget_name} at {threshold:.1f}% threshold",
            description=f"Budget {budget_name} has reached {budget_percentage:.1f}% of limit (${actual_spend:,.2f} / ${budget_limit:,.2f})",
            timestamp=datetime.fromisoformat(message.get("time").replace("Z", "+00:00")),
            source="AWS Budgets",
            details={
                "account_id": account_id,
                "budget_name": budget_name,
                "actual_spend": actual_spend,
                "budget_limit": budget_limit,
                "threshold": threshold,
                "time_unit": message.get("timeUnit"),
                "notification_type": message.get("notificationType"),
            },
            raw_event=event,
        )

    def _parse_guardduty(self, event: Dict[Any, Any]) -> NormalizedEvent:
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
            1.0: "low",
            2.0: "low",
            3.0: "low",
            4.0: "medium",
            5.0: "medium",
            6.0: "medium",
            7.0: "high",
            8.0: "high",
            9.0: "critical",
            10.0: "critical"
        }
        
        message = self._get_message_body(event)
        finding = message.get("detail", {})
        severity = severity_mapping.get(finding.get("severity", 1.0), "low")
        
        return NormalizedEvent(
            event_type=EventType.GUARD_DUTY,
            severity=severity,
            region=finding.get("region"),
            title=finding.get("title", "Unknown GuardDuty Finding"),
            description=finding.get("description", "No description provided"),
            timestamp=datetime.fromisoformat(
                finding.get("updatedAt", finding.get("createdAt")).replace("Z", "+00:00")
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
