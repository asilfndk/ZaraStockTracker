# 👗 Zara Stock Tracker

A native macOS desktop application that monitors Zara product stock availability and alerts you when your desired size becomes available.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-red.svg)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 🔍 **Real-time Stock Monitoring** - Track multiple Zara products simultaneously
- 🎯 **Size-specific Tracking** - Monitor only the size you want (S, M, L, XL, 38, 40, etc.)
- 🔔 **Sound Alerts** - Get notified with audio alerts when your size comes back in stock
- 🔄 **Auto-refresh** - Automatic stock checks every 60 seconds
- 💰 **Price Tracking** - See current prices, discounts, and price drops
- 🖥️ **Native Desktop App** - Runs as a standalone macOS application
- 🎨 **Clean UI** - Modern, intuitive interface with visual stock indicators

## 📸 Screenshots

| Tracking List | Add Product |
|---------------|-------------|
| View all tracked products with stock status | Add new products by URL |

## 🚀 Quick Start

### Prerequisites

- macOS 10.13 or later
- Internet connection

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/asilfndk/ZaraStockTracker.git
   cd ZaraStockTracker
   ```

2. **Run the installer**
   ```bash
   # If you get "damaged" error, run this first:
   xattr -d com.apple.quarantine install.sh
   
   # Then run the installer
   ./install.sh
   ```

3. **Launch the app**
   - Open "Zara Stock Tracker" from your Applications folder
   - Or run: `open ~/Applications/Zara\ Stock\ Tracker.app`

### Manual Installation

If you prefer manual setup:

```bash
# Install uv package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install streamlit pandas sqlalchemy requests pywebview

# Run the app
python desktop_app.py
```

## 📖 Usage

### Adding a Product

1. Go to the **"Add Product"** tab
2. Copy a Zara product URL from the website
   - URL must contain the `v1=` parameter (color variant ID)
   - Example: `https://www.zara.com/tr/en/jacket-p09876543.html?v1=123456789`
3. Enter the size you want to track (e.g., `M`, `L`, `42`)
4. Click **"Add Product"**

### Tracking

- Products are automatically checked every 60 seconds
- **Green badge**: Size is IN STOCK ✅
- **Red badge**: Size is OUT OF STOCK ❌
- **Yellow warning**: Low stock ⚠️

### Sound Alerts

- Click the 🔇 button in the header to enable sound alerts
- When enabled (🔊), you'll hear an alert when your desired size becomes available
- Sound must be enabled by clicking the button (browser security requirement)

## 🏗️ Project Structure

```
ZaraStok/
├── app.py              # Main Streamlit application
├── database.py         # SQLAlchemy database models
├── zara_scraper.py     # Zara API integration
├── desktop_app.py      # Native window launcher (pywebview)
├── install.sh          # macOS installer script
├── pyproject.toml      # Project dependencies
└── README.md           # This file
```

## 🔧 Technical Details

### Stack

- **Frontend**: Streamlit with custom CSS
- **Backend**: Python 3.12+
- **Database**: SQLite with SQLAlchemy ORM
- **Desktop**: pywebview for native window
- **API**: Zara's internal product API

### How It Works

1. Extracts the `v1` parameter (color ID) from the Zara URL
2. Calls Zara's product details API: `https://www.zara.com/tr/en/products-details?productIds={colorId}`
3. Parses size availability from the JSON response
4. Stores and tracks changes in SQLite database
5. Triggers alerts when desired size status changes to "in_stock"

## 🗑️ Uninstall

```bash
# Remove application
rm -rf ~/ZaraStockTracker
rm -rf ~/Applications/Zara\ Stock\ Tracker.app

# Remove cloned repository (if desired)
rm -rf /path/to/ZaraStok
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This project is for personal use only. It is not affiliated with, endorsed by, or connected to Zara or Inditex in any way. Use responsibly and respect Zara's terms of service.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [pywebview](https://pywebview.flowrl.com/) for native window support
- [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM

---

Made with ❤️ for Zara shoppers who hate missing out on their size!
