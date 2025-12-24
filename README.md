# 🛍️ Zara Stock Tracker

A macOS application that monitors **Zara** product stock in real-time with size-specific tracking and instant notifications.

![Version](https://img.shields.io/badge/version-5.1-purple)
![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)

## ✨ Features

- 🎯 **Size Tracking** - Monitor specific sizes and get alerted when they're back in stock
- 📊 **Price History** - Track price changes over time with charts
- 🔔 **Smart Notifications** - macOS native + optional Telegram alerts
- 🖥️ **Menu Bar App** - Runs 24/7 in the background
- 🌍 **Multi-Region** - Support for 7 countries (TR, US, UK, DE, FR, ES, IT)
- 💾 **Auto Backup** - Database backup with automatic retention
- ⚡ **Smart Caching** - TTL cache to reduce API calls

## 🚀 Quick Start

### Prerequisites

- macOS 10.13+
- Python 3.9+

### Installation

```bash
# Clone the repository
git clone https://github.com/asilfndk/ZaraStok.git
cd ZaraStok

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run the dashboard
streamlit run app.py
```

## 🖥️ Menu Bar App

The menu bar app runs in the background and monitors stock 24/7.

```bash
# Run from source
python menu_bar_app.py

# Or build standalone app
pip install pyinstaller
pyinstaller ZaraStockTracker.spec --noconfirm

# App location: dist/Zara Stock Tracker.app
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

| Setting | Default | Description |
|---------|---------|-------------|
| `ZARA_COUNTRY` | `tr` | Country code (tr, us, uk, de, fr, es, it) |
| `ZARA_LANGUAGE` | `en` | Language code |
| `ZARA_CHECK_INTERVAL` | `300` | Check interval in seconds |
| `ZARA_TELEGRAM_ENABLED` | `false` | Enable Telegram notifications |

### UI Settings

All settings can be configured from the **Settings** tab:
- 🌍 **Region** - Select country
- 📱 **Telegram** - Configure notifications
- 💾 **Backup** - Database backup/restore

## 📁 Project Structure

```
ZaraStok/
├── app.py                    # Streamlit dashboard
├── menu_bar_app.py           # macOS menu bar app
├── scraper.py                # Scraper router
├── zara_scraper.py           # Zara API scraper
├── database.py               # SQLite + backup
├── notifications.py          # macOS + Telegram
├── config.py                 # Configuration
├── cache.py                  # TTL cache
├── ZaraStockTracker.spec     # PyInstaller config
└── icon.icns                 # App icon
```

## 🌍 Supported Regions

| Code | Country |
|------|---------|
| `tr` | 🇹🇷 Turkey |
| `us` | 🇺🇸 United States |
| `uk` | 🇬🇧 United Kingdom |
| `de` | 🇩🇪 Germany |
| `fr` | 🇫🇷 France |
| `es` | 🇪🇸 Spain |
| `it` | 🇮🇹 Italy |

## 📜 Changelog

### v5.1 (Latest)
- Simplified to Zara-only support
- Improved stability and performance
- Multi-region support
- Telegram notifications
- Database backup

### v5.0
- Multi-brand support
- Menu bar app improvements

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ for fashion shoppers
