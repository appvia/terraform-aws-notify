import json
import pytest
import sys
from pathlib import Path
import os
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Request, Response

# Add the assets directory to Python path for imports
assets_dir = str(Path(__file__).parent.parent)
if assets_dir not in sys.path:
    sys.path.append(assets_dir)

from notifications.lambda_function import lambda_handler
from notifications.events import EventParser


class TestLambdaFunction:
    def setup_method(self):
        self.parser = EventParser()
        
    @pytest.fixture(autouse=True)
    def setup_test_env(self, httpserver: HTTPServer):
        """
        Fixture to set up test environment variables and HTTP server before each test.
        The autouse=True ensures this runs automatically for each test.
        """
        original_environ = dict(os.environ)
        
        # Configure environment to use our test server
        os.environ['SLACK_WEBHOOK_URL'] = httpserver.url_for('/')
        os.environ['NOTIFICATION_PLATFORM'] = 'slack'
        
        # Configure server to capture Slack messages
        httpserver.expect_request("/",method="POST"
        ).respond_with_response(Response(status=200))
        
        yield httpserver  # This runs the test
        
        # Cleanup after test
        os.environ.clear()
        os.environ.update(original_environ)
        
    def get_sns_event(self, message):
        """Helper to wrap a message in SNS format"""
        return {
            "Records": [
                {
                    "EventSource": "aws:sns",
                    "Sns": {
                        "Message": json.dumps(message),
                    },
                },
            ],
        }

    def get_securityhub_event(self):
        """
        Generate a sample SecurityHub finding event wrapped in an SNS message format.

        Returns:
            Dict[str, Any]: A dictionary representing a SecurityHub event with test data,
            including finding details, severity, resources, and compliance status.
        """
        
        return self.get_sns_event(json.dumps({
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
                        "timestamp": "2024-03-21T12:00:00Z"
                    }
                ]
            },
        }))


    #def test_cloudwatch_alarm_processing():
    #    """
    #    Test the processing of a CloudWatch Alarm event through the lambda handler.
    #
    #    Verifies that:
    #    - The lambda successfully processes the event
    #    - Returns a 200 status code
    #    - Includes a success message in the response
    #
    #    Raises:
    #        AssertionError: If any of the assertions fail
    #    """
    #    event = get_cloudwatch_alarm_event()
    #    response = lambda_handler(event, None)
    #
    #    assert response["statusCode"] == 200
    #    assert "Event processed successfully" in response["body"]
    #
    #
    #def test_securityhub_processing():
    #    """
    #    Test the processing of a SecurityHub event through the lambda handler.
    #
    #    Verifies that:
    #    - The lambda successfully processes the event
    #    - Returns a 200 status code
    #    - Includes a success message in the response
    #
    #    Raises:
    #        AssertionError: If any of the assertions fail
    #    """
    #    event = get_securityhub_event()
    #    response = lambda_handler(event, None)
    #
    #    assert response["statusCode"] == 200
    #    assert "Event processed successfully" in response["body"]
    #
    #
    #def test_invalid_event():
    #    """
    #    Test the lambda handler's response to an invalid event structure.
    #
    #    Verifies that:
    #    - The lambda raises a ValueError for invalid event formats
    #
    #    Raises:
    #        AssertionError: If the ValueError is not raised as expected
    #    """
    #    event = {"invalid": "event"}
    #    with pytest.raises(ValueError):
    #        lambda_handler(event, None)
    #
    #
    #def test_missing_records():
    #    """
    #    Test the lambda handler's response to an event missing the Records field.
    #
    #    Verifies that:
    #    - The lambda raises a ValueError for events without Records
    #
    #    Raises:
    #        AssertionError: If the ValueError is not raised as expected
    #    """
    #    event = {}
    #    with pytest.raises(ValueError):
    #        lambda_handler(event, None)
    #
    def test_webhook_url_configuration(self, httpserver: HTTPServer):
        """
        Test that the lambda handler correctly sends notifications to the webhook URL.

        Verifies that:
        - The lambda can access the SLACK_WEBHOOK_URL from environment variables
        - The notification is properly sent to the webhook
        - The webhook receives the expected payload
        """
        
        test_event = self.get_sns_event({
            "AlarmName": "Test Alarm",
            "AlarmDescription": "This is a test alarm",
            "NewStateValue": "ALARM",
            "OldStateValue": "OK",
            "StateChangeTime": "2024-03-21T12:00:00Z",
            "NewStateReason": "Threshold crossed",
            "Region": "us-east-1"
        })
        
        # Test with a CloudWatch event to ensure end-to-end processing
        response = lambda_handler(test_event, None)
        
        # Verify the response
        assert response["statusCode"] == 200
        assert response["body"] == '{"message": "Notification sent successfully"}'
        
        # Verify that the webhook received exactly one request
        assert len(httpserver.log) == 1
        
        # Verify the request payload (assuming JSON payload)
        request: Request = httpserver.log[0][0]
        assert request.headers['Content-Type'] == 'application/json'
        payload = json.loads(request.get_data(as_text=True))
        assert payload is not None

