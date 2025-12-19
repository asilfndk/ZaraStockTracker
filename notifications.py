"""macOS Native Push Notifications for Zara Stock Tracker"""
import subprocess
import sys
from typing import Optional
from exceptions import NotificationError


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


def send_notification(title: str, message: str, subtitle: Optional[str] = None) -> bool:
    """
    Convenience function to send a notification.

    Args:
        title: Notification title
        message: Notification body
        subtitle: Optional subtitle

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        return MacOSNotifier.send(title, message, subtitle)
    except NotificationError:
        return False
