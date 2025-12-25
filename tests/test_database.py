"""Tests for database models and operations"""
from zara_tracker.core.models import ZaraProduct, ZaraStockStatus, PriceHistory, UserSettings
import pytest
from datetime import datetime
import sys
import os

# Add parent and src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestZaraProduct:
    """Tests for ZaraProduct model"""

    def test_create_product(self, test_session, sample_product_data):
        """Test creating a new product"""
        product = ZaraProduct(
            url=sample_product_data['url'],
            product_name=sample_product_data['product_name'],
            product_id=sample_product_data['product_id'],
            price=sample_product_data['price'],
            old_price=sample_product_data['old_price'],
            discount=sample_product_data['discount'],
            color=sample_product_data['color'],
            image_url=sample_product_data['image_url'],
            desired_size=sample_product_data['desired_size']
        )
        test_session.add(product)
        test_session.commit()

        assert product.id is not None
        assert product.product_name == 'Test Product'
        assert product.price == 999.99
        assert product.active == 1

    def test_product_defaults(self, test_session):
        """Test product default values"""
        product = ZaraProduct(
            url='https://www.zara.com/tr/en/test-p123.html?v1=123'
        )
        test_session.add(product)
        test_session.commit()

        assert product.active == 1
        assert product.price == 0.0
        assert product.old_price == 0.0
        assert product.created_at is not None


class TestZaraStockStatus:
    """Tests for ZaraStockStatus model"""

    def test_create_stock_status(self, test_session, sample_product_data):
        """Test creating stock status for a product"""
        # First create a product
        product = ZaraProduct(
            url=sample_product_data['url'],
            product_name=sample_product_data['product_name']
        )
        test_session.add(product)
        test_session.commit()

        # Create stock status
        status = ZaraStockStatus(
            zara_product_id=product.id,
            size='M',
            in_stock=1,
            stock_status='in_stock'
        )
        test_session.add(status)
        test_session.commit()

        assert status.id is not None
        assert status.size == 'M'
        assert status.in_stock == 1

    def test_product_stock_relationship(self, test_session, sample_product_data):
        """Test relationship between product and stock status"""
        product = ZaraProduct(
            url=sample_product_data['url'] + '&test=1',
            product_name=sample_product_data['product_name']
        )
        test_session.add(product)
        test_session.commit()

        # Add multiple sizes
        for size in ['S', 'M', 'L']:
            status = ZaraStockStatus(
                zara_product_id=product.id,
                size=size,
                in_stock=1 if size == 'M' else 0,
                stock_status='in_stock' if size == 'M' else 'out_of_stock'
            )
            test_session.add(status)
        test_session.commit()

        # Refresh product to get relationships
        test_session.refresh(product)
        assert len(product.stock_statuses) == 3


class TestPriceHistory:
    """Tests for PriceHistory model"""

    def test_create_price_history(self, test_session, sample_product_data):
        """Test creating price history entry"""
        product = ZaraProduct(
            url=sample_product_data['url'] + '&history=1',
            product_name=sample_product_data['product_name']
        )
        test_session.add(product)
        test_session.commit()

        history = PriceHistory(
            zara_product_id=product.id,
            price=999.99,
            old_price=1299.99,
            discount='-23%'
        )
        test_session.add(history)
        test_session.commit()

        assert history.id is not None
        assert history.price == 999.99
        assert history.recorded_at is not None


class TestUserSettings:
    """Tests for UserSettings model"""

    def test_create_setting(self, test_session):
        """Test creating a user setting"""
        setting = UserSettings(
            setting_key='test_key',
            setting_value='test_value'
        )
        test_session.add(setting)
        test_session.commit()

        assert setting.id is not None
        assert setting.setting_key == 'test_key'
        assert setting.setting_value == 'test_value'
