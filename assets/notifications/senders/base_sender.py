from abc import ABC, abstractmethod
from typing import Dict, Any


class MessageSender(ABC):
    """Abstract base class for message senders.

    This class defines the interface for sending messages to different messaging platforms.
    All concrete message sender implementations should inherit from this class.
    """

    @abstractmethod
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send the formatted message to the target platform.

        Args:
            message (Dict[str, Any]): The formatted message to be sent. Structure depends
                                    on the target platform's API requirements.

        Returns:
            bool: True if message was sent successfully, False otherwise.
        """
        pass
