import os
import json
from typing import Dict, Any
from notifications.events import EventParser
from notifications.formatters import SlackFormatter, TeamsFormatter
from notifications.senders import SlackSender, TeamsSender
import logging

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))


def get_notification_config():
    """
    Get and validate notification configuration from environment variables.

    This function retrieves the notification platform and corresponding
    webhook URLs from environment variables. It validates that the platform
    is supported (either 'slack' or 'teams') and that the required webhook URL
    for the selected platform is present.

    Environment Variables:
        NOTIFICATION_PLATFORM: The platform to use ('slack' or 'teams)
        SLACK_WEBHOOK_URL: Required webhook URL if platform is 'slack'
        SLACK_WEBHOOK_ARN: Optional ARN for the Slack webhook secret
        TEAMS_WEBHOOK_URL: Required webhook URL if platform is 'teams'
        TEAMS_WEBHOOK_ARN: Optional ARN for the Teams webhook secret

    Returns:
        dict: Configuration dictionary containing:
            - platform: str - The selected notification platform
            - webhook_url: str - The webhook URL
            - webhook_arn: str - The webhook ARN

    Raises:
        ValueError: If the platform is unsupported or if the required webhook
        URL is missing
    """
    platform = os.environ.get("NOTIFICATION_PLATFORM", "slack").lower()
    logger.debug("Notification platform: %s", platform)

    if platform not in ["slack", "teams"]:
        raise ValueError(f"Unsupported notification platform: {platform}")

    # Validate webhook URL based on platform
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    webhook_arn = os.environ.get("WEBHOOK_ARN", "")
    
    if not webhook_url and not webhook_arn:
        raise ValueError("Missing WEBHOOK_URL or WEBHOOK_ARN environment variable")
    
    return {
        "platform": platform,
        "webhook_url": webhook_url,
        "webhook_arn": webhook_arn,
    }


def lambda_handler(event: Dict[Any, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler to process various AWS events and send notifications
    """
    logger.debug("Received event: %s", json.dumps(event))

    try:
        # Get notification configuration
        config = get_notification_config()
        logger.debug("Using platform: %s", config["platform"])

        # Validate platform
        if config["platform"] not in ["slack", "teams"]:
            raise ValueError(f'Invalid platform: {config["platform"]}')
        
        webhook_url = config["webhook_url"]
        
        # If the webhook ARN is present, we need to retrieve the secret from the ARN
        if config["webhook_arn"] != "":
            logger.info("Retrieving webhook URL from secret: %s", config["webhook_arn"])
            
            client = boto3.client('secretsmanager')
            secret = get_secret(client, config["webhook_arn"])
            
            # Check if the secret is empty or the webhook URL is not present
            if secret is None or secret["webhook_url"] == "":
                raise ValueError(f"Secret {config['webhook_arn']} is empty")
            
            webhook_url = secret["webhook_url"]
        
        # Parse and normalize the event
        parser = EventParser()
        normalized_event = parser.parse_event(event)
        # Convert normalized_event to dict before logging
        logger.debug("Normalized event: %s", json.dumps(normalized_event.to_dict()))

        # Create appropriate formatter and sender based on platform
        if config["platform"] == "slack":
            formatter = SlackFormatter()
            sender = SlackSender(webhook_url)
        else:  # teams
            formatter = TeamsFormatter()
            sender = TeamsSender(webhook_url)

        # Format the message
        message = formatter.format(normalized_event)
        logger.debug("Formatted message: %s", json.dumps(message))

        # Send the message
        logger.debug("Attempting to send message")
        success = sender.send_message(message)
        logger.info("Message sent successfully: %s", success)

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
        logger.error("Error processing event: %s", str(e), exc_info=True)
        raise
