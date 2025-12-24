"""Database models and connection with backup support"""
import functools
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy import event
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional, List
import os
import shutil
import logging

logger = logging.getLogger(__name__)

# Database connection - store in user's home directory for write access
DB_DIR = os.path.join(os.path.expanduser("~"), ".zara_stock_tracker")
BACKUP_DIR = os.path.join(DB_DIR, "backups")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(DB_DIR, "zara_stock.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# Database setup with better concurrency
engine = create_engine(
    DATABASE_URL,
    # Increased timeout for Playwright operations
    connect_args={'timeout': 60, 'check_same_thread': False},
    echo=False
)

# Enable WAL mode for better concurrency


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ZaraProduct(Base):
    """Zara products being tracked"""
    __tablename__ = "zara_products"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False)
    product_name = Column(String(300))
    product_id = Column(String(50))  # Zara's product ID
    price = Column(Float, default=0.0)
    old_price = Column(Float, default=0.0)  # Price before discount
    discount = Column(String(20))  # Discount percentage
    color = Column(String(100))
    image_url = Column(String(500))
    desired_size = Column(String(20))  # Size user wants to track
    active = Column(Integer, default=1)  # Is tracking active?
    created_at = Column(DateTime, default=datetime.now)
    last_check = Column(DateTime)

    stock_statuses = relationship(
        "ZaraStockStatus", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan")


class ZaraStockStatus(Base):
    """Zara product size stock statuses"""
    __tablename__ = "zara_stock_statuses"

    id = Column(Integer, primary_key=True, index=True)
    zara_product_id = Column(Integer, ForeignKey(
        "zara_products.id"), nullable=False)
    size = Column(String(20), nullable=False)
    in_stock = Column(Integer, default=0)  # 1: yes, 0: no
    stock_status = Column(String(50))  # in_stock, out_of_stock, low_on_stock
    last_updated = Column(DateTime, default=datetime.now)

    product = relationship("ZaraProduct", back_populates="stock_statuses")


class PriceHistory(Base):
    """Price history for products"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    zara_product_id = Column(Integer, ForeignKey(
        "zara_products.id"), nullable=False)
    price = Column(Float, nullable=False)
    old_price = Column(Float)
    discount = Column(String(20))
    recorded_at = Column(DateTime, default=datetime.now)

    product = relationship("ZaraProduct", back_populates="price_history")


class UserSettings(Base):
    """User settings storage"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def retry_on_lock(max_retries=10, initial_delay=0.5):
    """Retry operation if database is locked with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e):
                        if i == max_retries - 1:
                            logger.error(
                                f"Database locked after {max_retries} retries in {func.__name__}")
                            raise
                        logger.debug(
                            f"Database locked, retrying in {delay}s...")
                        time.sleep(delay)
                        # Exponential backoff, max 5s
                        delay = min(delay * 1.5, 5.0)
                    else:
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator


def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get database session"""
    return SessionLocal()


@retry_on_lock()
def add_price_history(product_id: int, price: float, old_price: Optional[float] = None, discount: Optional[str] = None) -> None:
    """Add price history record (only if price changed)"""
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


def get_price_history(product_id: int, limit: int = 30) -> List[PriceHistory]:
    """Get price history for a product"""
    session = get_session()
    try:
        return session.query(PriceHistory).filter(
            PriceHistory.zara_product_id == product_id
        ).order_by(PriceHistory.recorded_at.desc()).limit(limit).all()
    finally:
        session.close()


def get_setting(key: str, default: str = "") -> str:
    """Get a user setting"""
    session = get_session()
    try:
        setting = session.query(UserSettings).filter(
            UserSettings.setting_key == key).first()
        return setting.setting_value if setting else default
    finally:
        session.close()


@retry_on_lock()
def set_setting(key: str, value: str) -> None:
    """Set a user setting"""
    session = get_session()
    try:
        setting = session.query(UserSettings).filter(
            UserSettings.setting_key == key).first()
        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.now()
        else:
            setting = UserSettings(setting_key=key, setting_value=value)
            session.add(setting)
        session.commit()
    finally:
        session.close()


def backup_database(max_backups: int = 5) -> Optional[str]:
    """
    Create a backup of the database.

    Args:
        max_backups: Maximum number of backups to keep

    Returns:
        Path to backup file or None if failed
    """
    if not os.path.exists(DATABASE_PATH):
        logger.warning("Database file does not exist, nothing to backup")
        return None

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"zara_stock_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        # Copy only, no lock risk mostly
        shutil.copy2(DATABASE_PATH, backup_path)
        logger.info(f"Database backed up to: {backup_path}")

        # Cleanup old backups
        _cleanup_old_backups(max_backups)

        return backup_path
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


def _cleanup_old_backups(max_backups: int) -> None:
    """Remove old backups keeping only the most recent ones"""
    try:
        backups = sorted([
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith("zara_stock_backup_") and f.endswith(".db")
        ])

        while len(backups) > max_backups:
            old_backup = backups.pop(0)
            os.remove(os.path.join(BACKUP_DIR, old_backup))
            logger.debug(f"Removed old backup: {old_backup}")
    except Exception as e:
        logger.warning(f"Backup cleanup failed: {e}")


def restore_database(backup_path: str) -> bool:
    """
    Restore database from a backup file.

    Args:
        backup_path: Path to backup file

    Returns:
        True if successful
    """
    if not os.path.exists(backup_path):
        logger.error(f"Backup file not found: {backup_path}")
        return False

    try:
        # Create safety backup first
        if os.path.exists(DATABASE_PATH):
            safety_backup = DATABASE_PATH + ".before_restore"
            shutil.copy2(DATABASE_PATH, safety_backup)

        shutil.copy2(backup_path, DATABASE_PATH)
        logger.info(f"Database restored from: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def list_backups() -> List[dict]:
    """
    List available database backups.

    Returns:
        List of backup info dicts with path, filename, created_at, size
    """
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
