"""Zara Stock Tracker - Multi-brand size tracking with alerts and price history"""
import streamlit as st
import base64
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import time
from database import (
    init_db, get_session, ZaraProduct, ZaraStockStatus,
    get_setting, set_setting, add_price_history, get_price_history
)
from scraper import get_scraper_for_url, is_supported_url, get_brand_from_url, get_supported_brands
from notifications import send_notification

# Page configuration
st.set_page_config(
    page_title="Zara Stock Tracker",
    page_icon="🛍️",
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
if 'push_notifications' not in st.session_state:
    st.session_state.push_notifications = get_setting(
        "push_notifications", "true") == "true"
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = int(
        get_setting("refresh_interval", "60"))

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

    # Use region from settings
    country = get_setting("country_code", "tr")
    language = get_setting("language", "en")
    updated = 0
    changes = 0
    size_alerts = []

    for product in products:
        try:
            # Get appropriate scraper for brand
            scraper = get_scraper_for_url(product.url, country, language)
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
    import time
    from sqlalchemy.exc import OperationalError

    # Validate URL is from supported brand
    if not is_supported_url(url):
        supported = ", ".join(get_supported_brands())
        return False, f"Unsupported URL. Supported brands: {supported}", None

    session = get_session()

    existing = session.query(ZaraProduct).filter(
        ZaraProduct.url == url).first()
    if existing:
        session.close()
        return False, "This product is already in tracking list!", None

    # Use region from settings and get appropriate scraper
    country = get_setting("country_code", "tr")
    language = get_setting("language", "en")

    try:
        scraper = get_scraper_for_url(url, country, language)
        result = scraper.get_stock_status(url)
    except RuntimeError as e:
        session.close()
        return False, str(e), None
    except Exception as e:
        session.close()
        return False, f"Error fetching product: {str(e)}", None

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

    # Retry logic for database operations
    max_retries = 10
    retry_delay = 0.5

    for attempt in range(max_retries):
        try:
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

            # Record initial price history
            add_price_history(new_product.id, result.price,
                              result.old_price, result.discount)

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
            break  # Success, exit retry loop

        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                session.rollback()
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 5.0)
                continue
            else:
                session.close()
                return False, "Database is busy. Please try again.", None

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
col_header, col_sound = st.columns([6, 1])
with col_header:
    try:
        with open("icon.png", "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 15px; padding-bottom: 10px;">
                <img src="data:image/png;base64,{img_data}" width="60" style="border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h1 style="margin: 0; padding: 0; font-size: 2.5rem;">Zara Stock Tracker</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.title("🛍️ Zara Stock Tracker")

with col_sound:
    st.write("")
    st.write("")  # Add spacing to align button
    if st.session_state.sound_enabled:
        if st.button("🔊", help="Turn off sound", key="sound_toggle"):
            toggle_sound()
            st.rerun()
    else:
        if st.button("🔇", help="Turn on sound", key="sound_toggle"):
            toggle_sound()
            st.rerun()

st.caption(
    "🎯 Track your desired Zara sizes • 🔔 Sound & push alerts • ⏱️ Auto-refresh")

# Get product count
session_count = get_session()
total_products = session_count.query(
    ZaraProduct).filter(ZaraProduct.active == 1).count()
session_count.close()

# Main tabs
tab1, tab2, tab3 = st.tabs(["📋 Tracking List", "➕ Add Product", "⚙️ Settings"])

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

                    # Price history expander
                    with st.expander("📊 Price History"):
                        history = get_price_history(product.id, limit=30)
                        if history:
                            history_data = [{'Date': h.recorded_at.strftime(
                                '%m/%d'), 'Price': h.price} for h in reversed(history)]
                            df = pd.DataFrame(history_data)
                            st.line_chart(df.set_index('Date'))
                            if len(history) >= 2:
                                change = history[0].price - history[-1].price
                                if change < 0:
                                    st.success(
                                        f"💰 Price dropped ₺{abs(change):.0f}!")
                                elif change > 0:
                                    st.warning(
                                        f"📈 Price increased ₺{change:.0f}")
                        else:
                            st.info("No price history yet.")

                with col3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"del_{product.id}", help="Delete product"):
                        alarm_key = f"{product.id}_{product.desired_size}"
                        st.session_state.alarm_triggered.discard(alarm_key)
                        # Close session before delete to avoid db lock
                        session.close()
                        delete_product(product.id)
                        st.rerun()

                st.divider()
    else:
        st.info(
            "👆 No products being tracked. Add a product link from 'Add Product' tab.")

    session.close()


