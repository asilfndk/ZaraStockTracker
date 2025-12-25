# 🛍️ Zara Stock Tracker

A macOS application that monitors **Zara** product stock in real-time with size-specific tracking and instant notifications.

![Version](https://img.shields.io/badge/version-6.2-purple)
![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.11-green)

## ✨ Features

- 🎯 **Size Tracking** - Monitor specific sizes and get alerted when they're back in stock
- 📊 **Price History** - Track price changes over time
- 🔔 **Smart Notifications** - macOS native push notifications
- 🖥️ **Menu Bar App** - Runs 24/7 in the background
- 🌐 **Web Dashboard** - Streamlit-based interface for product management
- 🌍 **Multi-Region** - Support for 7 countries (TR, US, UK, DE, FR, ES, IT)
- 💾 **Auto Backup** - Database backup with automatic retention
- 📦 **Easy Install** - Single script installs everything

## 🚀 Quick Start

### New Mac Installation

```bash
# 1. Copy ZaraStok folder to your Mac

# 2. Open Terminal and navigate to the folder
cd /path/to/ZaraStok

# 3. Run the installation script
chmod +x install.sh
./install.sh
```

The script will automatically:
- Install Homebrew & Python 3.11
- Set up virtual environment
- Install all dependencies
- Build the macOS application
- Install app to `/Applications` folder
- Launch the app

**See [INSTALL.md](INSTALL.md) for detailed instructions.**

### After Installation

Open the app from:
- **Finder** → Applications → Zara Stock Tracker
- **Spotlight** → Cmd+Space → "Zara"
- **Terminal** → `./start.sh`

## 🖥️ Usage

### Menu Bar App

The menu bar app runs in the background with a 🛍️ icon.

**Menu Options:**
- 🔄 **Check Now** - Manual stock check
- 📊 **Open Dashboard** - Opens web dashboard
- ⏱️ **Check Interval** - Set monitoring frequency (1, 5, 15, 30 min)
- ❌ **Quit** - Stop the app

### Web Dashboard

Add and manage products through the web interface:

```bash
./dashboard.sh
```

Opens at: http://localhost:8505

**Features:**
- Add new Zara products to track
- View all tracked products with stock status
- See price history charts
- Configure settings

## 📁 Project Structure

```
ZaraStok/
├── install.sh            # One-click installer
├── start.sh              # Launch app
├── dashboard.sh          # Launch web dashboard
├── app.py                # Streamlit entry
├── menu_bar_app.py       # Menu bar entry
├── requirements.txt      # Python dependencies
├── INSTALL.md            # Installation guide
├── src/
│   └── zara_tracker/
│       ├── config.py     # Configuration
│       ├── models/       # Data models
│       ├── db/           # Database layer
│       ├── scraper/      # Web scraping
│       ├── services/     # Business logic
│       └── ui/           # UI components
└── tests/                # Unit tests
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

### v6.2 (Latest)
- **Easy Installer** - Single `./install.sh` script for new Mac setup
- **Auto Applications Install** - App automatically installed to /Applications
- **Helper Scripts** - `start.sh`, `dashboard.sh` for easy access
- Improved documentation

### v6.1
- Native Dashboard - Standalone macOS window using PyObjC/Cocoa
- Streamlit-free option
- Full Portability

### v6.0
- Complete architecture rebuild
- Context manager pattern for database sessions
- Modular service layer

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ for fashion shoppers
