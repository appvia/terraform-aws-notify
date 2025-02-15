from typing import Dict, Any
import json
from datetime import datetime
from .normalized_event import NormalizedEvent
from .event_type import EventType, Severity
from notifications.events.parsers.cloudwatch import CloudWatchParser
from notifications.events.parsers.securityhub import SecurityParser
from notifications.events.parsers.kms import KMSParser
from notifications.events.parsers.default import DefaultParser
from notifications.events.parsers.guardduty import GuardDutyParser


class EventParser:
    """
    Parses and normalizes different types of AWS events into a
    consistent format. This class handles various AWS event types
    and provides a default parser for unknown events.
    """

    def __init__(self):
        self._cloudwatch_parser = CloudWatchParser()
        self._security_parser = SecurityParser()
        self._kms_parser = KMSParser()
        self._default_parser = DefaultParser()
        
        self._parser_cache = {
            EventType.CLOUDWATCH: CloudWatchParser().parse,
            EventType.SECURITY_HUB: SecurityParser().parse,
            EventType.GUARDDUTY: GuardDutyParser().parse,
            EventType.KMS_DELETION: KMSParser().parse,
        }

    def parse_event(self, event: Dict[Any, Any]) -> NormalizedEvent:
        """
        Parse an incoming event into a normalized format.

        Args:
            event (Dict[Any, Any]): The incoming event to parse

        Returns:
            NormalizedEvent: A normalized representation of the incoming event
        """
        event_type = self._determine_event_type(event)

        # step: we always use the default parser if the event type is not in the cache
        if not event_type in self._parser_cache:
            return self._default_parser.parse_default(event)

        return self._parser_cache[event_type](event)

    
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

        if "AlarmName" in message or message.get("detail-type", "") == "CloudWatch Alarm State Change":
            return EventType.CLOUDWATCH
        elif message.get("detail-type") == "Security Hub Findings - Imported":
            return EventType.SECURITY_HUB
        elif message.get("detail-type", "") == "GuardDuty Finding":
            return EventType.GUARDDUTY
        elif message.get("detail-type", "") == "KMS CMK Deletion":
            return EventType.KMS_DELETION

        raise ValueError("Unknown event type")
    

    def _is_sns_event(self, event: Dict[Any, Any]) -> bool:
        """
        Check if the event is an SNS event
        """
        if not "Records" in event or len(event["Records"]) <= 0:
            return False
        if (
            not "EventSource" in event["Records"][0]
            or event["Records"][0]["EventSource"] != "aws:sns"
        ):
            return False
        if not "Sns" in event["Records"][0]:
            return False

        return True
