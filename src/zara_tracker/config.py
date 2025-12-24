"""Configuration settings for Zara Stock Tracker."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class RegionConfig:
    """Configuration for a supported region."""
    code: str
    name: str
    flag: str
    languages: List[str]


# Supported regions
REGIONS: Dict[str, RegionConfig] = {
    "tr": RegionConfig("tr", "Turkey", "🇹🇷", ["en", "tr"]),
    "us": RegionConfig("us", "United States", "🇺🇸", ["en"]),
    "uk": RegionConfig("uk", "United Kingdom", "🇬🇧", ["en"]),
    "de": RegionConfig("de", "Germany", "🇩🇪", ["de", "en"]),
    "fr": RegionConfig("fr", "France", "🇫🇷", ["fr", "en"]),
    "es": RegionConfig("es", "Spain", "🇪🇸", ["es", "en"]),
    "it": RegionConfig("it", "Italy", "🇮🇹", ["it", "en"]),
}


@dataclass
class Config:
    """Application configuration."""

    # Paths
    app_dir: Path = field(
        default_factory=lambda: Path.home() / ".zara_stock_tracker")

    # Database
    @property
    def db_path(self) -> Path:
        return self.app_dir / "zara_stock.db"

    @property
    def backup_dir(self) -> Path:
        return self.app_dir / "backups"

    # Defaults
    default_country: str = "tr"
    default_language: str = "en"
    default_check_interval: int = 300  # 5 minutes

    # API
    api_timeout: int = 15
    cache_ttl: int = 300  # 5 minutes
    max_retries: int = 3

    def __post_init__(self):
        """Ensure directories exist."""
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
