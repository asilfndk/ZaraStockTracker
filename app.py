"""
Zara Stock Tracker - Streamlit Dashboard
A clean, minimal entry point for the Streamlit application.
"""
from zara_tracker.ui.pages import tracking, add_product, settings
from zara_tracker.db import init_db
import streamlit as st
from pathlib import Path

# Initialize the package path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))


# Get icon path
ICON_PATH = Path(__file__).parent / "icon.png"

# Page configuration
st.set_page_config(
    page_title="Zara Stock Tracker",
    page_icon=str(ICON_PATH) if ICON_PATH.exists() else "🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()

# Header with icon - using HTML for proper alignment
if ICON_PATH.exists():
    import base64
    with open(ICON_PATH, "rb") as f:
        icon_data = base64.b64encode(f.read()).decode()
    st.markdown(
        f'''
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
            <img src="data:image/png;base64,{icon_data}" width="45" style="border-radius: 8px;">
            <h1 style="margin: 0; padding: 0;">Zara Stock Tracker</h1>
        </div>
        ''',
        unsafe_allow_html=True
    )
else:
    st.title("🛍️ Zara Stock Tracker")
st.caption("🎯 Track sizes • 🔔 Get alerts • 📊 Price history")

# Main tabs
tab1, tab2, tab3 = st.tabs(["📋 Tracking List", "➕ Add Product", "⚙️ Settings"])

with tab1:
    tracking.render()

with tab2:
    add_product.render()

with tab3:
    settings.render()

# Footer
st.divider()
st.caption("v6.1")
