"""Custom exceptions for Zara Stock Tracker"""


class ZaraTrackerError(Exception):
    """Base exception for Zara Stock Tracker"""
    pass


class ScraperError(ZaraTrackerError):
    """Base exception for scraper-related errors"""
    pass


class APIError(ScraperError):
    """Error when API request fails"""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"{message} (status: {status_code})" if status_code else message)


class RateLimitError(ScraperError):
    """Error when rate limit is exceeded"""
    pass


class ParseError(ScraperError):
    """Error when parsing API response fails"""
    pass


class ProductNotFoundError(ScraperError):
    """Error when product is not found"""
    pass


class InvalidURLError(ScraperError):
    """Error when URL is invalid or missing required parameters"""
    pass


class DatabaseError(ZaraTrackerError):
    """Error related to database operations"""
    pass


class CacheError(ZaraTrackerError):
    """Error related to cache operations"""
    pass


class NotificationError(ZaraTrackerError):
    """Error when sending notification fails"""
    pass
