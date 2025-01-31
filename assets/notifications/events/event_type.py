from enum import Enum
from typing import Dict


class EventType(Enum):
    """
    Enumeration of supported event types and their display properties.
    Each event type has an associated emoji and display name.
    """

    SECURITY_HUB = ("🔒", "Security Alert")
    GUARD_DUTY = ("🔒", "GuardDuty Alert")
    CLOUDWATCH = ("📊", "CloudWatch Alert")
    COST_ANOMALY = ("💰", "Cost Alert")
    AWS_BUDGETS = ("💵", "Budget Alert")
    UNKNOWN = ("🚨", "Alert")

    def __init__(self, emoji: str, display_name: str):
        self.emoji = emoji
        self.display_name = display_name


# Mapping of AWS event types to our enum
EVENT_TYPE_MAPPING: Dict[str, EventType] = {
    "aws_budgets": EventType.AWS_BUDGETS,
    "cloudwatch_alarm": EventType.CLOUDWATCH,
    "cost_anomaly": EventType.COST_ANOMALY,
    "guardduty": EventType.GUARD_DUTY,
    "securityhub": EventType.SECURITY_HUB,
}