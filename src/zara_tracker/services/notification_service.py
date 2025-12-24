"""
Notification Service - Handles all notification channels.
"""
import logging
import subprocess
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class NotificationService:
    """Unified notification service for macOS and Telegram."""

    APP_NAME = "Zara Stock Tracker"
    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(
        self,
        telegram_enabled: bool = False,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ):
        """
        Initialize NotificationService.

        Args:
            telegram_enabled: Whether Telegram notifications are enabled
            telegram_bot_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
        """
        self._telegram_enabled = telegram_enabled
        self._telegram_token = telegram_bot_token
        self._telegram_chat_id = telegram_chat_id

    @property
    def telegram_enabled(self) -> bool:
        """Check if Telegram is properly configured."""
        return (
            self._telegram_enabled and
            bool(self._telegram_token) and
            bool(self._telegram_chat_id)
        )

    def send(
        self,
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        use_telegram: bool = True
    ) -> bool:
        """
        Send notification via all enabled channels.

        Args:
            title: Notification title
            message: Notification body
            subtitle: Optional subtitle (macOS only)
            use_telegram: Whether to also send via Telegram

        Returns:
            True if sent via at least one channel
        """
        macos_sent = self._send_macos(title, message, subtitle)
        telegram_sent = False

        if use_telegram and self.telegram_enabled:
            telegram_sent = self._send_telegram(f"*{title}*\n{message}")

        return macos_sent or telegram_sent

    def notify_stock_available(
        self,
        product_name: str,
        size: str,
        price: float,
        url: Optional[str] = None
    ) -> bool:
        """Send notification when desired size becomes available."""
        title = "🎉 Size Available!"
        message = f"{product_name} - {size} is now IN STOCK!"
        subtitle = f"₺{price:.0f}"

        macos_sent = self._send_macos(title, message, subtitle)
        telegram_sent = False

        if self.telegram_enabled:
            telegram_msg = (
                f"🎉 <b>Size Available!</b>\n\n"
                f"<b>{product_name}</b>\n"
                f"Size: {size}\n"
                f"Price: ₺{price:.0f}"
            )
            if url:
                telegram_msg += f"\n\n<a href=\"{url}\">View Product</a>"
            telegram_sent = self._send_telegram(telegram_msg)

        return macos_sent or telegram_sent

    def notify_price_drop(
        self,
        product_name: str,
        old_price: float,
        new_price: float,
        url: Optional[str] = None
    ) -> bool:
        """Send notification when price drops."""
        savings = old_price - new_price
        title = "💰 Price Drop!"
        message = f"{product_name}: ₺{old_price:.0f} → ₺{new_price:.0f}"
        subtitle = f"Save ₺{savings:.0f}"

        macos_sent = self._send_macos(title, message, subtitle)
        telegram_sent = False

        if self.telegram_enabled:
            telegram_msg = (
                f"💰 <b>Price Drop!</b>\n\n"
                f"<b>{product_name}</b>\n"
                f"Was: ₺{old_price:.0f}\n"
                f"Now: ₺{new_price:.0f}\n"
                f"Save: ₺{savings:.0f}"
            )
            if url:
                telegram_msg += f"\n\n<a href=\"{url}\">View Product</a>"
            telegram_sent = self._send_telegram(telegram_msg)

        return macos_sent or telegram_sent

    def _send_macos(
        self,
        title: str,
        message: str,
        subtitle: Optional[str] = None
    ) -> bool:
        """Send macOS native notification."""
        try:
            title_escaped = self._escape(title)
            message_escaped = self._escape(message)

            script = f'display notification "{message_escaped}" with title "{title_escaped}"'
            if subtitle:
                script += f' subtitle "{self._escape(subtitle)}"'
            script += " sound name \"Glass\""

            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                timeout=5
            )
            return True
        except Exception as e:
            logger.error(f"macOS notification failed: {e}")
            return False

    def _send_telegram(self, message: str) -> bool:
        """Send Telegram message."""
        if not self.telegram_enabled:
            return False

        try:
            url = self.TELEGRAM_API_URL.format(token=self._telegram_token)
            response = requests.post(
                url,
                json={
                    "chat_id": self._telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False

    @staticmethod
    def _escape(text: str) -> str:
        """Escape special characters for AppleScript."""
        return text.replace("\\", "\\\\").replace('"', '\\"')


# Convenience function for backward compatibility
def send_notification(
    title: str,
    message: str,
    subtitle: Optional[str] = None,
    use_telegram: bool = True
) -> bool:
    """Send notification using default service."""
    from ..core.repository import SettingsRepository

    service = NotificationService(
        telegram_enabled=SettingsRepository.get(
            "telegram_enabled", "false") == "true",
        telegram_bot_token=SettingsRepository.get("telegram_bot_token"),
        telegram_chat_id=SettingsRepository.get("telegram_chat_id")
    )
    return service.send(title, message, subtitle, use_telegram)
