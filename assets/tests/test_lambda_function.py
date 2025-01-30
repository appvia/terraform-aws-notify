import json
import pytest
import sys
from pathlib import Path

# Add the assets directory to Python path for imports
assets_dir = str(Path(__file__).parent.parent)
if assets_dir not in sys.path:
    sys.path.append(assets_dir)

from lambda_function import lambda_handler
from events import EventParser


def get_cloudwatch_alarm_event():
    """
    Generate a sample CloudWatch Alarm event wrapped in an SNS message format.

    Returns:
        Dict[str, Any]: A dictionary representing a CloudWatch Alarm event with test data,
        including alarm name, description, state changes, and timestamps.
    """
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {
                    "Message": json.dumps(
                        {
                            "AlarmName": "Test Alarm",
                            "AlarmDescription": "This is a test alarm",
                            "NewStateValue": "ALARM",
                            "OldStateValue": "OK",
                            "StateChangeTime": "2024-03-21T12:00:00Z",
                            "NewStateReason": "Threshold crossed",
                        }
                    )
                },
            }
        ]
    }


def get_securityhub_event():
    """
    Generate a sample SecurityHub finding event wrapped in an SNS message format.

    Returns:
        Dict[str, Any]: A dictionary representing a SecurityHub event with test data,
        including finding details, severity, resources, and compliance status.
    """
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {
                    "Message": json.dumps(
                        {
                            "detail-type": "Security Hub Findings - Imported",
                            "detail": {
                                "findings": [
                                    {
                                        "Title": "Security Finding",
                                        "Description": "Security issue detected",
                                        "Severity": {"Label": "HIGH"},
                                        "UpdatedAt": "2024-03-21T12:00:00Z",
                                        "Resources": [{"Type": "AWS::EC2::Instance"}],
                                        "Region": "us-east-1",
                                        "Compliance": {"Status": "FAILED"},
                                    }
                                ]
                            },
                        }
                    )
                },
            }
        ]
    }


def test_cloudwatch_alarm_processing():
    """
    Test the processing of a CloudWatch Alarm event through the lambda handler.

    Verifies that:
    - The lambda successfully processes the event
    - Returns a 200 status code
    - Includes a success message in the response

    Raises:
        AssertionError: If any of the assertions fail
    """
    event = get_cloudwatch_alarm_event()
    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert "Event processed successfully" in response["body"]


def test_securityhub_processing():
    """
    Test the processing of a SecurityHub event through the lambda handler.

    Verifies that:
    - The lambda successfully processes the event
    - Returns a 200 status code
    - Includes a success message in the response

    Raises:
        AssertionError: If any of the assertions fail
    """
    event = get_securityhub_event()
    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert "Event processed successfully" in response["body"]


def test_invalid_event():
    """
    Test the lambda handler's response to an invalid event structure.

    Verifies that:
    - The lambda raises a ValueError for invalid event formats

    Raises:
        AssertionError: If the ValueError is not raised as expected
    """
    event = {"invalid": "event"}
    with pytest.raises(ValueError):
        lambda_handler(event, None)


def test_missing_records():
    """
    Test the lambda handler's response to an event missing the Records field.

    Verifies that:
    - The lambda raises a ValueError for events without Records

    Raises:
        AssertionError: If the ValueError is not raised as expected
    """
    event = {}
    with pytest.raises(ValueError):
        lambda_handler(event, None)
