# 👗 Zara Stock Tracker v4.0

Track Zara product sizes and get notified when they're back in stock!

![Version](https://img.shields.io/badge/version-4.0-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.9+-green)

## ✨ Features

- 📦 **Product Tracking** - Track multiple Zara products and sizes
- 🔔 **Instant Notifications** - Get macOS push notifications when sizes are available
- 📊 **Price History** - Track price changes over time with charts
- ⏱️ **Auto-Refresh** - Customizable refresh intervals (30s - 5min)
- 🔊 **Sound Alerts** - Audio notifications for stock availability
- 👗 **Menu Bar App** - 24/7 background monitoring from menu bar

## 🚀 Quick Install (macOS)

```bash
# Clone the repository
git clone https://github.com/asilfndk/ZaraStok.git
cd ZaraStok

# Run the installer
./install.sh
```

The installer will:
- Create a Python virtual environment
- Install all dependencies
- Create two macOS apps in `~/Applications/`:
  - **Zara Stock Tracker** - Full dashboard app
  - **Zara Tracker Menu** - Menu bar background tracker (24/7)

## 📱 Usage

### Menu Bar App (24/7 Tracking)
1. Open **"Zara Tracker Menu"** from Applications
2. Look for 👗 icon in menu bar
3. Click for options:
   - 🔄 Check Now
   - 📊 Open Dashboard
   - ⏱️ Set check interval
   - ❌ Quit

### Dashboard App
1. Open **"Zara Stock Tracker"** from Applications
2. Add products via the "Add Product" tab
3. Configure notifications in "Settings" tab

## 📋 Adding Products

1. Go to any Zara product page
2. Select a color/variant (URL should contain `v1=`)
3. Copy the full URL
4. Paste in the app and set your desired size

## 🛠️ Requirements

- macOS 10.14+
- Python 3.9+
- Internet connection

## 📁 Project Structure

```
ZaraStok/
├── app.py              # Main Streamlit app
├── menu_bar_app.py     # Menu bar background app
├── desktop_app.py      # Desktop wrapper (pywebview)
├── database.py         # SQLAlchemy models
├── zara_scraper.py     # Zara API scraper
├── notifications.py    # macOS notifications
├── cache.py            # Caching utilities
├── exceptions.py       # Custom exceptions
├── install.sh          # macOS installer
└── tests/              # Unit tests
```

## 🔧 Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install streamlit pywebview sqlalchemy httpx pandas pync rumps

# Run the app
streamlit run app.py

# Or run menu bar app
python menu_bar_app.py
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

Made with ❤️ for Zara shoppers
