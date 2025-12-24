"""Repository pattern for database operations."""

import shutil
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..config import config
from .tables import ProductTable, StockStatusTable, PriceHistoryTable, SettingsTable


class ProductRepository:
    """Repository for product operations."""

    @staticmethod
    def get_all_active(db: Session) -> List[ProductTable]:
        """Get all active products."""
        return db.query(ProductTable).filter(ProductTable.active == True).all()

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[ProductTable]:
        """Get product by ID."""
        return db.query(ProductTable).filter(ProductTable.id == product_id).first()

    @staticmethod
    def get_by_url(db: Session, url: str) -> Optional[ProductTable]:
        """Get product by URL."""
        return db.query(ProductTable).filter(ProductTable.url == url).first()

    @staticmethod
    def create(db: Session, **kwargs) -> ProductTable:
        """Create a new product."""
        product = ProductTable(**kwargs)
        db.add(product)
        db.flush()
        return product

    @staticmethod
    def delete(db: Session, product: ProductTable) -> None:
        """Delete a product."""
        db.delete(product)

    @staticmethod
    def count_active(db: Session) -> int:
        """Count active products."""
        return db.query(ProductTable).filter(ProductTable.active == True).count()


class StockRepository:
    """Repository for stock status operations."""

    @staticmethod
    def get_by_product(db: Session, product_id: int) -> List[StockStatusTable]:
        """Get all stock statuses for a product."""
        return db.query(StockStatusTable).filter(
            StockStatusTable.product_id == product_id
        ).order_by(StockStatusTable.size).all()

    @staticmethod
    def get_by_product_and_size(db: Session, product_id: int, size: str) -> Optional[StockStatusTable]:
        """Get stock status for a specific size."""
        return db.query(StockStatusTable).filter(
            StockStatusTable.product_id == product_id,
            StockStatusTable.size == size
        ).first()

    @staticmethod
    def create(db: Session, **kwargs) -> StockStatusTable:
        """Create a stock status."""
        stock = StockStatusTable(**kwargs)
        db.add(stock)
        return stock

    @staticmethod
    def upsert(db: Session, product_id: int, size: str, in_stock: bool, stock_status: str) -> StockStatusTable:
        """Create or update stock status."""
        existing = StockRepository.get_by_product_and_size(
            db, product_id, size)
        if existing:
            existing.in_stock = in_stock
            existing.stock_status = stock_status
            existing.last_updated = datetime.now()
            return existing
        return StockRepository.create(
            db,
            product_id=product_id,
            size=size,
            in_stock=in_stock,
            stock_status=stock_status
        )


class PriceHistoryRepository:
    """Repository for price history operations."""

    @staticmethod
    def add(db: Session, product_id: int, price: float, old_price: float = 0.0, discount: str = "") -> PriceHistoryTable:
        """Add a price history record."""
        record = PriceHistoryTable(
            product_id=product_id,
            price=price,
            old_price=old_price,
            discount=discount
        )
        db.add(record)
        return record

    @staticmethod
    def add_if_changed(db: Session, product_id: int, price: float, old_price: float = 0.0, discount: str = "") -> Optional[PriceHistoryTable]:
        """Add price history only if price changed."""
        last = db.query(PriceHistoryTable).filter(
            PriceHistoryTable.product_id == product_id
        ).order_by(PriceHistoryTable.recorded_at.desc()).first()

        if not last or last.price != price:
            return PriceHistoryRepository.add(db, product_id, price, old_price, discount)
        return None

    @staticmethod
    def get_history(db: Session, product_id: int, limit: int = 30) -> List[PriceHistoryTable]:
        """Get price history for a product."""
        return db.query(PriceHistoryTable).filter(
            PriceHistoryTable.product_id == product_id
        ).order_by(PriceHistoryTable.recorded_at.desc()).limit(limit).all()


class SettingsRepository:
    """Repository for user settings."""

    @staticmethod
    def get(db: Session, key: str, default: str = "") -> str:
        """Get a setting value."""
        setting = db.query(SettingsTable).filter(
            SettingsTable.key == key).first()
        return setting.value if setting else default

    @staticmethod
    def set(db: Session, key: str, value: str) -> SettingsTable:
        """Set a setting value."""
        setting = db.query(SettingsTable).filter(
            SettingsTable.key == key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.now()
        else:
            setting = SettingsTable(key=key, value=value)
            db.add(setting)
        return setting


class BackupRepository:
    """Repository for database backup operations."""

    @staticmethod
    def create_backup(max_backups: int = 5) -> Optional[str]:
        """Create a database backup."""
        if not config.db_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config.backup_dir / f"backup_{timestamp}.db"

        try:
            shutil.copy2(config.db_path, backup_path)
            BackupRepository._cleanup_old(max_backups)
            return str(backup_path)
        except Exception:
            return None

    @staticmethod
    def _cleanup_old(max_backups: int) -> None:
        """Remove old backups."""
        backups = sorted(config.backup_dir.glob("backup_*.db"))
        while len(backups) > max_backups:
            backups.pop(0).unlink()

    @staticmethod
    def restore(backup_path: str) -> bool:
        """Restore database from backup."""
        from pathlib import Path
        backup = Path(backup_path)

        if not backup.exists():
            return False

        try:
            if config.db_path.exists():
                shutil.copy2(config.db_path, str(
                    config.db_path) + ".before_restore")
            shutil.copy2(backup, config.db_path)
            return True
        except Exception:
            return False

    @staticmethod
    def list_backups() -> List[dict]:
        """List all available backups."""
        backups = []
        for f in sorted(config.backup_dir.glob("backup_*.db"), reverse=True):
            stat = f.stat()
            backups.append({
                "path": str(f),
                "filename": f.name,
                "created_at": datetime.fromtimestamp(stat.st_mtime),
                "size_bytes": stat.st_size
            })
        return backups
