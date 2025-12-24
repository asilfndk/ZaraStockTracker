"""
Stock Service - Business logic for stock tracking and updates.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class StockService:
    """Service for stock tracking business logic."""

    def __init__(self, session_factory, scraper_factory):
        """
        Initialize StockService.

        Args:
            session_factory: Callable that returns a database session
            scraper_factory: Callable(url, country, language) that returns a scraper
        """
        self._session_factory = session_factory
        self._scraper_factory = scraper_factory

    def update_all_products(
        self,
        country: str = "tr",
        language: str = "en"
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Update stock status for all active products.

        Args:
            country: Country code
            language: Language code

        Returns:
            Tuple of (updated_count, changes_count, size_alerts_list)
        """
        from zara_tracker.core.repository import (
            ProductRepository, StockRepository, get_session
        )
        from zara_tracker.core.models import ZaraStockStatus

        session = get_session()

        try:
            products = ProductRepository.get_all_active(session)

            if not products:
                return 0, 0, []

            updated = 0
            changes = 0
            size_alerts = []

            for product in products:
                try:
                    scraper = self._scraper_factory(
                        product.url, country, language)
                    result = scraper.get_stock_status(product.url)

                    if not result:
                        continue

                    for size_info in result.sizes:
                        current_stock = StockRepository.get_by_product_and_size(
                            session, product.id, size_info.size
                        )

                        new_stock = 1 if size_info.in_stock else 0

                        if current_stock:
                            if current_stock.in_stock != new_stock:
                                changes += 1

                                # Alert if desired size came in stock
                                if (new_stock == 1 and
                                    product.desired_size and
                                        size_info.size.upper() == product.desired_size.upper()):
                                    size_alerts.append({
                                        'product_id': product.id,
                                        'product_name': product.product_name,
                                        'size': size_info.size,
                                        'price': result.price
                                    })

                            current_stock.in_stock = new_stock
                            current_stock.stock_status = size_info.stock_status
                            current_stock.last_updated = datetime.now()
                        else:
                            new_status = ZaraStockStatus(
                                zara_product_id=product.id,
                                size=size_info.size,
                                in_stock=new_stock,
                                stock_status=size_info.stock_status
                            )
                            session.add(new_status)

                    product.last_check = datetime.now()
                    product.price = result.price
                    product.old_price = result.old_price
                    product.discount = result.discount
                    updated += 1

                except Exception as e:
                    logger.error(f"Update error ({product.product_name}): {e}")

            session.commit()
            return updated, changes, size_alerts

        finally:
            session.close()

    def check_desired_size_availability(
        self,
        product_id: int,
        desired_size: str
    ) -> Tuple[Optional[bool], Optional[str]]:
        """
        Check if a desired size is in stock.

        Args:
            product_id: Product ID
            desired_size: Desired size to check

        Returns:
            Tuple of (is_in_stock, stock_status) or (None, None) if not found
        """
        from zara_tracker.core.repository import StockRepository, get_session

        if not desired_size:
            return None, None

        session = get_session()
        try:
            statuses = StockRepository.get_by_product(session, product_id)
            for stock in statuses:
                if stock.size.upper() == desired_size.upper():
                    return stock.in_stock == 1, stock.stock_status
            return None, None
        finally:
            session.close()

    def get_stock_statuses(self, product_id: int) -> List:
        """Get all stock statuses for a product."""
        from zara_tracker.core.repository import StockRepository, get_session

        session = get_session()
        try:
            return StockRepository.get_by_product(session, product_id)
        finally:
            session.close()
