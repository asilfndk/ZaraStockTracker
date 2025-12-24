"""
Product Service - Business logic for product management.
"""
import logging
from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


class ProductService:
    """Service for product-related business logic."""

    def __init__(self, session_factory, scraper_factory):
        """
        Initialize ProductService.

        Args:
            session_factory: Callable that returns a database session
            scraper_factory: Callable(url, country, language) that returns a scraper
        """
        self._session_factory = session_factory
        self._scraper_factory = scraper_factory

    def add_product(
        self,
        url: str,
        desired_size: Optional[str] = None,
        country: str = "tr",
        language: str = "en"
    ) -> Tuple[bool, str, Optional[bool]]:
        """
        Add a new product to tracking.

        Args:
            url: Product URL
            desired_size: Size to track (optional)
            country: Country code
            language: Language code

        Returns:
            Tuple of (success, message, desired_size_in_stock)
        """
        # Import here to avoid circular imports
        from zara_tracker.core.repository import (
            ProductRepository, StockRepository, PriceHistoryRepository, get_session
        )
        from zara_tracker.core.models import ZaraProduct, ZaraStockStatus

        session = get_session()

        try:
            # Check if already exists
            existing = ProductRepository.get_by_url(session, url)
            if existing:
                session.close()
                return False, "This product is already being tracked!", None

            # Fetch product info
            try:
                scraper = self._scraper_factory(url, country, language)
                result = scraper.get_stock_status(url)
            except Exception as e:
                session.close()
                return False, f"Error fetching product: {str(e)}", None

            if not result:
                session.close()
                return False, "Could not get product info. Check the URL.", None

            # Validate desired size
            if desired_size:
                size_exists = any(
                    s.size.upper() == desired_size.upper()
                    for s in result.sizes
                )
                if not size_exists:
                    available = [s.size for s in result.sizes]
                    session.close()
                    return False, f"Size '{desired_size}' not found. Available: {', '.join(available)}", None

            # Create product
            product = ZaraProduct(
                url=url,
                product_name=result.name,
                product_id=result.product_id,
                price=result.price,
                old_price=result.old_price,
                discount=result.discount,
                color=result.color,
                image_url=result.image_url,
                desired_size=desired_size.upper() if desired_size else None,
                last_check=datetime.now()
            )
            session.add(product)
            session.flush()

            # Add price history
            PriceHistoryRepository.add_if_changed(
                product.id,
                result.price,
                result.old_price,
                result.discount
            )

            # Add stock statuses
            for size in result.sizes:
                stock_status = ZaraStockStatus(
                    zara_product_id=product.id,
                    size=size.size,
                    in_stock=1 if size.in_stock else 0,
                    stock_status=size.stock_status,
                    last_updated=datetime.now()
                )
                session.add(stock_status)

            session.commit()

            # Check if desired size is in stock
            desired_in_stock = None
            if desired_size:
                for size in result.sizes:
                    if size.size.upper() == desired_size.upper():
                        desired_in_stock = size.in_stock
                        break

            session.close()
            return True, f"'{result.name}' added to tracking list!", desired_in_stock

        except OperationalError as e:
            session.rollback()
            session.close()
            if "database is locked" in str(e):
                return False, "Database is busy. Please try again.", None
            raise

    def delete_product(self, product_id: int) -> bool:
        """Delete a product from tracking."""
        from zara_tracker.core.repository import ProductRepository, get_session

        session = get_session()
        try:
            product = ProductRepository.get_by_id(session, product_id)
            if product:
                ProductRepository.delete(session, product)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_all_active(self) -> List:
        """Get all active products."""
        from zara_tracker.core.repository import ProductRepository, get_session

        session = get_session()
        try:
            return ProductRepository.get_all_active(session)
        finally:
            session.close()
