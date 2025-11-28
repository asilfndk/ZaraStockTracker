"""Zara Website Stock Check Module"""
import requests
import re
import json
from typing import Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime


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


class ZaraScraper:
    """Class to fetch product and stock info from Zara website"""

    def __init__(self, country_code: str = "tr", language: str = "en"):
        self.country_code = country_code
        self.language = language
        self.base_url = f"https://www.zara.com/{country_code}/{language}"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": f"https://www.zara.com/{country_code}/{language}/",
        })

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

    def get_stock_status(self, url: str) -> Optional[ProductInfo]:
        """Check stock status from product URL"""
        try:
            product_id, color_id = self._extract_ids_from_url(url)

            if not color_id:
                color_id = self._get_color_id_from_page(url, product_id)

            if not color_id:
                print(f"Color ID not found: {url}")
                return None

            api_url = f"https://www.zara.com/{self.country_code}/{self.language}/products-details?productIds={color_id}"
            response = self.session.get(api_url, timeout=15)

            if response.status_code != 200:
                print(f"API error: {response.status_code}")
                return None

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                return None

            if not data:
                print("API returned empty response")
                return None

            return self._parse_product_data(data[0], url)

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

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
        except:
            return None

    def _parse_product_data(self, data: dict, url: str) -> Optional[ProductInfo]:
        """Parse API response"""
        try:
            product_id = str(data.get("id", ""))
            name = data.get("name", "Unknown Product")

            detail = data.get("detail", {})
            colors = detail.get("colors", [])

            if not colors:
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
            print(f"Parse error: {e}")
            return None
