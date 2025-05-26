import logging
from typing import Optional, Dict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from lib.env_vars import SLACK_BOT_TOKEN

logger = logging.getLogger(__name__)

class SlackManager:
    """
    Manages posting messages to Slack channels by name.
    - Authenticates using SLACK_BOT_TOKEN from env_vars.
    - Caches channel name to ID lookups for efficiency.
    - Provides a simple API for posting formatted messages.
    """
    def __init__(self, client: Optional[WebClient] = None):
        if not SLACK_BOT_TOKEN:
            raise ValueError("SLACK_BOT_TOKEN is not set in environment variables.")
        self.client = client or WebClient(token=SLACK_BOT_TOKEN)
        self._channel_cache: Dict[str, str] = {}

    def get_channel_id(self, channel_name: str) -> str:
        """
        Find the Slack channel ID for a given channel name. Caches results.
        Raises ValueError if not found.
        """
        if channel_name in self._channel_cache:
            return self._channel_cache[channel_name]
        try:
            cursor = None
            while True:
                response = self.client.conversations_list(cursor=cursor, exclude_archived=True, limit=100)
                for channel in response["channels"]:
                    if channel["name"] == channel_name:
                        channel_id = channel["id"]
                        self._channel_cache[channel_name] = channel_id
                        return channel_id
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        except SlackApiError as e:
            logger.error(f"Slack API error during channel lookup: {e}")
            raise
        raise ValueError(f"Channel '{channel_name}' not found.")

    def send_message(self, channel_name: str, title: str, body: str) -> str:
        """
        Send a message to the given Slack channel (by name), with the title in bold and the body as plain text.
        Returns the message timestamp (ts) if successful.
        Raises exceptions on failure.
        """
        channel_id = self.get_channel_id(channel_name)
        message = f"*{title}*\n{body}"
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=message
            )
            logger.info(f"Message sent to #{channel_name} (id={channel_id}): {title}")
            return response["ts"]
        except SlackApiError as e:
            logger.error(f"Failed to send message to #{channel_name}: {e}")
            raise

if __name__ == "__main__":
    # Example usage for manual testing
    import os
    logging.basicConfig(level=logging.INFO)
    channel = os.environ.get("SLACK_TEST_CHANNEL", "general")
    title = "Test Notification"
    body = "This is a test message from SlackManager."
    manager = SlackManager()
    try:
        ts = manager.send_message(channel, title, body)
        print(f"Message sent successfully (ts={ts})")
    except Exception as e:
        print(f"Error: {e}") 