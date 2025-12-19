"""Tests for notifications module"""
from exceptions import NotificationError
from notifications import MacOSNotifier, send_notification
import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMacOSNotifier:
    """Tests for MacOSNotifier class"""

    def test_escape_special_characters(self):
        """Test escaping special characters for AppleScript"""
        assert MacOSNotifier._escape(
            'Test "quoted" text') == 'Test \\"quoted\\" text'
        assert MacOSNotifier._escape('Test\\backslash') == 'Test\\\\backslash'

    @patch('notifications.sys.platform', 'linux')
    def test_send_non_darwin(self):
        """Test that send returns False on non-macOS"""
        result = MacOSNotifier.send("Test", "Message")
        assert result is False

    @patch('notifications.sys.platform', 'darwin')
    @patch('notifications.subprocess.run')
    def test_send_success(self, mock_run):
        """Test successful notification send"""
        mock_run.return_value = Mock(returncode=0, stderr="")

        result = MacOSNotifier.send("Test Title", "Test Message")

        assert result is True
        mock_run.assert_called_once()

    @patch('notifications.sys.platform', 'darwin')
    @patch('notifications.subprocess.run')
    def test_send_with_subtitle(self, mock_run):
        """Test notification with subtitle"""
        mock_run.return_value = Mock(returncode=0, stderr="")

        result = MacOSNotifier.send("Title", "Message", subtitle="Subtitle")

        assert result is True
        # Verify subtitle was included in the call
        call_args = mock_run.call_args
        script = call_args[0][0][2]  # osascript -e <script>
        assert 'subtitle' in script

    @patch('notifications.sys.platform', 'darwin')
    @patch('notifications.subprocess.run')
    def test_send_failure(self, mock_run):
        """Test notification send failure"""
        mock_run.return_value = Mock(returncode=1, stderr="Error message")

        with pytest.raises(NotificationError):
            MacOSNotifier.send("Title", "Message")

    @patch('notifications.sys.platform', 'darwin')
    @patch('notifications.subprocess.run')
    def test_notify_stock_available(self, mock_run):
        """Test stock available notification"""
        mock_run.return_value = Mock(returncode=0, stderr="")

        result = MacOSNotifier.notify_stock_available(
            "Test Product",
            "M",
            999.99
        )

        assert result is True

    @patch('notifications.sys.platform', 'darwin')
    @patch('notifications.subprocess.run')
    def test_notify_price_drop(self, mock_run):
        """Test price drop notification"""
        mock_run.return_value = Mock(returncode=0, stderr="")

        result = MacOSNotifier.notify_price_drop(
            "Test Product",
            1299.99,
            999.99
        )

        assert result is True


class TestSendNotification:
    """Tests for send_notification convenience function"""

    @patch('notifications.MacOSNotifier.send')
    def test_send_notification_success(self, mock_send):
        """Test send_notification success"""
        mock_send.return_value = True

        result = send_notification("Title", "Message")

        assert result is True
        mock_send.assert_called_once_with("Title", "Message", None)

    @patch('notifications.MacOSNotifier.send')
    def test_send_notification_failure(self, mock_send):
        """Test send_notification handles errors gracefully"""
        mock_send.side_effect = NotificationError("Test error")

        result = send_notification("Title", "Message")

        assert result is False
