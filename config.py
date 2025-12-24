"""
Configuration management for Zara Stock Tracker

Supports loading from environment variables and .env file
"""
import os
import logging
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Config:
    """Application configuration"""

    # Database
    db_dir: str = field(default_factory=lambda: os.path.join(
        os.path.expanduser("~"), ".zara_stock_tracker"
    ))

    # Scraper settings
    country_code: str = "tr"
    language: str = "en"
    request_timeout: int = 15
    max_retries: int = 3
    retry_base_delay: float = 1.0

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes

    # Notification settings
    push_notifications_enabled: bool = True
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Menu bar app settings
    check_interval_seconds: int = 300  # 5 minutes

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            db_dir=os.getenv("ZARA_DB_DIR", os.path.join(
                os.path.expanduser("~"), ".zara_stock_tracker"
            )),
            country_code=os.getenv("ZARA_COUNTRY", "tr"),
            language=os.getenv("ZARA_LANGUAGE", "en"),
            request_timeout=int(os.getenv("ZARA_TIMEOUT", "15")),
            max_retries=int(os.getenv("ZARA_MAX_RETRIES", "3")),
            retry_base_delay=float(os.getenv("ZARA_RETRY_DELAY", "1.0")),
            cache_enabled=os.getenv(
                "ZARA_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("ZARA_CACHE_TTL", "300")),
            push_notifications_enabled=os.getenv(
                "ZARA_PUSH_ENABLED", "true").lower() == "true",
            telegram_enabled=os.getenv(
                "ZARA_TELEGRAM_ENABLED", "false").lower() == "true",
            telegram_bot_token=os.getenv("ZARA_TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("ZARA_TELEGRAM_CHAT_ID"),
            check_interval_seconds=int(
                os.getenv("ZARA_CHECK_INTERVAL", "300")),
            log_level=os.getenv("ZARA_LOG_LEVEL", "INFO"),
            log_file=os.getenv("ZARA_LOG_FILE"),
        )

    @property
    def database_path(self) -> str:
        """Get full database path"""
        return os.path.join(self.db_dir, "zara_stock.db")

    @property
    def backup_dir(self) -> str:
        """Get backup directory path"""
        return os.path.join(self.db_dir, "backups")


def setup_logging(config: Optional[Config] = None) -> None:
    """Configure logging for the application"""
    if config is None:
        config = Config.from_env()

    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]

    if config.log_file:
        log_dir = os.path.dirname(config.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(config.log_file))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True
    )

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


# Global config instance
config = Config.from_env()
