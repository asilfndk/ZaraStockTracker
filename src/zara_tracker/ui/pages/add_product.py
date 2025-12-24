"""Add product page."""

import time
import streamlit as st

from ...db import get_db
from ...db.repository import SettingsRepository
from ...services import ProductService, send_notification


def render() -> None:
    """Render the add product page."""

    st.subheader("➕ Add New Product")

    st.write("Paste a Zara product URL and enter the size you want to track:")

    # URL input
    url_input = st.text_input(
        "🔗 Product URL",
        placeholder="https://www.zara.com/tr/en/product-name-p12345678.html?v1=...",
        help="Paste product URL from Zara website"
    )

    # Size input
    col1, col2 = st.columns([1, 1])
    with col1:
        size_input = st.text_input(
            "📏 Desired Size",
            placeholder="E.g.: S, M, L, XL, 38, 40...",
            help="Size you want to track"
        ).strip()

    with col2:
        st.write("")
        st.write("")
        st.caption("💡 You'll get notified when this size is in stock!")

    st.caption("🏪 Supported: **Zara** (zara.com)")

    # Add button
    if st.button("➕ Add Product", type="primary", use_container_width=True):
        if not url_input:
            st.warning("⚠️ Please enter a URL!")
            return

        if not size_input:
            st.warning("⚠️ Please enter the size you want to track!")
            return

        with st.spinner("Getting product info..."):
            # Get settings
            with get_db() as db:
                country = SettingsRepository.get(db, "country_code", "tr")
                language = SettingsRepository.get(db, "language", "en")

            # Add product
            result = ProductService.add_product(
                url_input,
                size_input,
                country,
                language
            )

            if result.success:
                st.success(f"✅ {result.message}")

                if result.desired_size_in_stock:
                    st.balloons()
                    send_notification(
                        "🎉 Size Available!",
                        f"The size you wanted is already in stock!"
                    )
                    st.success(f"🎉 Great! {size_input} is currently IN STOCK!")
                else:
                    st.info(
                        f"📢 {size_input} is currently out of stock. You'll be notified when it's back!")

                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ {result.message}")
