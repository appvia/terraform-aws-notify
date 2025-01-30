from datetime import datetime
from ..events import EventParser, NormalizedEvent
import pytest


class TestEventParser:
    def setup_method(self):
        self.parser = EventParser()

    def test_parse_unknown_event(self):
        # Test handling of an unknown event type
        test_event = {
            "timestamp": "2024-03-20T12:00:00Z",
            "detail": {"some": "data"},
        }

        result = self.parser.parse_event(test_event)

        assert isinstance(result, NormalizedEvent)
        assert result.timestamp == datetime.fromisoformat("2024-03-20T12:00:00+00:00")
        assert result.raw_event == test_event

    def test_parse_event_missing_timestamp(self):
        # Test handling of events without timestamp
        test_event = {"detail": {"some": "data"}}

        with pytest.raises(ValueError) as exc_info:
            self.parser.parse_event(test_event)
        assert "Missing timestamp in event" in str(exc_info.value)

    def test_parse_event_invalid_timestamp(self):
        # Test handling of invalid timestamp format
        test_event = {"timestamp": "invalid-timestamp", "detail": {"some": "data"}}

        with pytest.raises(ValueError) as exc_info:
            self.parser.parse_event(test_event)
        assert "Invalid timestamp format" in str(exc_info.value)
