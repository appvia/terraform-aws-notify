from typing import Dict, Any
from .base_formatter import BaseFormatter
from .event_types import EventType
from ..events import NormalizedEvent


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
        details_text = "\n".join([f"• {k}: {v}" for k, v in event.details.items()])

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
                            f"*Type:* {event_type.display_name}\n"
                            f"*Severity:* {event.severity}\n"
                            f"*Source:* {event.source}\n\n"
                            f"{event.description}"
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

    def _format_security_hub(
        self, event: NormalizedEvent, event_type: EventType
    ) -> Dict[str, Any]:
        """Format SecurityHub specific events"""
        color = self._get_severity_color(event.severity)
        details_text = "\n".join(
            [
                f"• Resource Type: {event.details.get('resource', 'N/A')}",
                f"• Region: {event.details.get('region', 'N/A')}",
                f"• Compliance: {event.details.get('compliance_status', 'N/A')}",
            ]
        )

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{event_type.emoji} Security Alert: {event.title}",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Severity:* {event.severity}\n{event.description}",
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Details:*\n{details_text}"},
                },
            ]
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
