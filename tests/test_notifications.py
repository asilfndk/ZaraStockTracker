"""Tests for notifications module"""
from zara_tracker.services.notification_service import NotificationService, send_notification
import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add parent and src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestNotificationService:
    """Tests for NotificationService class"""

    def test_escape_special_characters(self):
        """Test escaping special characters for AppleScript"""
        assert NotificationService._escape(
            'Test "quoted" text') == 'Test \\"quoted\\" text'
        assert NotificationService._escape(
            'Test\\backslash') == 'Test\\\\backslash'

    @patch('zara_tracker.services.notification_service.subprocess.run')
    def test_send_success(self, mock_run):
        """Test successful notification send"""
        mock_run.return_value = Mock(returncode=0)

        service = NotificationService()
        result = service.send("Test Title", "Test Message")

        assert result is True
        mock_run.assert_called_once()

    @patch('zara_tracker.services.notification_service.subprocess.run')
    def test_send_with_subtitle(self, mock_run):
        """Test notification with subtitle"""
        mock_run.return_value = Mock(returncode=0)

        service = NotificationService()
        result = service.send("Title", "Message", subtitle="Subtitle")

        assert result is True
        # Verify subtitle was included in the call
        call_args = mock_run.call_args
        script = call_args[0][0][2]  # osascript -e <script>
        assert 'subtitle' in script

    @patch('zara_tracker.services.notification_service.subprocess.run')
    def test_notify_stock_available(self, mock_run):
        """Test stock available notification"""
        mock_run.return_value = Mock(returncode=0)

        service = NotificationService()
        result = service.notify_stock_available(
            "Test Product",
            "M",
            999.99
        )

        assert result is True

    @patch('zara_tracker.services.notification_service.subprocess.run')
    def test_notify_price_drop(self, mock_run):
        """Test price drop notification"""
        mock_run.return_value = Mock(returncode=0)

        service = NotificationService()
        result = service.notify_price_drop(
            "Test Product",
            1299.99,
            999.99
        )

        assert result is True


class TestSendNotification:
    """Tests for send_notification convenience function"""

    @patch('zara_tracker.services.notification_service.subprocess.run')
    @patch('zara_tracker.core.repository.SettingsRepository.get')
    def test_send_notification_success(self, mock_get_setting, mock_run):
        """Test send_notification success"""
        mock_get_setting.return_value = "false"
        mock_run.return_value = Mock(returncode=0)

        result = send_notification("Title", "Message")

        assert result is True

    @patch('zara_tracker.services.notification_service.subprocess.run')
    @patch('zara_tracker.core.repository.SettingsRepository.get')
    def test_send_notification_failure(self, mock_get_setting, mock_run):
        """Test send_notification handles errors gracefully"""
        mock_get_setting.return_value = "false"
        mock_run.side_effect = Exception("Test error")

        result = send_notification("Title", "Message")

        assert result is False
