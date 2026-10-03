import logging

import requests

logger = logging.getLogger(__name__)


class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, message):
        if not self.webhook_url:
            logger.warning("Discord webhook URL is not configured")
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json={"content": message},
                timeout=10,
            )
            response.raise_for_status()

            logger.info("Discord notification sent")
            return True

        except requests.RequestException as e:
            logger.error("Failed to send Discord notification: %s", e)
            return False
