# Event Parsers

This directory contains event parsers that normalize different event types into a standardized format for the notification system.

## Adding Custom Event Parsers

To add support for parsing a new event type:

1. Create a parser function that converts your event into a `NormalizedEvent`
2. Update the parser configuration to register your new parser

### Parser Function

Create a function that takes your event data and returns a `NormalizedEvent`. The normalized event must include these required fields:

- `event_type`: The type of event (e.g., `EventType.CLOUDWATCH_ALARM`)
- `title`: A short title for the event
- `description`: A detailed description of the event
- `timestamp`: The timestamp of the event
- `severity`: The severity of the event (e.g., `"critical"`, `"high"`, `"medium"`, `"low"`, `"info"`, `"unknown"`)

### Parser Configuration

Update the `parser_cache` in `event_parser.py` to register your new parser.

```python
self._parser_cache = {
    EventType.AWS_BUDGETS: self._parse_aws_budgets,
    EventType.CLOUDWATCH: self._parse_cloudwatch_alarm,
    EventType.COST_ANOMALY: self._parse_cost_anomaly,
    EventType.SECURITY_HUB: self._parse_securityhub,
    EventType.GUARD_DUTY: self._parse_guardduty,
}
```

### Example

Here's an example of a custom parser for a new event type:

```python
def _parse_my_event(event: Dict[Any, Any]) -> NormalizedEvent:
    # Implement your parser logic here
    pass
```

### Example Configuration

Update the `parser_cache` in `event_parser.py` to register your new parser.

```python
self._parser_cache = {
    EventType.AWS_BUDGETS: self._parse_aws_budgets,
    EventType.MY_EVENT: self._parse_my_event, # Add your new event type here
}
```

### Example Usage

Here's an example of how to use the new event parser:

```python
event_parser = EventParser()
normalized_event = event_parser.parse_event(event)
```

### Testing

You can find a event generator in the `tests/test_event_generator.py`, which can be used to generate events of different types, print to screen of send the event to a SNS topic for live testing.

```
python scripts/event_generator.py <event_type>
```

You can use the `-h|--help` flag to see the available events and their usage.

```
python scripts/event_generator.py -h
```

You can send the event to a SNS topic for live testing.

```
python scripts/event_generator.py <event_type> -t <topic_name>
```

### Unit Testing Requirements

All event parsers must include comprehensive unit tests. Create your tests in the `tests/notifications/events/` directory following these guidelines:

1. Test file naming: `test_event_parser.py`
2. Required test cases:
   - Happy path with all required fields
   - Edge cases (null values, missing optional fields)
   - Invalid input handling

Example test structure:

```python
def test_parse_my_event_happy_path():
    input_event = {
        "event_type": "my_event",
        "title": "Expected Title",
        "description": "Expected Description",
        "timestamp": "2024-03-20T10:00:00Z",
        "severity": "medium",
        "source": "my_event",
        "detail": {"some": "data"}
    }

    result = event_parser._parse_my_event(self.get_sns_event(input_event))

    assert result.event_type == EventType.MY_EVENT
    assert result.title == "Expected Title"
    assert result.description == "Expected Description"
    assert result.timestamp == "2024-03-20T10:00:00Z"
    assert result.severity == "medium"
```
