"""Notification service for macOS and Telegram."""

import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications."""

    @staticmethod
    def send_macos(
        title: str,
        message: str,
        subtitle: str = "",
        sound: bool = True
    ) -> bool:
        """
        Send macOS native notification.

        Args:
            title: Notification title
            message: Notification body
            subtitle: Optional subtitle
            sound: Whether to play sound

        Returns:
            True if successful
        """
        try:
            # Escape special characters for AppleScript
            title = title.replace('"', '\\"').replace("'", "\\'")
            message = message.replace('"', '\\"').replace("'", "\\'")
            subtitle = subtitle.replace('"', '\\"').replace("'", "\\'")

            script_parts = [
                f'display notification "{message}"',
                f'with title "{title}"'
            ]

            if subtitle:
                script_parts.append(f'subtitle "{subtitle}"')

            if sound:
                script_parts.append('sound name "Glass"')

            script = " ".join(script_parts)

            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=5
            )

            logger.debug(f"Sent notification: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    @staticmethod
    def send_telegram(
        bot_token: str,
        chat_id: str,
        message: str
    ) -> bool:
        """
        Send Telegram notification.

        Args:
            bot_token: Telegram bot token
            chat_id: Chat ID to send to
            message: Message text

        Returns:
            True if successful
        """
        import requests

        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            response = requests.post(
                url,
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                timeout=10
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    @staticmethod
    def notify_size_available(
        product_name: str,
        size: str,
        price: float,
        telegram_config: Optional[dict] = None
    ) -> None:
        """Send notifications for size becoming available."""
        title = "🎉 Size Available!"
        message = f"{product_name} - {size} is now in stock! (₺{price:.0f})"

        # macOS notification
        NotificationService.send_macos(title, message)

        # Telegram notification if configured
        if telegram_config and telegram_config.get("enabled"):
            NotificationService.send_telegram(
                telegram_config["bot_token"],
                telegram_config["chat_id"],
                f"<b>{title}</b>\n{message}"
            )


def send_notification(title: str, message: str, subtitle: str = "") -> bool:
    """Convenience function for sending macOS notification."""
    return NotificationService.send_macos(title, message, subtitle)
