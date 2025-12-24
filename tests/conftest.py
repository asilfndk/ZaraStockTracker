"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from zara_tracker.db.tables import Base


@pytest.fixture
def test_db():
    """Create a test database in memory."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_product_info():
    """Sample product info for testing."""
    from zara_tracker.models.product import ProductInfo, SizeStock

    return ProductInfo(
        product_id="12345678",
        name="Test Product",
        price=1990.0,
        old_price=2490.0,
        discount="-20%",
        color="Black",
        image_url="https://example.com/image.jpg",
        url="https://www.zara.com/tr/en/test-p12345678.html?v1=12345678",
        sizes=[
            SizeStock("S", True, "in_stock", 1990.0, 2490.0, "-20%"),
            SizeStock("M", False, "out_of_stock", 1990.0, 2490.0, "-20%"),
            SizeStock("L", True, "low_on_stock", 1990.0, 2490.0, "-20%"),
        ]
    )
