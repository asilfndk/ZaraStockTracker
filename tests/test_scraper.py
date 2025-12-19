"""Tests for Zara scraper module"""
from exceptions import APIError, RateLimitError, InvalidURLError, ParseError
from zara_scraper import ZaraScraper, SizeStock, ProductInfo, RateLimiter
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRateLimiter:
    """Tests for RateLimiter class"""

    def test_acquire_within_limit(self):
        """Test acquiring requests within rate limit"""
        limiter = RateLimiter(max_requests=5, time_window=60)

        for _ in range(5):
            assert limiter.acquire() is True

        # 6th request should fail
        assert limiter.acquire() is False

    def test_wait_time_calculation(self):
        """Test wait time calculation"""
        limiter = RateLimiter(max_requests=2, time_window=60)

        # No wait when under limit
        assert limiter.wait_time() == 0

        # Acquire all slots
        limiter.acquire()
        limiter.acquire()

        # Should have wait time now
        wait = limiter.wait_time()
        assert wait > 0
        assert wait <= 60


class TestZaraScraperURLParsing:
    """Tests for URL parsing functionality"""

    def test_extract_ids_from_valid_url(self):
        """Test extracting IDs from a valid Zara URL"""
        scraper = ZaraScraper()
        url = "https://www.zara.com/tr/en/product-name-p12345678.html?v1=987654321"

        product_id, color_id = scraper._extract_ids_from_url(url)

        assert product_id == "12345678"
        assert color_id == "987654321"

    def test_extract_ids_missing_color(self):
        """Test extracting IDs when color ID is missing"""
        scraper = ZaraScraper()
        url = "https://www.zara.com/tr/en/product-name-p12345678.html"

        product_id, color_id = scraper._extract_ids_from_url(url)

        assert product_id == "12345678"
        assert color_id is None

    def test_extract_ids_invalid_url(self):
        """Test extracting IDs from invalid URL"""
        scraper = ZaraScraper()
        url = "https://www.example.com/product"

        product_id, color_id = scraper._extract_ids_from_url(url)

        assert product_id is None
        assert color_id is None


class TestZaraScraperParsing:
    """Tests for API response parsing"""

    def test_parse_product_data(self, sample_api_response):
        """Test parsing complete API response"""
        scraper = ZaraScraper()
        url = "https://www.zara.com/tr/en/test-p123.html?v1=123456789"

        result = scraper._parse_product_data(sample_api_response[0], url)

        assert result is not None
        assert result.name == "Test Product"
        assert result.color == "Black"
        assert len(result.sizes) == 3
        assert result.price == 999.99
        assert result.old_price == 1299.99

    def test_parse_size_availability(self, sample_api_response):
        """Test parsing size availability correctly"""
        scraper = ZaraScraper()
        url = "https://www.zara.com/tr/en/test-p123.html?v1=123456789"

        result = scraper._parse_product_data(sample_api_response[0], url)

        # Check each size
        sizes = {s.size: s for s in result.sizes}

        assert sizes['S'].in_stock is True
        assert sizes['S'].stock_status == 'in_stock'

        assert sizes['M'].in_stock is False
        assert sizes['M'].stock_status == 'out_of_stock'

        assert sizes['L'].in_stock is True  # low_on_stock counts as in_stock
        assert sizes['L'].stock_status == 'low_on_stock'

    def test_parse_empty_colors(self):
        """Test parsing response with no colors"""
        scraper = ZaraScraper()
        url = "https://www.zara.com/tr/en/test-p123.html?v1=123"

        data = {'id': '123', 'name': 'Test', 'detail': {'colors': []}}

        with pytest.raises(ParseError):
            scraper._parse_product_data(data, url)


class TestZaraScraperIntegration:
    """Integration tests for scraper (with mocked HTTP)"""

    @patch('zara_scraper.httpx.Client')
    def test_get_stock_status_success(self, mock_client_class, sample_api_response):
        """Test successful stock status retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        scraper = ZaraScraper()
        url = "https://www.zara.com/tr/en/test-p12345678.html?v1=123456789"

        result = scraper.get_stock_status(url)

        assert result is not None
        assert result.name == "Test Product"

    @patch('zara_scraper.httpx.Client')
    def test_get_stock_status_api_error(self, mock_client_class):
        """Test handling API error"""
        mock_response = Mock()
        mock_response.status_code = 500

        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        scraper = ZaraScraper()
        url = "https://www.zara.com/tr/en/test-p12345678.html?v1=123456789"

        # Clear cache to ensure fresh request
        scraper.clear_cache()

        result = scraper.get_stock_status(url)

        # Should return None on API error (sync version handles gracefully)
        assert result is None


class TestSizeStock:
    """Tests for SizeStock dataclass"""

    def test_size_stock_creation(self):
        """Test creating SizeStock instance"""
        stock = SizeStock(
            size="M",
            in_stock=True,
            stock_status="in_stock",
            price=999.99,
            old_price=1299.99,
            discount="-23%"
        )

        assert stock.size == "M"
        assert stock.in_stock is True
        assert stock.price == 999.99


class TestProductInfo:
    """Tests for ProductInfo dataclass"""

    def test_product_info_creation(self):
        """Test creating ProductInfo instance"""
        sizes = [
            SizeStock(size="S", in_stock=True, stock_status="in_stock"),
            SizeStock(size="M", in_stock=False, stock_status="out_of_stock")
        ]

        product = ProductInfo(
            product_id="12345",
            name="Test Product",
            price=999.99,
            old_price=1299.99,
            discount="-23%",
            color="Black",
            image_url="https://example.com/image.jpg",
            url="https://www.zara.com/tr/en/test-p12345.html?v1=123",
            sizes=sizes
        )

        assert product.name == "Test Product"
        assert len(product.sizes) == 2
