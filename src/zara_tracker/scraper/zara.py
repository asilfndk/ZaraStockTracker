"""Zara website scraper using official API."""

import logging
import re
import time
from typing import List, Optional, Tuple

import requests

from ..config import config, REGIONS
from ..models.product import ProductInfo, SizeStock
from .cache import scrape_cache

logger = logging.getLogger(__name__)


class ZaraScraper:
    """Scraper for Zara product information using their API."""

    def __init__(
        self,
        country_code: str = "tr",
        language: str = "en",
        use_cache: bool = True
    ):
        self.country_code = country_code.lower()
        self.language = language.lower()
        self.use_cache = use_cache

        # Validate region
        if self.country_code not in REGIONS:
            raise ValueError(f"Unsupported country: {country_code}")

        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://www.zara.com/{self.country_code}/{self.language}/",
        })

    def get_product_info(self, url: str) -> Optional[ProductInfo]:
        """
        Fetch product information from URL.

        Args:
            url: Zara product URL

        Returns:
            ProductInfo if successful, None otherwise
        """
        try:
            # Extract IDs from URL
            product_id, color_id = self._extract_ids(url)

            if not color_id:
                color_id = self._get_color_id_from_page(url)

            if not color_id:
                logger.warning(f"Could not extract color ID from: {url}")
                return None

            # Check cache
            cache_key = f"zara:{self.country_code}:{color_id}"
            if self.use_cache:
                cached = scrape_cache.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for {color_id}")
                    return self._parse_response(cached, url)

            # Fetch from API
            data = self._fetch_api(color_id)
            if not data:
                return None

            # Cache response
            if self.use_cache:
                scrape_cache.set(cache_key, data, config.cache_ttl)

            return self._parse_response(data, url)

        except Exception as e:
            logger.error(f"Error fetching product: {e}")
            return None

    def _extract_ids(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract product ID and color ID from URL."""
        product_id = None
        color_id = None

        # Product ID pattern: -p12345678.html
        product_match = re.search(r'-p(\d+)\.html', url)
        if product_match:
            product_id = product_match.group(1)

        # Color ID pattern: v1=123456789
        color_match = re.search(r'v1=(\d+)', url)
        if color_match:
            color_id = color_match.group(1)

        return product_id, color_id

    def _get_color_id_from_page(self, url: str) -> Optional[str]:
        """Try to extract color ID from page HTML."""
        try:
            response = self.session.get(url, timeout=config.api_timeout)
            patterns = [
                r'"productId"\s*:\s*(\d+)',
                r'data-product-id="(\d+)"',
                r'/product/(\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.warning(f"Failed to get color ID from page: {e}")
        return None

    def _fetch_api(self, color_id: str) -> Optional[dict]:
        """Fetch product data from Zara API with retry."""
        api_url = f"https://www.zara.com/{self.country_code}/{self.language}/products-details?productIds={color_id}"

        for attempt in range(config.max_retries):
            try:
                response = self.session.get(
                    api_url, timeout=config.api_timeout)

                if response.status_code != 200:
                    logger.warning(f"API returned {response.status_code}")
                    continue

                data = response.json()
                if data and len(data) > 0:
                    return data[0]

            except requests.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
            except requests.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")

            if attempt < config.max_retries - 1:
                time.sleep(1.0 * (attempt + 1))

        return None

    def _parse_response(self, data: dict, url: str) -> Optional[ProductInfo]:
        """Parse API response into ProductInfo."""
        try:
            product_id = str(data.get("id", ""))
            name = data.get("name", "Unknown Product")

            detail = data.get("detail", {})
            colors = detail.get("colors", [])

            if not colors:
                logger.warning("No colors in response")
                return None

            color = colors[0]
            color_name = color.get("name", "")
            color_product_id = str(color.get("productId", ""))

            # Get image URL
            image_url = ""
            xmedia = color.get("xmedia", [])
            for media in xmedia:
                if media.get("kind") == "full":
                    image_url = media.get(
                        "extraInfo", {}).get("deliveryUrl", "")
                    break
            if not image_url and xmedia:
                image_url = xmedia[0].get(
                    "extraInfo", {}).get("deliveryUrl", "")

            # Parse sizes
            sizes: List[SizeStock] = []
            price = 0.0
            old_price = 0.0
            discount = ""

            for size_data in color.get("sizes", []):
                size_name = size_data.get("name", "")
                availability = size_data.get("availability", "out_of_stock")
                in_stock = availability in [
                    "in_stock", "low_on_stock", "back_soon"]

                size_price = size_data.get("price", 0) / 100
                size_old_price = size_data.get("oldPrice", 0) / 100
                size_discount = size_data.get("discountLabel", "")

                if size_price > 0:
                    price = size_price
                if size_old_price > 0:
                    old_price = size_old_price
                if size_discount:
                    discount = size_discount

                sizes.append(SizeStock(
                    size=size_name,
                    in_stock=in_stock,
                    stock_status=availability,
                    price=size_price,
                    old_price=size_old_price,
                    discount=size_discount
                ))

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

    @staticmethod
    def is_supported_url(url: str) -> bool:
        """Check if URL is a valid Zara URL."""
        return "zara.com" in url.lower()
