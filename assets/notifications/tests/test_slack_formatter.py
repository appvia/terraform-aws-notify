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
                "current_value": "150"
            },
            raw_event={}
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
        assert len(result["blocks"]) == 4
        
        # Check header block
        header = result["blocks"][0]
        assert header["type"] == "header"
        assert "Test Alert" in header["text"]["text"]
        
        # Check main section block
        main_section = result["blocks"][1]
        assert main_section["type"] == "section"
        text = main_section["text"]["text"]
        assert "*Severity:* high" in text
        assert "*State:* ALARM" in text
        assert "*Threshold:* 100" in text
        assert "This is a test alert" in text
        
        # Check details section
        details_section = result["blocks"][2]
        assert details_section["type"] == "section"
        details_text = details_section["text"]["text"]
        assert "*Details:*" in details_text
        assert "• Metric Name: CPU Usage" in details_text
        assert "• Current Value: 150" in details_text
        
        # Check timestamp context
        timestamp_block = result["blocks"][3]
        assert timestamp_block["type"] == "context"
        assert "2024-01-01 12:00:00 UTC" in timestamp_block["elements"][0]["text"]