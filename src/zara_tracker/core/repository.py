"""
Repository pattern implementation for database operations.

Provides clean separation between data access and business logic.
"""
import functools
import logging
import os
import shutil
import time
from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session

from .models import (
    Base,
    ZaraProduct,
    ZaraStockStatus,
    PriceHistory,
    UserSettings
)

logger = logging.getLogger(__name__)

# Database paths
DB_DIR = os.path.join(os.path.expanduser("~"), ".zara_stock_tracker")
BACKUP_DIR = os.path.join(DB_DIR, "backups")
DATABASE_PATH = os.path.join(DB_DIR, "zara_stock.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Ensure directories exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"timeout": 60, "check_same_thread": False},
    echo=False
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode for better concurrency."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def retry_on_lock(max_retries: int = 10, initial_delay: float = 0.5):
    """Decorator to retry operations on database lock with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e):
                        if attempt == max_retries - 1:
                            logger.error(
                                f"Database locked after {max_retries} retries")
                            raise
                        logger.debug(
                            f"Database locked, retry {attempt + 1}/{max_retries}")
                        time.sleep(delay)
                        delay = min(delay * 1.5, 5.0)
                    else:
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator


def init_db() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Get a new database session."""
    return SessionLocal()


class ProductRepository:
    """Repository for product-related database operations."""

    @staticmethod
    def get_all_active(session: Session) -> List[ZaraProduct]:
        """Get all active products."""
        return session.query(ZaraProduct).filter(ZaraProduct.active == 1).all()

    @staticmethod
    def get_by_id(session: Session, product_id: int) -> Optional[ZaraProduct]:
        """Get product by ID."""
        return session.query(ZaraProduct).filter(ZaraProduct.id == product_id).first()

    @staticmethod
    def get_by_url(session: Session, url: str) -> Optional[ZaraProduct]:
        """Get product by URL."""
        return session.query(ZaraProduct).filter(ZaraProduct.url == url).first()

    @staticmethod
    def create(session: Session, **kwargs) -> ZaraProduct:
        """Create a new product."""
        product = ZaraProduct(**kwargs)
        session.add(product)
        return product

    @staticmethod
    def delete(session: Session, product: ZaraProduct) -> None:
        """Delete a product."""
        session.delete(product)

    @staticmethod
    def count_active(session: Session) -> int:
        """Count active products."""
        return session.query(ZaraProduct).filter(ZaraProduct.active == 1).count()


class StockRepository:
    """Repository for stock status operations."""

    @staticmethod
    def get_by_product(session: Session, product_id: int) -> List[ZaraStockStatus]:
        """Get all stock statuses for a product."""
        return session.query(ZaraStockStatus).filter(
            ZaraStockStatus.zara_product_id == product_id
        ).order_by(ZaraStockStatus.size).all()

    @staticmethod
    def get_by_product_and_size(
        session: Session,
        product_id: int,
        size: str
    ) -> Optional[ZaraStockStatus]:
        """Get stock status for a specific product size."""
        return session.query(ZaraStockStatus).filter(
            ZaraStockStatus.zara_product_id == product_id,
            ZaraStockStatus.size == size
        ).first()

    @staticmethod
    def create(session: Session, **kwargs) -> ZaraStockStatus:
        """Create a new stock status."""
        status = ZaraStockStatus(**kwargs)
        session.add(status)
        return status


class PriceHistoryRepository:
    """Repository for price history operations."""

    @staticmethod
    @retry_on_lock()
    def add_if_changed(
        product_id: int,
        price: float,
        old_price: Optional[float] = None,
        discount: Optional[str] = None
    ) -> None:
        """Add price history record only if price changed."""
        session = get_session()
        try:
            last_record = session.query(PriceHistory).filter(
                PriceHistory.zara_product_id == product_id
            ).order_by(PriceHistory.recorded_at.desc()).first()

            if not last_record or last_record.price != price:
                history = PriceHistory(
                    zara_product_id=product_id,
                    price=price,
                    old_price=old_price,
                    discount=discount
                )
                session.add(history)
                session.commit()
        finally:
            session.close()

    @staticmethod
    def get_history(
        session: Session,
        product_id: int,
        limit: int = 30
    ) -> List[PriceHistory]:
        """Get price history for a product."""
        return session.query(PriceHistory).filter(
            PriceHistory.zara_product_id == product_id
        ).order_by(PriceHistory.recorded_at.desc()).limit(limit).all()


class SettingsRepository:
    """Repository for user settings operations."""

    @staticmethod
    def get(key: str, default: str = "") -> str:
        """Get a setting value."""
        session = get_session()
        try:
            setting = session.query(UserSettings).filter(
                UserSettings.setting_key == key
            ).first()
            return setting.setting_value if setting else default
        finally:
            session.close()

    @staticmethod
    @retry_on_lock()
    def set(key: str, value: str) -> None:
        """Set a setting value."""
        session = get_session()
        try:
            setting = session.query(UserSettings).filter(
                UserSettings.setting_key == key
            ).first()
            if setting:
                setting.setting_value = value
                setting.updated_at = datetime.now()
            else:
                setting = UserSettings(setting_key=key, setting_value=value)
                session.add(setting)
            session.commit()
        finally:
            session.close()


class BackupRepository:
    """Repository for database backup operations."""

    @staticmethod
    def create_backup(max_backups: int = 5) -> Optional[str]:
        """Create a database backup."""
        if not os.path.exists(DATABASE_PATH):
            logger.warning("Database file does not exist")
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                BACKUP_DIR, f"zara_stock_backup_{timestamp}.db")
            shutil.copy2(DATABASE_PATH, backup_path)
            logger.info(f"Backup created: {backup_path}")
            BackupRepository._cleanup_old(max_backups)
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    @staticmethod
    def _cleanup_old(max_backups: int) -> None:
        """Remove old backups."""
        try:
            backups = sorted([
                f for f in os.listdir(BACKUP_DIR)
                if f.startswith("zara_stock_backup_") and f.endswith(".db")
            ])
            while len(backups) > max_backups:
                os.remove(os.path.join(BACKUP_DIR, backups.pop(0)))
        except Exception as e:
            logger.warning(f"Backup cleanup failed: {e}")

    @staticmethod
    def restore(backup_path: str) -> bool:
        """Restore database from backup."""
        if not os.path.exists(backup_path):
            logger.error(f"Backup not found: {backup_path}")
            return False

        try:
            if os.path.exists(DATABASE_PATH):
                shutil.copy2(DATABASE_PATH, DATABASE_PATH + ".before_restore")
            shutil.copy2(backup_path, DATABASE_PATH)
            logger.info(f"Restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    @staticmethod
    def list_all() -> List[dict]:
        """List all available backups."""
        backups = []
        try:
            for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
                if f.startswith("zara_stock_backup_") and f.endswith(".db"):
                    path = os.path.join(BACKUP_DIR, f)
                    stat = os.stat(path)
                    backups.append({
                        "path": path,
                        "filename": f,
                        "created_at": datetime.fromtimestamp(stat.st_mtime),
                        "size_bytes": stat.st_size
                    })
        except Exception as e:
            logger.warning(f"Failed to list backups: {e}")
        return backups


# Backward compatibility aliases
add_price_history = PriceHistoryRepository.add_if_changed


def get_price_history(product_id, limit=30): return PriceHistoryRepository.get_history(
    get_session(), product_id, limit
)


get_setting = SettingsRepository.get
set_setting = SettingsRepository.set
backup_database = BackupRepository.create_backup
restore_database = BackupRepository.restore
list_backups = BackupRepository.list_all
