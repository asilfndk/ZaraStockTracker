# 🛍️ Zara Stock Tracker

A macOS application that monitors **Zara** product stock in real-time with size-specific tracking and instant notifications.

![Version](https://img.shields.io/badge/version-6.0-purple)
![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.11-green)

## ✨ Features

- 🎯 **Size Tracking** - Monitor specific sizes and get alerted when they're back in stock
- 📊 **Price History** - Track price changes over time
- 🔔 **Smart Notifications** - macOS native + optional Telegram alerts
- 🖥️ **Menu Bar App** - Runs 24/7 in the background
- 🌍 **Multi-Region** - Support for 7 countries (TR, US, UK, DE, FR, ES, IT)
- 💾 **Auto Backup** - Database backup with automatic retention
- ⚡ **Clean Architecture** - Modular, testable, maintainable code

## 🚀 Quick Start

### Prerequisites

- macOS 10.13+
- Python 3.11+

### Installation

```bash
# Clone the repository
git clone https://github.com/asilfndk/ZaraStok.git
cd ZaraStok

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run the dashboard
streamlit run app.py
```

## 🖥️ Menu Bar App

The menu bar app runs in the background and monitors stock 24/7.

```bash
python menu_bar_app.py
```

## 📁 Project Structure

```
ZaraStok/
├── app.py                    # Streamlit entry (~40 lines)
├── menu_bar_app.py           # Menu bar entry
├── src/
│   └── zara_tracker/
│       ├── config.py         # Configuration
│       ├── models/           # Data models
│       ├── db/               # Database layer
│       │   ├── engine.py     # Connection management
│       │   ├── tables.py     # SQLAlchemy models
│       │   └── repository.py # CRUD operations
│       ├── scraper/          # Web scraping
│       │   ├── zara.py       # Zara API scraper
│       │   └── cache.py      # Response cache
│       ├── services/         # Business logic
│       │   ├── product_service.py
│       │   ├── stock_service.py
│       │   └── notification_service.py
│       └── ui/               # Streamlit components
│           ├── components.py # Reusable UI
│           └── pages/        # Page modules
└── tests/                    # Unit tests
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

### v6.0 (Latest)
- Complete clean architecture rebuild
- Context manager pattern for database sessions
- Modular service layer
- Minimal entry points
- Improved error handling

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ for fashion shoppers
