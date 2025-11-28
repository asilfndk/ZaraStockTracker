"""Zara Stock Tracker - Size tracking with sound alerts"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import time
from database import init_db, get_session, ZaraProduct, ZaraStockStatus
from zara_scraper import ZaraScraper

# Page configuration
st.set_page_config(
    page_title="Zara Stock Tracker",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()

# Session state initialization
if 'alarm_triggered' not in st.session_state:
    st.session_state.alarm_triggered = set()
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'sound_enabled' not in st.session_state:
    st.session_state.sound_enabled = False
if 'pending_alarm' not in st.session_state:
    st.session_state.pending_alarm = False

# CSS styles
st.markdown("""
<style>
    .wanted-size-available {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white !important;
        padding: 15px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        margin: 5px 0;
        animation: pulse 2s infinite;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
    }
    .wanted-size-unavailable {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white !important;
        padding: 15px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        margin: 5px 0;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)


# Sound system functions
def toggle_sound():
    """Toggle sound state and play confirmation"""
    st.session_state.sound_enabled = not st.session_state.sound_enabled
    if st.session_state.sound_enabled:
        components.html("""
            <script>
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.frequency.value = 800;
                gain.gain.value = 0.3;
                osc.start();
                osc.stop(audioCtx.currentTime + 0.15);
            </script>
        """, height=0)


def play_alert_sound():
    """Trigger alert sound"""
    st.session_state.pending_alarm = True


def render_alarm_sound():
    """Play pending alarm sound"""
    if st.session_state.pending_alarm and st.session_state.sound_enabled:
        components.html("""
            <script>
                (function() {
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const duration = 1.5;
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    oscillator.type = 'sine';
                    
                    const now = audioContext.currentTime;
                    oscillator.frequency.setValueAtTime(400, now);
                    
                    for (let i = 0; i < 3; i++) {
                        oscillator.frequency.linearRampToValueAtTime(800, now + (i * 0.5) + 0.25);
                        oscillator.frequency.linearRampToValueAtTime(400, now + (i * 0.5) + 0.5);
                    }
                    
                    gainNode.gain.setValueAtTime(0.5, now);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration);
                    
                    oscillator.start(now);
                    oscillator.stop(now + duration);
                })();
            </script>
        """, height=0)
        st.session_state.pending_alarm = False


def check_desired_size_availability(product, stock_statuses):
    """Check if desired size is in stock"""
    if not product.desired_size:
        return None, None

    for stock in stock_statuses:
        if stock.size.upper() == product.desired_size.upper():
            return stock.in_stock == 1, stock.stock_status

    return None, None


def update_all_products():
    """Update stock status for all products"""
    session = get_session()
    products = session.query(ZaraProduct).filter(ZaraProduct.active == 1).all()

    if not products:
        session.close()
        return 0, 0, []

    scraper = ZaraScraper()
    updated = 0
    changes = 0
    size_alerts = []

    for product in products:
        try:
            result = scraper.get_stock_status(product.url)

            if result:
                for size_info in result.sizes:
                    current_stock = session.query(ZaraStockStatus).filter(
                        ZaraStockStatus.zara_product_id == product.id,
                        ZaraStockStatus.size == size_info.size
                    ).first()

                    new_stock = 1 if size_info.in_stock else 0

                    if current_stock:
                        if current_stock.in_stock != new_stock:
                            changes += 1

                            # Alert if desired size came in stock
                            if (new_stock == 1 and
                                product.desired_size and
                                    size_info.size.upper() == product.desired_size.upper()):
                                size_alerts.append({
                                    'product_id': product.id,
                                    'product_name': product.product_name,
                                    'size': size_info.size,
                                    'price': result.price
                                })

                        current_stock.in_stock = new_stock
                        current_stock.stock_status = size_info.stock_status
                        current_stock.last_updated = datetime.now()
                    else:
                        new_status = ZaraStockStatus(
                            zara_product_id=product.id,
                            size=size_info.size,
                            in_stock=new_stock,
                            stock_status=size_info.stock_status
                        )
                        session.add(new_status)

                product.last_check = datetime.now()
                product.price = result.price
                product.old_price = result.old_price
                product.discount = result.discount
                updated += 1

        except Exception as e:
            print(f"Update error ({product.product_name}): {e}")

    session.commit()
    session.close()
    return updated, changes, size_alerts


