"""
Zara Scraper Module

Central module for Zara stock tracking.
Supports only Zara (API-based, fast).
"""
from zara_scraper import SUPPORTED_REGIONS
from zara_scraper import ZaraScraper, SizeStock, ProductInfo
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Scraper mapping - only Zara
SCRAPER_MAP = {
    "zara.com": ZaraScraper,
}


def get_scraper_for_url(url: str, country_code: str = "tr", language: str = "en", use_cache: bool = True):
    """Get appropriate scraper for URL"""
    url_lower = url.lower()
    for domain, scraper_class in SCRAPER_MAP.items():
        if domain in url_lower:
            return scraper_class(country_code=country_code, language=language, use_cache=use_cache)

    supported = ", ".join(SCRAPER_MAP.keys())
    raise ValueError(f"Unsupported URL: {url}. Supported domains: {supported}")


def is_supported_url(url: str) -> bool:
    """Check if URL is supported"""
    return any(domain in url.lower() for domain in SCRAPER_MAP.keys())


def get_brand_from_url(url: str) -> Optional[str]:
    """Get brand name from URL"""
    url_lower = url.lower()
    if "zara.com" in url_lower:
        return "Zara"
    return None


def get_supported_brands() -> List[str]:
    """Get list of supported brand names"""
    return ["Zara"]


def get_supported_domains() -> List[str]:
    """Get list of supported domains"""
    return list(SCRAPER_MAP.keys())
