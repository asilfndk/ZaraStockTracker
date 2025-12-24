"""Reusable Streamlit UI components."""

import streamlit as st
from typing import List, Optional

from ..db.tables import ProductTable, StockStatusTable


def render_size_badge(stock: StockStatusTable, is_desired: bool = False) -> None:
    """Render a size badge with stock status."""
    if is_desired:
        if stock.in_stock:
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #28a745, #20c997); '
                f'color: white; padding: 12px; border-radius: 8px; text-align: center; '
                f'font-weight: bold; margin: 4px 0;">✅ {stock.size}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #dc3545, #c82333); '
                f'color: white; padding: 12px; border-radius: 8px; text-align: center; '
                f'font-weight: bold; margin: 4px 0;">❌ {stock.size}</div>',
                unsafe_allow_html=True
            )
    else:
        if stock.in_stock:
            if stock.stock_status == "low_on_stock":
                st.warning(f"⚠️ {stock.size}")
            else:
                st.success(f"✅ {stock.size}")
        else:
            st.error(f"❌ {stock.size}")


def render_product_card(
    product: ProductTable,
    on_delete: Optional[callable] = None
) -> None:
    """Render a product card with all its information."""

    with st.container():
        col1, col2, col3 = st.columns([1, 4, 1])

        with col1:
            if product.image_url:
                st.image(product.image_url, width=120)
            else:
                st.write("🖼️ No image")

        with col2:
            # Product name and link
            st.markdown(f"### [{product.product_name}]({product.url})")

            # Price
            if product.old_price and product.old_price > product.price:
                st.markdown(
                    f"💰 ~~₺{product.old_price:.0f}~~ → **₺{product.price:.0f}** {product.discount or ''}"
                )
            else:
                st.markdown(f"💰 **₺{product.price:.0f}**")

            # Color
            if product.color:
                st.caption(f"🎨 {product.color}")

            # Desired size
            if product.desired_size:
                st.caption(f"🎯 Tracking: **{product.desired_size}**")

            # Size grid
            st.write("**Sizes:**")
            stocks = list(product.stock_statuses)
            if stocks:
                cols = st.columns(min(len(stocks), 6))
                for i, stock in enumerate(stocks):
                    with cols[i % 6]:
                        is_desired = (
                            product.desired_size and
                            stock.size.upper() == product.desired_size.upper()
                        )
                        render_size_badge(stock, is_desired)

            # Last check
            if product.last_check:
                st.caption(
                    f"🕐 Last check: {product.last_check.strftime('%d.%m.%Y %H:%M')}")

        with col3:
            st.write("")
            st.write("")
            if on_delete:
                if st.button("🗑️", key=f"del_{product.id}", help="Delete"):
                    on_delete(product.id)

        st.divider()


def render_empty_state(message: str = "No products yet") -> None:
    """Render empty state message."""
    st.info(f"👆 {message}. Add a product from the 'Add Product' tab.")
