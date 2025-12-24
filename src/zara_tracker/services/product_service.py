"""Product management service."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from ..db import get_db, ProductRepository, StockRepository, PriceHistoryRepository
from ..db.tables import ProductTable
from ..scraper import ZaraScraper
from ..models.product import ProductInfo


@dataclass
class AddProductResult:
    """Result of adding a product."""
    success: bool
    message: str
    product_id: Optional[int] = None
    desired_size_in_stock: Optional[bool] = None


class ProductService:
    """Service for product management."""

    @staticmethod
    def add_product(
        url: str,
        desired_size: str,
        country_code: str = "tr",
        language: str = "en"
    ) -> AddProductResult:
        """
        Add a new product to tracking.

        Args:
            url: Zara product URL
            desired_size: Size to track
            country_code: Region code
            language: Language code

        Returns:
            AddProductResult with success status and message
        """
        # Validate URL
        if not ZaraScraper.is_supported_url(url):
            return AddProductResult(False, "Only Zara URLs are supported")

        # Check if already exists
        with get_db() as db:
            existing = ProductRepository.get_by_url(db, url)
            if existing:
                return AddProductResult(False, "This product is already being tracked")

        # Fetch product info
        scraper = ZaraScraper(country_code, language)
        product_info = scraper.get_product_info(url)

        if not product_info:
            return AddProductResult(False, "Could not fetch product info. Check the URL.")

        # Validate size exists
        size_upper = desired_size.upper()
        size_found = None
        for size in product_info.sizes:
            if size.size.upper() == size_upper or size_upper in size.size.upper():
                size_found = size
                break

        if not size_found:
            available = [s.size for s in product_info.sizes]
            return AddProductResult(
                False,
                f"Size '{desired_size}' not found. Available: {', '.join(available)}"
            )

        # Save to database
        with get_db() as db:
            product = ProductRepository.create(
                db,
                url=url,
                product_name=product_info.name,
                product_id=product_info.product_id,
                price=product_info.price,
                old_price=product_info.old_price,
                discount=product_info.discount,
                color=product_info.color,
                image_url=product_info.image_url,
                desired_size=size_found.size,
                last_check=datetime.now()
            )

            # Add stock statuses
            for size in product_info.sizes:
                StockRepository.create(
                    db,
                    product_id=product.id,
                    size=size.size,
                    in_stock=size.in_stock,
                    stock_status=size.stock_status
                )

            # Add initial price history
            PriceHistoryRepository.add(
                db,
                product.id,
                product_info.price,
                product_info.old_price,
                product_info.discount
            )

            return AddProductResult(
                success=True,
                message=f"'{product_info.name}' added to tracking!",
                product_id=product.id,
                desired_size_in_stock=size_found.in_stock
            )

    @staticmethod
    def delete_product(product_id: int) -> bool:
        """Delete a product from tracking."""
        with get_db() as db:
            product = ProductRepository.get_by_id(db, product_id)
            if product:
                ProductRepository.delete(db, product)
                return True
            return False

    @staticmethod
    def get_all_active() -> List[ProductTable]:
        """Get all active products with their stock statuses."""
        with get_db() as db:
            return ProductRepository.get_all_active(db)

    @staticmethod
    def get_product_count() -> int:
        """Get count of active products."""
        with get_db() as db:
            return ProductRepository.count_active(db)
