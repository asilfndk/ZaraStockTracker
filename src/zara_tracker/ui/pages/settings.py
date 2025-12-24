"""Settings page."""

import streamlit as st

from ...config import REGIONS
from ...db import get_db
from ...db.repository import SettingsRepository, BackupRepository


def render() -> None:
    """Render the settings page."""

    st.subheader("⚙️ Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        _render_notifications()

    with col2:
        _render_region()

    with col3:
        _render_backup()

    st.divider()
    st.markdown("**Zara Stock Tracker v6.1**")


def _render_notifications() -> None:
    """Render notification settings."""
    st.markdown("#### 🔔 Notifications")

    with get_db() as db:
        push_enabled = SettingsRepository.get(
            db, "push_notifications", "true") == "true"

    new_push = st.toggle(
        "Push Notifications (macOS)",
        value=push_enabled,
        help="Show native macOS notifications"
    )

    if new_push != push_enabled:
        with get_db() as db:
            SettingsRepository.set(
                db, "push_notifications", "true" if new_push else "false")
        st.success("✅ Saved!")

    st.markdown("---")
    st.markdown("##### 📱 Telegram")

    with get_db() as db:
        telegram_enabled = SettingsRepository.get(
            db, "telegram_enabled", "false") == "true"

    new_telegram = st.toggle(
        "Enable Telegram",
        value=telegram_enabled,
        help="Send notifications via Telegram"
    )

    if new_telegram != telegram_enabled:
        with get_db() as db:
            SettingsRepository.set(
                db, "telegram_enabled", "true" if new_telegram else "false")

    if new_telegram:
        with get_db() as db:
            bot_token = SettingsRepository.get(db, "telegram_bot_token", "")
            chat_id = SettingsRepository.get(db, "telegram_chat_id", "")

        new_token = st.text_input(
            "Bot Token", value=bot_token, type="password")
        new_chat_id = st.text_input("Chat ID", value=chat_id)

        if st.button("💾 Save Telegram", use_container_width=True):
            with get_db() as db:
                SettingsRepository.set(db, "telegram_bot_token", new_token)
                SettingsRepository.set(db, "telegram_chat_id", new_chat_id)
            st.success("✅ Saved!")


def _render_region() -> None:
    """Render region settings."""
    st.markdown("#### 🌍 Region")

    with get_db() as db:
        current_country = SettingsRepository.get(db, "country_code", "tr")

    region_options = {
        code: f"{r.flag} {r.name}" for code, r in REGIONS.items()}

    selected = st.selectbox(
        "Country",
        options=list(region_options.keys()),
        format_func=lambda x: region_options[x],
        index=list(region_options.keys()).index(
            current_country) if current_country in region_options else 0
    )

    if selected != current_country:
        with get_db() as db:
            SettingsRepository.set(db, "country_code", selected)
        st.success("✅ Region updated!")
        st.info("ℹ️ New products will use this region")


def _render_backup() -> None:
    """Render backup settings."""
    st.markdown("#### 💾 Database")

    if st.button("📦 Create Backup", use_container_width=True):
        backup_path = BackupRepository.create_backup()
        if backup_path:
            st.success("✅ Backup created!")
        else:
            st.error("❌ Backup failed")

    st.markdown("---")
    st.markdown("##### 📋 Backups")

    backups = BackupRepository.list_backups()

    if backups:
        for i, backup in enumerate(backups[:5]):
            col_name, col_restore = st.columns([3, 1])
            with col_name:
                size_mb = backup["size_bytes"] / 1024 / 1024
                st.caption(
                    f"{backup['created_at'].strftime('%Y-%m-%d %H:%M')} ({size_mb:.1f}MB)")
            with col_restore:
                if st.button("🔄", key=f"restore_{i}", help="Restore"):
                    if BackupRepository.restore(backup["path"]):
                        st.success("✅ Restored!")
                        st.rerun()
    else:
        st.caption("No backups yet")