def add_product(url: str, desired_size: str = None):
    """Add new product to tracking"""
    session = get_session()

    existing = session.query(ZaraProduct).filter(
        ZaraProduct.url == url).first()
    if existing:
        session.close()
        return False, "This product is already in tracking list!", None

    scraper = ZaraScraper()
    result = scraper.get_stock_status(url)

    if not result:
        session.close()
        return False, "Could not get product info. Check the URL.", None

    if desired_size:
        size_exists = any(s.size.upper() == desired_size.upper()
                          for s in result.sizes)
        if not size_exists:
            available_sizes = [s.size for s in result.sizes]
            session.close()
            return False, f"'{desired_size}' size not available! Available sizes: {', '.join(available_sizes)}", None

    new_product = ZaraProduct(
        url=url,
        product_name=result.name,
        product_id=result.product_id,
        price=result.price,
        old_price=result.old_price,
        discount=result.discount,
        color=result.color,
        image_url=result.image_url,
        desired_size=desired_size.upper() if desired_size else None,
        last_check=datetime.now()
    )
    session.add(new_product)
    session.flush()

    for size in result.sizes:
        stock_status = ZaraStockStatus(
            zara_product_id=new_product.id,
            size=size.size,
            in_stock=1 if size.in_stock else 0,
            stock_status=size.stock_status,
            last_updated=datetime.now()
        )
        session.add(stock_status)

    session.commit()

    desired_in_stock = None
    if desired_size:
        for size in result.sizes:
            if size.size.upper() == desired_size.upper():
                desired_in_stock = size.in_stock
                break

    session.close()
    return True, f"'{result.name}' added to tracking list!", desired_in_stock


def delete_product(product_id: int):
    """Delete product from tracking"""
    session = get_session()
    product = session.query(ZaraProduct).filter(
        ZaraProduct.id == product_id).first()
    if product:
        session.delete(product)
        session.commit()
    session.close()


# Header with sound toggle
col_title, col_sound = st.columns([6, 1])
with col_title:
    st.title("👗 Zara Stock Tracker")
with col_sound:
    st.write("")
    if st.session_state.sound_enabled:
        if st.button("🔊", help="Turn off sound", key="sound_toggle"):
            toggle_sound()
            st.rerun()
    else:
        if st.button("🔇", help="Turn on sound", key="sound_toggle"):
            toggle_sound()
            st.rerun()

st.caption("Desired size tracking • Sound alerts • Auto-refresh every minute")

# Get product count
session_count = get_session()
total_products = session_count.query(
    ZaraProduct).filter(ZaraProduct.active == 1).count()
session_count.close()

# Main tabs
tab1, tab2 = st.tabs(["📋 Tracking List", "➕ Add Product"])

with tab1:
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    session = get_session()

    last_update = session.query(ZaraProduct).filter(
        ZaraProduct.last_check != None
    ).order_by(ZaraProduct.last_check.desc()).first()

    with col1:
        if last_update and last_update.last_check:
            st.caption(
                f"🕐 Last update: {last_update.last_check.strftime('%H:%M:%S')}")
        else:
            st.caption("🕐 No updates yet")

    with col2:
        st.metric("📦 Tracking", total_products)

    with col3:
        if st.button("🔄 Update Now", type="primary", use_container_width=True):
            with st.spinner("Checking stocks..."):
                updated, changes, alerts = update_all_products()

                if alerts:
                    play_alert_sound()
                    for item in alerts:
                        st.balloons()
                        st.success(
                            f"🎉 **{item['product_name']}** - {item['size']} is IN STOCK!")

                st.success(f"✅ {updated} products updated, {changes} changes!")
                time.sleep(1)
                st.rerun()

    with col4:
        st.session_state.auto_refresh = st.checkbox(
            "⏱️ Auto", value=st.session_state.auto_refresh, help="Auto-refresh every 60 seconds")

    st.divider()

    products = session.query(ZaraProduct).filter(ZaraProduct.active == 1).all()

    if products:
        for product in products:
            stock_statuses = session.query(ZaraStockStatus).filter(
                ZaraStockStatus.zara_product_id == product.id
            ).order_by(ZaraStockStatus.size).all()

            in_stock_count = sum(1 for s in stock_statuses if s.in_stock)
            total_sizes = len(stock_statuses)

            desired_in_stock, desired_status = check_desired_size_availability(
                product, stock_statuses)

            with st.container():
                # Trigger alarm if desired size is in stock
                if product.desired_size and desired_in_stock:
                    alarm_key = f"{product.id}_{product.desired_size}"
                    if alarm_key not in st.session_state.alarm_triggered:
                        play_alert_sound()
                        st.session_state.alarm_triggered.add(alarm_key)

                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    if product.image_url:
                        st.image(product.image_url, width=120)
                    else:
                        st.write("🖼️")

                with col2:
                    st.markdown(f"### [{product.product_name}]({product.url})")

                    if product.old_price and product.old_price > product.price:
                        st.markdown(
                            f"💰 ~~₺{product.old_price:.0f}~~ → **₺{product.price:.0f}** {product.discount or ''}")
                    else:
                        st.markdown(f"💰 **₺{product.price:.0f}**")

                    if product.color:
                        st.caption(f"🎨 {product.color}")

                    if product.desired_size:
                        st.caption(
                            f"🎯 Tracking size: **{product.desired_size}**")

                    st.write("**All Sizes:**")
                    size_cols = st.columns(min(len(stock_statuses), 6))
                    for i, stock in enumerate(stock_statuses):
                        with size_cols[i % 6]:
                            is_desired = product.desired_size and stock.size.upper() == product.desired_size.upper()

                            if is_desired:
                                # Show special badge for desired size
                                if stock.in_stock:
                                    st.markdown(
                                        f'<div class="wanted-size-available">✅ {stock.size} - IN STOCK</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(
                                        f'<div class="wanted-size-unavailable">❌ {stock.size} - OUT OF STOCK</div>', unsafe_allow_html=True)
                            else:
                                # Normal display for other sizes
                                if stock.in_stock:
                                    if stock.stock_status == "low_on_stock":
                                        st.warning(f"⚠️ {stock.size}")
                                    else:
                                        st.success(f"✅ {stock.size}")
                                else:
                                    st.error(f"❌ {stock.size}")

                    if product.last_check:
                        st.caption(
                            f"🕐 Last check: {product.last_check.strftime('%d.%m.%Y %H:%M:%S')}")

                with col3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"del_{product.id}", help="Delete product"):
                        alarm_key = f"{product.id}_{product.desired_size}"
                        st.session_state.alarm_triggered.discard(alarm_key)
                        delete_product(product.id)
                        st.rerun()

                st.divider()
    else:
        st.info(
            "👆 No products being tracked. Add a Zara product link from 'Add Product' tab.")

    session.close()


