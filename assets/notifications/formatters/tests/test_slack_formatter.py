import pytest
from datetime import datetime, timezone
from notifications.events import NormalizedEvent
from notifications.events.event_type import EventType
from notifications.formatters.slack_formatter import SlackFormatter


class TestSlackFormatter:
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.formatter = SlackFormatter()
        self.sample_event = NormalizedEvent(
            title="Test Alert",
            description="This is a test alert",
            event_type=EventType.CLOUDWATCH,
            severity="high",
            region="us-east-1",
            source="aws.cloudwatch",
            timestamp=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            details={
                "state": "ALARM",
                "threshold": "100",
                "metric_name": "CPU Usage",
                "current_value": "150",
            },
            raw_event={},
        )

    def test_get_severity_color(self):
        """Test severity color mapping"""
        assert self.formatter._get_severity_color("critical") == "#FF0000"
        assert self.formatter._get_severity_color("high") == "#FFA500"
        assert self.formatter._get_severity_color("medium") == "#FFFF00"
        assert self.formatter._get_severity_color("low") == "#00FF00"
        assert self.formatter._get_severity_color("info") == "#0000FF"
        assert self.formatter._get_severity_color("unknown") == "#808080"

    def test_format(self):
        """Test default message formatting"""
        result = self.formatter.format(self.sample_event)

        # Check the basic structure
        assert isinstance(result, dict)
        assert "blocks" in result
        assert len(result["blocks"]) == 6