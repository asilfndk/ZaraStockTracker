"""
Notification module for Zara Stock Tracker
Supports macOS native notifications and Telegram
"""
import subprocess
import sys
import logging
import requests
from typing import Optional

from exceptions import NotificationError

logger = logging.getLogger(__name__)


class MacOSNotifier:
    """Send native macOS notifications using osascript"""

    APP_NAME = "Zara Stock Tracker"

    @classmethod
    def send(
        cls,
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: bool = True
    ) -> bool:
        """
        Send a macOS native notification.

        Args:
            title: Notification title
            message: Notification body text
            subtitle: Optional subtitle
            sound: Whether to play notification sound

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails to send
        """
        if sys.platform != "darwin":
            logger.debug("Not on macOS, skipping native notification")
            return False

        try:
            # Build AppleScript command
            script_parts = [f'display notification "{cls._escape(message)}"']
            script_parts.append(f'with title "{cls._escape(title)}"')

            if subtitle:
                script_parts.append(f'subtitle "{cls._escape(subtitle)}"')

            if sound:
                script_parts.append('sound name "Glass"')

            script = " ".join(script_parts)

            # Execute AppleScript
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                raise NotificationError(f"osascript failed: {result.stderr}")

            logger.debug(f"macOS notification sent: {title}")
            return True

        except subprocess.TimeoutExpired:
            raise NotificationError("Notification timed out")
        except Exception as e:
            raise NotificationError(f"Failed to send notification: {e}")

    @staticmethod
    def _escape(text: str) -> str:
        """Escape special characters for AppleScript"""
        return text.replace('\\', '\\\\').replace('"', '\\"')

    @classmethod
    def notify_stock_available(
        cls,
        product_name: str,
        size: str,
        price: float
    ) -> bool:
        """
        Send notification when desired size becomes available.

        Args:
            product_name: Name of the product
            size: Size that became available
            price: Current price

        Returns:
            True if notification was sent
        """
        return cls.send(
            title="🎉 Size Available!",
            message=f"{product_name}",
            subtitle=f"Size {size} is now in stock • ₺{price:.0f}"
        )

    @classmethod
    def notify_price_drop(
        cls,
        product_name: str,
        old_price: float,
        new_price: float
    ) -> bool:
        """
        Send notification when price drops.

        Args:
            product_name: Name of the product
            old_price: Previous price
            new_price: New lower price

        Returns:
            True if notification was sent
        """
        discount_pct = ((old_price - new_price) / old_price) * 100
        return cls.send(
            title="💰 Price Drop!",
            message=f"{product_name}",
            subtitle=f"₺{old_price:.0f} → ₺{new_price:.0f} ({discount_pct:.0f}% off)"
        )


class TelegramNotifier:
    """Send notifications via Telegram bot"""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._enabled = bool(bot_token and chat_id)

        if self._enabled:
            logger.info("Telegram notifications enabled")
        else:
            logger.debug("Telegram notifications disabled (no credentials)")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def send(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a Telegram message.

        Args:
            message: Message text
            parse_mode: Parse mode (HTML, Markdown, or empty)

        Returns:
            True if sent successfully
        """
        if not self._enabled:
            return False

        try:
            url = self.API_URL.format(token=self.bot_token)
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.debug("Telegram notification sent")
                return True
            else:
                logger.warning(f"Telegram API error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False

    def notify_stock_available(
        self,
        product_name: str,
        size: str,
        price: float,
        url: Optional[str] = None
    ) -> bool:
        """Send stock available notification via Telegram"""
        message = f"🎉 <b>Size Available!</b>\n\n"
        message += f"<b>{product_name}</b>\n"
        message += f"Size: {size}\n"
        message += f"Price: ₺{price:.0f}\n"
        if url:
            message += f"\n<a href='{url}'>View Product</a>"

        return self.send(message)

    def notify_price_drop(
        self,
        product_name: str,
        old_price: float,
        new_price: float,
        url: Optional[str] = None
    ) -> bool:
        """Send price drop notification via Telegram"""
        discount_pct = ((old_price - new_price) / old_price) * 100

        message = f"💰 <b>Price Drop!</b>\n\n"
        message += f"<b>{product_name}</b>\n"
        message += f"Price: <s>₺{old_price:.0f}</s> → ₺{new_price:.0f}\n"
        message += f"Discount: {discount_pct:.0f}% off\n"
        if url:
            message += f"\n<a href='{url}'>View Product</a>"

        return self.send(message)


# Initialize global Telegram notifier from config
_telegram_notifier: Optional[TelegramNotifier] = None


def get_telegram_notifier() -> Optional[TelegramNotifier]:
    """Get global Telegram notifier instance"""
    global _telegram_notifier
    if _telegram_notifier is None:
        try:
            from config import config
            if config.telegram_enabled:
                _telegram_notifier = TelegramNotifier(
                    bot_token=config.telegram_bot_token or "",
                    chat_id=config.telegram_chat_id or ""
                )
        except ImportError:
            pass
    return _telegram_notifier


def send_notification(
    title: str,
    message: str,
    subtitle: Optional[str] = None,
    use_telegram: bool = True
) -> bool:
    """
    Convenience function to send a notification.

    Args:
        title: Notification title
        message: Notification body
        subtitle: Optional subtitle
        use_telegram: Also send via Telegram if configured

    Returns:
        True if sent successfully via any channel
    """
    success = False

    # Try macOS notification
    try:
        if MacOSNotifier.send(title, message, subtitle):
            success = True
    except NotificationError as e:
        logger.warning(f"macOS notification failed: {e}")

    # Try Telegram
    if use_telegram:
        telegram = get_telegram_notifier()
        if telegram and telegram.enabled:
            full_message = f"<b>{title}</b>\n{message}"
            if subtitle:
                full_message += f"\n<i>{subtitle}</i>"
            if telegram.send(full_message):
                success = True

    return success
