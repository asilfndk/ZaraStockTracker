"""Tests for custom exceptions"""
from zara_tracker.exceptions import (
    ZaraTrackerError,
    ScraperError,
    APIError,
    RateLimitError,
    ParseError,
    ProductNotFoundError,
    InvalidURLError,
    DatabaseError,
    CacheError,
    NotificationError
)
import pytest
import sys
import os

# Add parent and src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy"""

    def test_base_exception(self):
        """Test ZaraTrackerError is base for all custom exceptions"""
        assert issubclass(ScraperError, ZaraTrackerError)
        assert issubclass(DatabaseError, ZaraTrackerError)
        assert issubclass(CacheError, ZaraTrackerError)
        assert issubclass(NotificationError, ZaraTrackerError)

    def test_scraper_exception_hierarchy(self):
        """Test ScraperError subclasses"""
        assert issubclass(APIError, ScraperError)
        assert issubclass(RateLimitError, ScraperError)
        assert issubclass(ParseError, ScraperError)
        assert issubclass(ProductNotFoundError, ScraperError)
        assert issubclass(InvalidURLError, ScraperError)


class TestAPIError:
    """Tests for APIError exception"""

    def test_api_error_with_status(self):
        """Test APIError with status code"""
        error = APIError("Request failed", status_code=404)

        assert error.status_code == 404
        assert "404" in str(error)
        assert "Request failed" in str(error)

    def test_api_error_without_status(self):
        """Test APIError without status code"""
        error = APIError("Request failed")

        assert error.status_code is None
        assert "Request failed" in str(error)


class TestExceptionMessages:
    """Tests for exception message handling"""

    def test_rate_limit_error(self):
        """Test RateLimitError message"""
        error = RateLimitError("Too many requests")
        assert str(error) == "Too many requests"

    def test_parse_error(self):
        """Test ParseError message"""
        error = ParseError("Invalid JSON")
        assert str(error) == "Invalid JSON"

    def test_product_not_found_error(self):
        """Test ProductNotFoundError message"""
        error = ProductNotFoundError("Product 12345 not found")
        assert str(error) == "Product 12345 not found"

    def test_invalid_url_error(self):
        """Test InvalidURLError message"""
        error = InvalidURLError("Missing v1 parameter")
        assert str(error) == "Missing v1 parameter"


class TestExceptionRaising:
    """Tests for raising and catching exceptions"""

    def test_catch_specific_exception(self):
        """Test catching specific exception type"""
        with pytest.raises(APIError):
            raise APIError("Test error", status_code=500)

    def test_catch_parent_exception(self):
        """Test catching parent exception type"""
        with pytest.raises(ScraperError):
            raise APIError("Test error")

        with pytest.raises(ZaraTrackerError):
            raise APIError("Test error")

    def test_exception_in_try_except(self):
        """Test exception handling in try-except block"""
        try:
            raise RateLimitError("Limit exceeded")
        except ScraperError as e:
            assert "Limit exceeded" in str(e)
