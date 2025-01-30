from typing import Dict, Any
from .base_formatter import BaseFormatter
from .event_types import EventType
from ..events import NormalizedEvent


class TeamsFormatter(BaseFormatter):
    """Formats messages for Microsoft Teams"""

    def _format_by_event_type(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Route to specific formatter based on event type"""
        formatters = {
            EventType.SECURITY_HUB: self._format_security_hub,
            EventType.CLOUDWATCH: self._format_cloudwatch,
            EventType.COST_ANOMALY: self._format_cost_anomaly,
            EventType.CLOUDTRAIL: self._format_cloudtrail,
            EventType.AWS_BUDGETS: self._format_budgets,
        }

        formatter = formatters.get(event_type, self._format_default)
        return formatter(event, event_type)

    def _format_default(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Default formatter for unknown event types"""
        facts = [
            {"name": "Type", "value": event_type.display_name},
            {"name": "Severity", "value": event.severity},
            {"name": "Source", "value": event.source},
        ]

        # Add all details as facts
        for k, v in event.details.items():
            facts.append({"name": k, "value": str(v)})

        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Large",
                                "weight": "Bolder",
                                "text": f"{event_type.emoji} {event.title}",
                                "wrap": True,
                            },
                            {
                                "type": "TextBlock",
                                "text": event.description,
                                "wrap": True,
                            },
                            {"type": "FactSet", "facts": facts},
                        ],
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.2",
                    },
                }
            ],
        }

    def _format_security_hub(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Format SecurityHub specific events"""
        facts = [
            {"name": "Severity", "value": event.severity},
            {"name": "Resource Type", "value": event.details.get("resource", "N/A")},
            {"name": "Region", "value": event.details.get("region", "N/A")},
            {
                "name": "Compliance",
                "value": event.details.get("compliance_status", "N/A"),
            },
        ]

        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Large",
                                "weight": "Bolder",
                                "text": f"{event_type.emoji} Security Alert: {event.title}",
                                "wrap": True,
                            },
                            {
                                "type": "TextBlock",
                                "text": event.description,
                                "wrap": True,
                            },
                            {"type": "FactSet", "facts": facts},
                        ],
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.2",
                    },
                }
            ],
        }

    def _format_cloudwatch(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Format CloudWatch specific events"""
        # Implementation for CloudWatch alerts
        pass

    def _format_cost_anomaly(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Format Cost Anomaly specific events"""
        # Implementation for Cost Anomaly alerts
        pass

    def _format_cloudtrail(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Format CloudTrail specific events"""
        # Implementation for CloudTrail alerts
        pass

    def _format_budgets(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Format AWS Budgets specific events"""
        # Implementation for Budget alerts
        pass