with tab2:
    st.subheader("➕ Add New Product")
    st.write("Paste the Zara product page URL and enter the size you want to track:")

    url_input = st.text_input(
        "🔗 Zara Product URL",
        placeholder="https://www.zara.com/tr/en/product-name-p12345678.html?v1=...",
        help="URL must contain v1 parameter"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        size_input = st.text_input(
            "📏 Desired Size",
            placeholder="E.g.: S, M, L, XL, 38, 40...",
            help="Size you want to track"
        ).strip().upper()

    with col2:
        st.write("")
        st.write("")
        st.caption("💡 You'll get a sound alert when this size comes in stock!")

    st.caption(
        "💡 URL example: `https://www.zara.com/tr/en/animal-print-jacket-p09076217.html?v1=483037454`")

    if st.button("➕ Add Product", type="primary", use_container_width=True):
        if url_input:
            if "zara.com" not in url_input:
                st.error("❌ Enter a valid Zara URL!")
            elif "v1=" not in url_input:
                st.error(
                    "❌ v1 parameter not found in URL. Copy the full URL from product page.")
            elif not size_input:
                st.error("❌ Please enter the size you want to track!")
            else:
                with st.spinner("Getting product info..."):
                    success, message, desired_in_stock = add_product(
                        url_input, size_input)
                    if success:
                        st.success(f"✅ {message}")

                        if desired_in_stock:
                            st.balloons()
                            play_alert_sound()
                            st.success(
                                f"🎉 Great! {size_input} size is currently IN STOCK!")
                        else:
                            st.info(
                                f"📢 {size_input} size is currently out of stock. You'll get an alert when it's back!")

                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.warning("⚠️ Please enter a URL!")


# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    sound_status = "🔊 Sound on" if st.session_state.sound_enabled else "🔇 Sound off"
    st.caption(
        f"{sound_status} • Zara Stock Tracker v3.0 • {datetime.now().strftime('%d.%m.%Y %H:%M')}")

# Render pending alarm sound
render_alarm_sound()

# Auto-refresh
if st.session_state.auto_refresh and total_products > 0:
    time_diff = (datetime.now() - st.session_state.last_update).total_seconds()
    if time_diff >= 60:
        st.session_state.last_update = datetime.now()
        updated, changes, alerts = update_all_products()

        if alerts:
            for item in alerts:
                alarm_key = f"{item['product_id']}_{item['size']}"
                if alarm_key not in st.session_state.alarm_triggered:
                    st.session_state.alarm_triggered.add(alarm_key)
                    play_alert_sound()

        st.rerun()
    else:
        time.sleep(max(1, 60 - time_diff))
        st.rerun()
