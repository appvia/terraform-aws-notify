from typing import Dict, Any
from .base_formatter import BaseFormatter
from notifications.events.event_type import EventType
from notifications.events import NormalizedEvent
from notifications.utils import format_key_name

class TeamsFormatter(BaseFormatter):
    """Formats messages for Microsoft Teams"""

    def format(
        self, event: NormalizedEvent
    ) -> Dict[str, Any]:
        """Route to specific formatter based on event type"""
        formatters = {
            #EventType.SECURITY_HUB: self._format_security_hub,
            #EventType.CLOUDWATCH: self._format_cloudwatch,
            #EventType.COST_ANOMALY: self._format_cost_anomaly,
            #EventType.CLOUDTRAIL: self._format_cloudtrail,
            #EventType.AWS_BUDGETS: self._format_budgets,
        }
        
        event_type = event.event_type
        formatter = formatters.get(event_type, self._format_default)
        
        return formatter(event, event_type)

    def _format_default(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Default formatter for unknown event types"""
        # Convert details into list of maps with formatted names
        facts = [
            {"name": format_key_name(k), "value": str(v)}
            for k, v in event.details.items()
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
