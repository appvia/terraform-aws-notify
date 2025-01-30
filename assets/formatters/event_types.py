from enum import Enum
from typing import Dict, Tuple


class EventType(Enum):
    """
    Enumeration of supported event types and their display properties.
    Each event type has an associated emoji and display name.
    """

    SECURITY_HUB = ("🔒", "Security Alert")
    CLOUDWATCH = ("📊", "CloudWatch Alert")
    COST_ANOMALY = ("💰", "Cost Alert")
    CLOUDTRAIL = ("🔧", "CloudTrail Alert")
    AWS_BUDGETS = ("💵", "Budget Alert")
    UNKNOWN = ("🚨", "Alert")

    def __init__(self, emoji: str, display_name: str):
        self.emoji = emoji
        self.display_name = display_name


# Mapping of AWS event types to our enum
EVENT_TYPE_MAPPING: Dict[str, EventType] = {
    "securityhub": EventType.SECURITY_HUB,
    "cloudwatch_alarm": EventType.CLOUDWATCH,
    "cost_anomaly": EventType.COST_ANOMALY,
    "cloudtrail": EventType.CLOUDTRAIL,
    "aws_budgets": EventType.AWS_BUDGETS,
}
