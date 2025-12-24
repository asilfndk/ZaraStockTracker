"""Pytest fixtures for Zara Stock Tracker tests"""
import pytest
import os
import sys
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'src'))

# Set test database path before importing database module
TEST_DB_DIR = tempfile.mkdtemp()
os.environ['ZARA_TEST_DB'] = os.path.join(TEST_DB_DIR, 'test_zara.db')


@pytest.fixture(scope="session")
def test_db_path():
    """Provide test database path"""
    return os.environ['ZARA_TEST_DB']


@pytest.fixture
def test_engine(test_db_path):
    """Create test database engine"""
    from zara_tracker.core.models import Base

    engine = create_engine(f"sqlite:///{test_db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_session(test_engine):
    """Create test database session"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        'url': 'https://www.zara.com/tr/en/test-product-p12345678.html?v1=123456789',
        'product_name': 'Test Product',
        'product_id': '12345678',
        'price': 999.99,
        'old_price': 1299.99,
        'discount': '-23%',
        'color': 'Black',
        'image_url': 'https://static.zara.net/photos/test.jpg',
        'desired_size': 'M'
    }


@pytest.fixture
def sample_api_response():
    """Sample Zara API response for mocking"""
    return [{
        'id': '123456789',
        'name': 'Test Product',
        'detail': {
            'colors': [{
                'name': 'Black',
                'productId': '123456789',
                'xmedia': [{
                    'kind': 'full',
                    'extraInfo': {
                        'deliveryUrl': 'https://static.zara.net/photos/test.jpg'
                    }
                }],
                'sizes': [
                    {
                        'name': 'S',
                        'availability': 'in_stock',
                        'price': 99999,
                        'oldPrice': 129999,
                        'discountLabel': '-23%'
                    },
                    {
                        'name': 'M',
                        'availability': 'out_of_stock',
                        'price': 99999,
                        'oldPrice': 129999,
                        'discountLabel': '-23%'
                    },
                    {
                        'name': 'L',
                        'availability': 'low_on_stock',
                        'price': 99999,
                        'oldPrice': 129999,
                        'discountLabel': '-23%'
                    }
                ]
            }]
        }
    }]