with tab2:
    st.subheader("➕ Add New Product")

    # Get supported brands dynamically
    supported_brands = get_supported_brands()
    brands_text = ", ".join(supported_brands)

    st.write(
        f"Paste a product URL from supported brands ({brands_text}) and enter the size:")

    url_input = st.text_input(
        "🔗 Product URL",
        placeholder="https://www.zara.com/tr/en/product-name-p12345678.html?v1=...",
        help="Paste product URL from Zara"
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
        "💡 URL example: `https://www.zara.com/tr/en/dress-p09076217.html?v1=483037454`")
    st.caption(
        f"🏪 Supported: {brands_text}")

    if st.button("➕ Add Product", type="primary", use_container_width=True):
        if url_input:
            if not is_supported_url(url_input):
                st.error(
                    f"❌ Unsupported URL! Supported brands: {brands_text}")
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


# Tab 3: Settings
with tab3:
    st.subheader("⚙️ Settings")

    # Initialize settings in session state
    if 'country_code' not in st.session_state:
        st.session_state.country_code = get_setting("country_code", "tr")
    if 'language' not in st.session_state:
        st.session_state.language = get_setting("language", "en")
    if 'telegram_enabled' not in st.session_state:
        st.session_state.telegram_enabled = get_setting(
            "telegram_enabled", "false") == "true"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🔔 Notifications")

        push_enabled = st.toggle(
            "Push Notifications (macOS)",
            value=st.session_state.push_notifications,
            help="Show native macOS notifications when sizes become available"
        )
        if push_enabled != st.session_state.push_notifications:
            st.session_state.push_notifications = push_enabled
            set_setting("push_notifications",
                        "true" if push_enabled else "false")
            st.success("✅ Setting saved!")

        sound_enabled = st.toggle(
            "Sound Alerts",
            value=st.session_state.sound_enabled,
            help="Play sound when desired sizes become available"
        )
        if sound_enabled != st.session_state.sound_enabled:
            st.session_state.sound_enabled = sound_enabled

        st.markdown("---")
        st.markdown("##### 📱 Telegram")

        telegram_enabled = st.toggle(
            "Enable Telegram",
            value=st.session_state.telegram_enabled,
            help="Send notifications via Telegram"
        )
        if telegram_enabled != st.session_state.telegram_enabled:
            st.session_state.telegram_enabled = telegram_enabled
            set_setting("telegram_enabled",
                        "true" if telegram_enabled else "false")

        if telegram_enabled:
            bot_token = st.text_input(
                "Bot Token",
                value=get_setting("telegram_bot_token", ""),
                type="password",
                help="From @BotFather"
            )
            chat_id = st.text_input(
                "Chat ID",
                value=get_setting("telegram_chat_id", ""),
                help="From @userinfobot"
            )
            if st.button("💾 Save Telegram", use_container_width=True):
                set_setting("telegram_bot_token", bot_token)
                set_setting("telegram_chat_id", chat_id)
                st.success("✅ Telegram settings saved!")

    with col2:
        st.markdown("#### ⏱️ Auto-Refresh")

        refresh_options = {30: "30 seconds", 60: "1 minute",
                           120: "2 minutes", 300: "5 minutes"}

        current = st.session_state.refresh_interval
        selected = st.selectbox(
            "Refresh Interval",
            options=list(refresh_options.keys()),
            format_func=lambda x: refresh_options[x],
            index=list(refresh_options.keys()).index(
                current) if current in refresh_options else 1
        )

        if selected != st.session_state.refresh_interval:
            st.session_state.refresh_interval = selected
            set_setting("refresh_interval", str(selected))
            st.success("✅ Interval updated!")

        auto_enabled = st.toggle(
            "Auto-Refresh Enabled",
            value=st.session_state.auto_refresh
        )
        if auto_enabled != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_enabled

        st.markdown("---")
        st.markdown("##### 🌍 Region")

        regions = {
            "tr": "🇹🇷 Turkey",
            "us": "🇺🇸 United States",
            "uk": "🇬🇧 United Kingdom",
            "de": "🇩🇪 Germany",
            "fr": "🇫🇷 France",
            "es": "🇪🇸 Spain",
            "it": "🇮🇹 Italy"
        }

        current_country = st.session_state.country_code
        selected_country = st.selectbox(
            "Country",
            options=list(regions.keys()),
            format_func=lambda x: regions[x],
            index=list(regions.keys()).index(
                current_country) if current_country in regions else 0
        )

        if selected_country != st.session_state.country_code:
            st.session_state.country_code = selected_country
            set_setting("country_code", selected_country)
            st.success("✅ Region updated!")
            st.info("ℹ️ New products will use this region")

    with col3:
        st.markdown("#### 💾 Database")

        # Import backup functions
        from database import backup_database, list_backups, restore_database, BACKUP_DIR

        if st.button("📦 Create Backup", use_container_width=True):
            backup_path = backup_database()
            if backup_path:
                st.success(f"✅ Backup created!")
            else:
                st.error("❌ Backup failed")

        st.markdown("---")
        st.markdown("##### 📋 Backups")

        backups = list_backups()
        if backups:
            for i, backup in enumerate(backups[:5]):  # Show last 5
                col_name, col_size, col_restore = st.columns([3, 1, 1])
                with col_name:
                    st.caption(backup['created_at'].strftime('%Y-%m-%d %H:%M'))
                with col_size:
                    size_mb = backup['size_bytes'] / 1024 / 1024
                    st.caption(f"{size_mb:.1f}MB")
                with col_restore:
                    if st.button("🔄", key=f"restore_{i}", help="Restore this backup"):
                        if restore_database(backup['path']):
                            st.success("✅ Restored!")
                            st.rerun()
        else:
            st.caption("No backups yet")

        st.markdown("---")
        st.caption(f"📁 Backups: `~/.zara_stock_tracker/backups/`")

    st.divider()

    # Version info with region
    region_name = regions.get(st.session_state.country_code, "Unknown")
    st.markdown(
        f"**Zara Stock Tracker v5.0** - {region_name} • Telegram • Backup")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    sound_status = "🔊 Sound on" if st.session_state.sound_enabled else "🔇 Sound off"
    push_status = "🔔 Push on" if st.session_state.push_notifications else "🔕 Push off"
    st.caption(
        f"{sound_status} • {push_status} • v5.0 • {datetime.now().strftime('%d.%m.%Y %H:%M')}")

# Render pending alarm sound
render_alarm_sound()

# Auto-refresh (non-blocking, configurable interval)
if st.session_state.auto_refresh and total_products > 0:
    time_diff = (datetime.now() - st.session_state.last_update).total_seconds()
    refresh_interval = st.session_state.refresh_interval

    if time_diff >= refresh_interval:
        st.session_state.last_update = datetime.now()
        updated, changes, alerts = update_all_products()

        if alerts:
            for item in alerts:
                alarm_key = f"{item['product_id']}_{item['size']}"
                if alarm_key not in st.session_state.alarm_triggered:
                    st.session_state.alarm_triggered.add(alarm_key)
                    play_alert_sound()
                    # Send push notification if enabled
                    if st.session_state.push_notifications:
                        send_notification(
                            title="🎉 Size Available!",
                            message=f"{item.get('product_name', 'Product')} - {item['size']} is now in stock!"
                        )

        st.rerun()
