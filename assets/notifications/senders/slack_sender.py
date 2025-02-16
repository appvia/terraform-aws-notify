import json
import urllib.request
import urllib.error
from typing import Dict, Any
from .base_sender import MessageSender


class SlackSender(MessageSender):
    """Handles sending messages to Slack.

    A concrete implementation of MessageSender that sends messages to Slack
    using webhook URLs.
    """

    def __init__(self, webhook_url: str):
        """Initialize the Slack message sender.

        Args:
            webhook_url (str): The Slack webhook URL to send messages to.
        """
        self.webhook_url = webhook_url

    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send a formatted message to Slack.

        Args:
            message (Dict[str, Any]): The formatted Slack message payload.
                                    Should follow Slack's message format specifications.

        Returns:
            bool: True if message was sent successfully, False otherwise.

        Example:
            message = {
                "text": "Hello from the app!",
                "blocks": [...]
            }
        """
        try:
            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                method='POST',
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"Error sending message to Slack: {str(e)}")
            return False
