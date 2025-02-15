from enum import Enum
from typing import Dict


class EventType(Enum):
    """
    Enumeration of supported event types and their display properties.
    Each event type has an associated emoji and display name.
    """

    SECURITY_HUB = ("🔒", "Security Alert")
    GUARDDUTY = ("🔒", "GuardDuty Alert")
    CLOUDWATCH = ("📊", "CloudWatch Alert")
    CLOUDWATCH_EVENTBRIDGE = ("📊", "CloudWatch EventBridge Alert")
    KMS_DELETION = ("🔑", "KMS Deletion Alert")
    UNKNOWN = ("🚨", "Alert")

    def __init__(self, emoji: str, display_name: str):
        self.emoji = emoji
        self.display_name = display_name

class Severity(Enum):
    """
    Enumeration of supported severity levels and their display properties.
    Each severity level has an associated emoji and display name.
    """ 
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"
    

# Mapping of AWS event types to our enum
EVENT_TYPE_MAPPING: Dict[str, EventType] = {
    "cloudwatch_alarm": EventType.CLOUDWATCH,
    "guardduty": EventType.GUARDDUTY,
    "kms_deletion": EventType.KMS_DELETION,
    "securityhub": EventType.SECURITY_HUB,
}
