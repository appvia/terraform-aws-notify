import requests
from typing import Dict, Any
from .base_sender import MessageSender


class TeamsSender(MessageSender):
    """Handles sending messages to Microsoft Teams.

    A concrete implementation of MessageSender that sends messages to Microsoft Teams
    using webhook URLs.
    """

    def __init__(self, webhook_url: str):
        """Initialize the Microsoft Teams message sender.

        Args:
            webhook_url (str): The Microsoft Teams webhook URL to send messages to.
        """
        self.webhook_url = webhook_url

    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send a formatted message to Microsoft Teams.

        Args:
            message (Dict[str, Any]): The formatted Teams message payload.
                                    Should follow Microsoft Teams' message format specifications.

        Returns:
            bool: True if message was sent successfully, False otherwise.

        Example:
            message = {
                "text": "Hello from the app!",
                "sections": [...]
            }
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending message to Teams: {str(e)}")
            return False
