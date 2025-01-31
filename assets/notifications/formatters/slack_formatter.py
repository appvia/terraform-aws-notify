from typing import Dict, Any
from .base_formatter import BaseFormatter
from notifications.events import NormalizedEvent
from notifications.events.event_type import EventType
from notifications.utils import format_key_name



class SlackFormatter(BaseFormatter):
    """Formats messages for Slack"""

    def _get_severity_color(self, severity: str) -> str:
        """
        Get the color code for a given severity level.

        Args:
            severity (str): The severity level of the event

        Returns:
            str: Hex color code corresponding to the severity level
        """
        severity_colors = {
            "critical": "#FF0000",
            "high": "#FFA500",
            "medium": "#FFFF00",
            "low": "#00FF00",
            "info": "#0000FF",
        }
        return severity_colors.get(severity.lower(), "#808080")

    def format(
        self, event: NormalizedEvent
    ) -> Dict[str, Any]:
        """Route to specific formatter based on event type"""
        # If you want to override an add a custom formatter, you can do so here
        # by adding a new key to the formatters dictionary
        formatters = {
            # EventType.AWS_BUDGETS: self._format_budgets,
            # EventType.CLOUDWATCH: self._format_cloudwatch,
            # EventType.COST_ANOMALY: self._format_cost_anomaly,
            # EventType.SECURITY_HUB: self._format_security_hub,
        }

        event_type = event.event_type
        formatter = formatters.get(event_type, self._format_default)
        
        return formatter(event, event_type)

    def _format_default(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Default formatter for unknown event types"""
        # Format each detail key-value pair as a bullet point 
        details_text = "\n".join([
            f"• {format_key_name(k)}: {v}"
            for k, v in event.details.items()
        ])

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{event_type.emoji} {event.title}",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Severity:* {event.severity}\n"
                            + (f"*State:* {event.details.get('state')}\n" if event.details.get('state') else "")
                            + (f"*Threshold:* {event.details.get('threshold')}\n" if event.details.get('threshold') else "")
                            + f"\n{event.description}"
                        ),
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Details:*\n{details_text}"},
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🕐 {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                        }
                    ],
                },
            ]
        }