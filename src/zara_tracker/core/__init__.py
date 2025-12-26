"""Core module - Database models, repository, scraper, and cache"""
from .models import ZaraProduct, ZaraStockStatus, PriceHistory, UserSettings
from .repository import (
    init_db, get_session,
    ProductRepository, StockRepository, PriceHistoryRepository,
    SettingsRepository, BackupRepository,
    add_price_history, get_price_history, get_setting, set_setting,
    backup_database, restore_database, list_backups
)
from .scraper import (
    ZaraScraper, SizeStock, ProductInfo, SUPPORTED_REGIONS,
    get_scraper_for_url, is_supported_url, get_brand_from_url
)
from .cache import TTLCache, api_cache

__all__ = [
    # Models
    "ZaraProduct",
    "ZaraStockStatus",
    "PriceHistory",
    "UserSettings",
    # Repository classes
    "ProductRepository",
    "StockRepository",
    "PriceHistoryRepository",
    "SettingsRepository",
    "BackupRepository",
    # Database functions
    "init_db",
    "get_session",
    "add_price_history",
    "get_price_history",
    "get_setting",
    "set_setting",
    "backup_database",
    "restore_database",
    "list_backups",
    # Scraper
    "ZaraScraper",
    "SizeStock",
    "ProductInfo",
    "SUPPORTED_REGIONS",
    "get_scraper_for_url",
    "is_supported_url",
    "get_brand_from_url",
    # Cache
    "TTLCache",
    "api_cache",
]


def get_supported_brands():
    """Get list of supported brands."""
    return ["Zara"]
