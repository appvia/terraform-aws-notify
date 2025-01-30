import os
import json
from typing import Dict, Any
from events import EventParser
from formatters import SlackFormatter, TeamsFormatter
from senders import SlackSender, TeamsSender


def get_notification_config():
    """
    Get and validate notification configuration from environment variables.

    This function retrieves the notification platform and corresponding webhook URLs
    from environment variables. It validates that the platform is supported
    (either 'slack' or 'teams') and that the required webhook URL for the
    selected platform is present.

    Environment Variables:
        NOTIFICATION_PLATFORM: The platform to use ('slack' or 'teams'). Defaults to 'slack'
        SLACK_WEBHOOK_URL: Required webhook URL if platform is 'slack'
        TEAMS_WEBHOOK_URL: Required webhook URL if platform is 'teams'

    Returns:
        dict: Configuration dictionary containing:
            - platform: str - The selected notification platform
            - slack_webhook_url: str - The Slack webhook URL
            - teams_webhook_url: str - The Teams webhook URL

    Raises:
        ValueError: If the platform is unsupported or if the required webhook URL is missing
    """
    platform = os.environ.get("NOTIFICATION_PLATFORM", "slack").lower()
    if platform not in ["slack", "teams"]:
        raise ValueError(f"Unsupported notification platform: {platform}")

    # Validate webhook URL based on platform
    if platform == "slack":
        slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
        if not slack_webhook_url:
            raise ValueError("Missing SLACK_WEBHOOK_URL environment variable")
        teams_webhook_url = os.environ.get("TEAMS_WEBHOOK_URL", "")
    else:  # platform == "teams"
        teams_webhook_url = os.environ.get("TEAMS_WEBHOOK_URL", "")
        if not teams_webhook_url:
            raise ValueError("Missing TEAMS_WEBHOOK_URL environment variable")
        slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")

    config = {
        "platform": platform,
        "slack_webhook_url": slack_webhook_url,
        "teams_webhook_url": teams_webhook_url,
    }

    return config


def lambda_handler(event: Dict[Any, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler to process various AWS events and send notifications
    """
    try:
        # Get notification configuration
        config = get_notification_config()

        # Validate platform
        if config["platform"] not in ["slack", "teams"]:
            raise ValueError(f"Invalid platform: {config['platform']}")

        # Parse and normalize the event
        parser = EventParser()
        normalized_event = parser.parse_event(event)

        # Create appropriate formatter and sender based on platform
        if config["platform"] == "slack":
            formatter = SlackFormatter()
            sender = SlackSender(config["slack_webhook_url"])
        else:  # teams
            formatter = TeamsFormatter()
            sender = TeamsSender(config["teams_webhook_url"])

        # Format the message
        message = formatter.format_message(normalized_event)

        # Send the message
        success = sender.send_message(message)

        return {
            "statusCode": 200 if success else 500,
            "body": json.dumps(
                {
                    "message": (
                        "Notification sent successfully"
                        if success
                        else "Failed to send notification"
                    )
                }
            ),
        }

    except Exception as e:
        print(f"Error processing event: {str(e)}")
        raise
