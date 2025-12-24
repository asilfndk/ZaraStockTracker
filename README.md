# 🛍️ Zara Stock Tracker

A macOS application that monitors **Zara** product stock in real-time with size-specific tracking and instant notifications.

![Version](https://img.shields.io/badge/version-6.1-purple)
![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.11-green)

## ✨ Features

- 🎯 **Size Tracking** - Monitor specific sizes and get alerted when they're back in stock
- 📊 **Price History** - Track price changes over time
- 🔔 **Smart Notifications** - macOS native push notifications
- 🖥️ **Menu Bar App** - Runs 24/7 in the background
- 📱 **Native Dashboard** - Standalone window, no browser required
- 🌍 **Multi-Region** - Support for 7 countries (TR, US, UK, DE, FR, ES, IT)
- 💾 **Auto Backup** - Database backup with automatic retention
- 📦 **Portable** - Single `.app` bundle works on any Mac

## 🚀 Quick Start

### Option 1: Download Pre-built App

Download `Zara Stock Tracker.app` from Releases and move to Applications folder.

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/asilfndk/ZaraStok.git
cd ZaraStok

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run the menu bar app
python menu_bar_app.py
```

## 🖥️ Usage

### Menu Bar App

The menu bar app runs in the background and monitors stock 24/7.

```bash
python menu_bar_app.py
```

**Menu Options:**
- 🔄 Check Now - Manual stock check
- 📊 Open Dashboard - Opens native dashboard window
- ⏱️ Check Interval - Set monitoring frequency
- ❌ Quit - Stop the app

### Native Dashboard

The dashboard opens as a standalone macOS window with:
- Product list with stock status
- Add/Delete products
- Manual stock refresh
- Real-time notifications

### Streamlit Dashboard (Optional)

For advanced features like price history charts:

```bash
streamlit run app.py
```

## 📦 Build Standalone App

```bash
# Build .app bundle
pyinstaller ZaraStockTracker.spec --clean

# Copy to Applications
cp -R "dist/Zara Stock Tracker.app" /Applications/
```

## 📁 Project Structure

```
ZaraStok/
├── app.py                    # Streamlit entry
├── menu_bar_app.py           # Menu bar entry
├── src/
│   └── zara_tracker/
│       ├── config.py         # Configuration
│       ├── models/           # Data models
│       ├── db/               # Database layer
│       ├── scraper/          # Web scraping
│       ├── services/         # Business logic
│       └── ui/
│           ├── native_dashboard.py  # Native macOS window
│           └── pages/               # Streamlit pages
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

### v6.1 (Latest)
- **Native Dashboard** - Standalone macOS window using PyObjC/Cocoa
- **Streamlit-free** - App works without browser or Streamlit
- **Full Portability** - Single `.app` runs on any Mac
- Menu bar app improvements

### v6.0
- Complete architecture rebuild
- Context manager pattern for database sessions
- Modular service layer
- Improved error handling

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ for fashion shoppers
