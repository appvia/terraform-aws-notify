import pytest
from datetime import datetime, timezone
from notifications.events import NormalizedEvent
from notifications.events.event_type import EventType
from notifications.formatters.teams_formatter import TeamsFormatter


class TestTeamsFormatter:
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.formatter = TeamsFormatter()
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

    def test_format_default(self):
        """Test the default formatting of events"""
        result = self.formatter.format(self.sample_event)

        assert result["type"] == "message"
        assert len(result["attachments"]) == 1
        
        content = result["attachments"][0]["content"]
        assert content["type"] == "AdaptiveCard"
        assert content["version"] == "1.2"
        
        body = content["body"]
        print(body)
        assert body[0]["text"] == f"{EventType.CLOUDWATCH.emoji} Test Alert"
        assert body[1]["text"] == "This is a test alert"
        assert body[2]["type"] == "FactSet"
        assert body[2]["facts"][0]["name"] == "State"
        assert body[2]["facts"][0]["value"] == "ALARM"
        assert body[2]["facts"][1]["name"] == "Threshold"
        assert body[2]["facts"][1]["value"] == "100"
        assert body[2]["facts"][2]["name"] == "Metric Name"
        assert body[2]["facts"][2]["value"] == "CPU Usage"
        assert body[2]["facts"][3]["name"] == "Current Value"
        assert body[2]["facts"][3]["value"] == "150"


    def test_format_with_empty_details(self):
        """Test formatting when details are empty"""
        result = self.formatter.format(self.sample_event)
        
        content = result["attachments"][0]["content"]
        facts = content["body"][2]["facts"]
        assert len(facts) == 4

    def test_format_with_non_string_values(self):
        """Test formatting when details contain non-string values"""
        result = self.formatter.format(self.sample_event)
        
        content = result["attachments"][0]["content"]
        facts = content["body"][2]["facts"]
        assert len(facts) == 4
        assert facts[0]["name"] == "State"
        assert facts[0]["value"] == "ALARM"
        assert facts[1]["name"] == "Threshold"
        assert facts[1]["value"] == "100"
        assert facts[2]["name"] == "Metric Name"
        assert facts[2]["value"] == "CPU Usage"
        assert facts[3]["name"] == "Current Value"
        assert facts[3]["value"] == "150"
