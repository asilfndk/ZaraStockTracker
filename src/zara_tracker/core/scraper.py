"""Zara Website Stock Check Module with caching, logging, and retry support"""
import requests
import re
import json
import logging
import time
from typing import Optional, List, Tuple
from dataclasses import dataclass
from functools import wraps

from .cache import api_cache

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SizeStock:
    """Size stock status"""
    size: str
    in_stock: bool
    stock_status: str  # "in_stock", "out_of_stock", "low_on_stock", "coming_soon"
    price: float = 0.0
    old_price: float = 0.0
    discount: str = ""


@dataclass
class ProductInfo:
    """Product information data class"""
    product_id: str
    name: str
    price: float
    old_price: float
    discount: str
    color: str
    image_url: str
    url: str
    sizes: List[SizeStock]


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, requests.Timeout) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
            raise last_exception
        return wrapper
    return decorator


# Supported countries and languages
SUPPORTED_REGIONS = {
    "tr": {"languages": ["en", "tr"], "name": "Turkey"},
    "us": {"languages": ["en"], "name": "United States"},
    "uk": {"languages": ["en"], "name": "United Kingdom"},
    "de": {"languages": ["de", "en"], "name": "Germany"},
    "fr": {"languages": ["fr", "en"], "name": "France"},
    "es": {"languages": ["es", "en"], "name": "Spain"},
    "it": {"languages": ["it", "en"], "name": "Italy"},
}


class ZaraScraper:
    """Class to fetch product and stock info from Zara website"""

    def __init__(
        self,
        country_code: str = "tr",
        language: str = "en",
        use_cache: bool = True,
        cache_ttl: int = 300
    ):
        """
        Initialize ZaraScraper.

        Args:
            country_code: Country code (tr, us, uk, de, fr, es, it)
            language: Language code (en, tr, de, fr, es, it)
            use_cache: Whether to cache API responses
            cache_ttl: Cache time-to-live in seconds (default: 5 min)
        """
        self.country_code = country_code.lower()
        self.language = language.lower()
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.base_url = f"https://www.zara.com/{self.country_code}/{self.language}"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": f"https://www.zara.com/{self.country_code}/{self.language}/",
        })

        logger.info(
            f"ZaraScraper initialized for {self.country_code}/{self.language}")

    def _extract_ids_from_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract product ID and color ID from URL"""
        product_id = None
        color_id = None

        product_match = re.search(r'-p(\d+)\.html', url)
        if product_match:
            product_id = product_match.group(1)

        color_match = re.search(r'v1=(\d+)', url)
        if color_match:
            color_id = color_match.group(1)

        return product_id, color_id

    def _get_cache_key(self, color_id: str) -> str:
        """Generate cache key for product"""
        return f"zara:{self.country_code}:{self.language}:{color_id}"

    def get_stock_status(self, url: str) -> Optional[ProductInfo]:
        """
        Check stock status from product URL.

        Args:
            url: Zara product URL

        Returns:
            ProductInfo if successful, None otherwise
        """
        try:
            product_id, color_id = self._extract_ids_from_url(url)

            if not color_id:
                color_id = self._get_color_id_from_page(url, product_id)

            if not color_id:
                logger.warning(f"Color ID not found: {url}")
                return None

            # Check cache first
            if self.use_cache:
                cache_key = self._get_cache_key(color_id)
                cached = api_cache.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for {color_id}")
                    return self._parse_product_data(cached, url)

            # Fetch from API with retry
            data = self._fetch_product_data(color_id)
            if not data:
                return None

            # Cache the response
            if self.use_cache:
                api_cache.set(cache_key, data, self.cache_ttl)
                logger.debug(f"Cached response for {color_id}")

            return self._parse_product_data(data, url)

        except Exception as e:
            logger.error(f"Error fetching stock status: {e}")
            return None

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _fetch_product_data(self, color_id: str) -> Optional[dict]:
        """Fetch product data from Zara API with retry"""
        api_url = f"https://www.zara.com/{self.country_code}/{self.language}/products-details?productIds={color_id}"

        logger.debug(f"Fetching: {api_url}")
        response = self.session.get(api_url, timeout=15)

        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}")
            return None

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None

        if not data:
            logger.warning("API returned empty response")
            return None

        return data[0]

    def _get_color_id_from_page(self, url: str, product_id: str) -> Optional[str]:
        """Try to find color_id from page HTML"""
        try:
            response = self.session.get(url, timeout=15)
            patterns = [
                rf'"productId"\s*:\s*(\d+)',
                rf'data-product-id="(\d+)"',
                rf'/product/(\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
            return None
        except Exception as e:
            logger.warning(f"Failed to get color_id from page: {e}")
            return None

    def _parse_product_data(self, data: dict, url: str) -> Optional[ProductInfo]:
        """Parse API response"""
        try:
            product_id = str(data.get("id", ""))
            name = data.get("name", "Unknown Product")

            detail = data.get("detail", {})
            colors = detail.get("colors", [])

            if not colors:
                logger.warning("No colors found in product data")
                return None

            color = colors[0]
            color_name = color.get("name", "")
            color_product_id = str(color.get("productId", ""))

            # Image URL
            image_url = ""
            xmedia = color.get("xmedia", [])
            if xmedia:
                for media in xmedia:
                    if media.get("kind") == "full":
                        extra = media.get("extraInfo", {})
                        image_url = extra.get("deliveryUrl", "")
                        break
                if not image_url and xmedia:
                    extra = xmedia[0].get("extraInfo", {})
                    image_url = extra.get("deliveryUrl", "")

            # Size and stock info
            sizes = []
            size_data = color.get("sizes", [])

            price = 0.0
            old_price = 0.0
            discount = ""

            for size in size_data:
                size_name = size.get("name", "")
                availability = size.get("availability", "out_of_stock")
                stock_available = availability in [
                    "in_stock", "low_on_stock", "back_soon"]

                size_price = size.get("price", 0) / 100
                size_old_price = size.get("oldPrice", 0) / 100
                size_discount = size.get("discountLabel", "")

                if size_price > 0:
                    price = size_price
                if size_old_price > 0:
                    old_price = size_old_price
                if size_discount:
                    discount = size_discount

                sizes.append(SizeStock(
                    size=size_name,
                    in_stock=stock_available,
                    stock_status=availability,
                    price=size_price,
                    old_price=size_old_price,
                    discount=size_discount
                ))

            logger.info(f"Parsed product: {name} ({len(sizes)} sizes)")

            return ProductInfo(
                product_id=color_product_id or product_id,
                name=name,
                price=price,
                old_price=old_price,
                discount=discount,
                color=color_name,
                image_url=image_url,
                url=url,
                sizes=sizes
            )

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None

    @classmethod
    def get_supported_regions(cls) -> dict:
        """Get list of supported regions"""
        return SUPPORTED_REGIONS


def get_scraper_for_url(url: str, country_code: str = "tr", language: str = "en", use_cache: bool = True) -> ZaraScraper:
    """Get appropriate scraper for URL (only Zara is supported)"""
    if "zara.com" in url.lower():
        return ZaraScraper(country_code=country_code, language=language, use_cache=use_cache)
    raise ValueError(f"Unsupported URL: {url}. Only Zara URLs are supported.")


def is_supported_url(url: str) -> bool:
    """Check if URL is supported (only Zara)"""
    return "zara.com" in url.lower()


def get_brand_from_url(url: str) -> Optional[str]:
    """Get brand name from URL"""
    if "zara.com" in url.lower():
        return "Zara"
    return None
