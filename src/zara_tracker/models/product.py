"""Product and stock data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SizeStock:
    """Stock status for a specific size."""
    size: str
    in_stock: bool
    stock_status: str  # "in_stock", "out_of_stock", "low_on_stock"
    price: float = 0.0
    old_price: float = 0.0
    discount: str = ""


@dataclass
class ProductInfo:
    """Product information from scraper."""
    product_id: str
    name: str
    price: float
    old_price: float
    discount: str
    color: str
    image_url: str
    url: str
    sizes: List[SizeStock]


@dataclass
class Product:
    """Product being tracked."""
    id: Optional[int] = None
    url: str = ""
    product_name: str = ""
    product_id: str = ""
    price: float = 0.0
    old_price: float = 0.0
    discount: str = ""
    color: str = ""
    image_url: str = ""
    desired_size: Optional[str] = None
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_check: Optional[datetime] = None

    # Related data (populated separately)
    stock_statuses: List[SizeStock] = field(default_factory=list)


@dataclass
class PriceHistory:
    """Price history record."""
    id: Optional[int] = None
    product_id: int = 0
    price: float = 0.0
    old_price: float = 0.0
    discount: str = ""
    recorded_at: datetime = field(default_factory=datetime.now)
