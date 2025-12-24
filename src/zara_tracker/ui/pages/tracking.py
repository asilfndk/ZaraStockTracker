"""Tracking list page."""

import time
import streamlit as st

from ...db import get_db
from ...db.repository import ProductRepository, SettingsRepository
from ...services import ProductService, StockService, send_notification
from ..components import render_product_card, render_empty_state


def render() -> None:
    """Render the tracking list page."""

    # Header row
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        with get_db() as db:
            last_product = db.query(ProductRepository.get_all_active(
                db)).first() if False else None
        # Get last check time
        products = ProductService.get_all_active()
        if products and products[0].last_check:
            st.caption(
                f"🕐 Last update: {products[0].last_check.strftime('%H:%M:%S')}")
        else:
            st.caption("🕐 No updates yet")

    with col2:
        count = ProductService.get_product_count()
        st.metric("📦 Tracking", count)

    with col3:
        if st.button("🔄 Update Now", type="primary", use_container_width=True):
            _do_update()

    st.divider()

    # Product list
    products = ProductService.get_all_active()

    if products:
        for product in products:
            render_product_card(product, on_delete=_delete_product)
    else:
        render_empty_state("No products being tracked")


def _do_update() -> None:
    """Perform stock update for all products."""
    with st.spinner("Checking stocks..."):
        # Get settings
        with get_db() as db:
            country = SettingsRepository.get(db, "country_code", "tr")
            language = SettingsRepository.get(db, "language", "en")

        result = StockService.check_all_products(country, language)

        # Send notifications for alerts
        for alert in result.alerts:
            send_notification(
                "🎉 Size Available!",
                f"{alert.product_name} - {alert.size} is now in stock!"
            )
            st.balloons()
            st.success(
                f"🎉 **{alert.product_name}** - {alert.size} is IN STOCK!")

        st.success(
            f"✅ {result.updated} products updated, {result.changes} changes!")
        time.sleep(1)
        st.rerun()


def _delete_product(product_id: int) -> None:
    """Delete a product."""
    ProductService.delete_product(product_id)
    st.rerun()
