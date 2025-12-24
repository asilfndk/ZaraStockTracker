"""Stock checking and update service."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..db import get_db, ProductRepository, StockRepository, PriceHistoryRepository
from ..db.tables import ProductTable
from ..scraper import ZaraScraper


@dataclass
class StockAlert:
    """Alert for size becoming available."""
    product_id: int
    product_name: str
    size: str
    price: float


@dataclass
class UpdateResult:
    """Result of stock update operation."""
    updated: int
    changes: int
    alerts: List[StockAlert]


class StockService:
    """Service for stock checking and updates."""

    @staticmethod
    def check_all_products(
        country_code: str = "tr",
        language: str = "en"
    ) -> UpdateResult:
        """
        Check and update all active products.

        Returns:
            UpdateResult with counts and alerts
        """
        updated = 0
        changes = 0
        alerts: List[StockAlert] = []

        # Get products to check
        with get_db() as db:
            products = ProductRepository.get_all_active(db)
            product_data = [
                {
                    "id": p.id,
                    "url": p.url,
                    "name": p.product_name,
                    "desired_size": p.desired_size
                }
                for p in products
            ]

        if not product_data:
            return UpdateResult(0, 0, [])

        scraper = ZaraScraper(country_code, language)

        for pdata in product_data:
            try:
                result = scraper.get_product_info(pdata["url"])
                if not result:
                    continue

                with get_db() as db:
                    product = ProductRepository.get_by_id(db, pdata["id"])
                    if not product:
                        continue

                    # Update sizes
                    for size_info in result.sizes:
                        existing = StockRepository.get_by_product_and_size(
                            db, product.id, size_info.size
                        )

                        new_in_stock = size_info.in_stock

                        if existing:
                            old_in_stock = existing.in_stock

                            if old_in_stock != new_in_stock:
                                changes += 1

                                # Check if desired size came in stock
                                if (new_in_stock and
                                    pdata["desired_size"] and
                                        size_info.size.upper() == pdata["desired_size"].upper()):
                                    alerts.append(StockAlert(
                                        product_id=pdata["id"],
                                        product_name=pdata["name"],
                                        size=size_info.size,
                                        price=result.price
                                    ))

                            existing.in_stock = new_in_stock
                            existing.stock_status = size_info.stock_status
                            existing.last_updated = datetime.now()
                        else:
                            StockRepository.create(
                                db,
                                product_id=product.id,
                                size=size_info.size,
                                in_stock=new_in_stock,
                                stock_status=size_info.stock_status
                            )

                    # Update product
                    product.price = result.price
                    product.old_price = result.old_price
                    product.discount = result.discount
                    product.last_check = datetime.now()

                    # Record price history
                    PriceHistoryRepository.add_if_changed(
                        db, product.id, result.price,
                        result.old_price, result.discount
                    )

                    updated += 1

            except Exception as e:
                print(f"Error updating {pdata['name']}: {e}")
                continue

        return UpdateResult(updated, changes, alerts)

    @staticmethod
    def check_desired_size(product: ProductTable) -> Optional[bool]:
        """Check if desired size is in stock."""
        if not product.desired_size:
            return None

        for stock in product.stock_statuses:
            if stock.size.upper() == product.desired_size.upper():
                return stock.in_stock

        return None
