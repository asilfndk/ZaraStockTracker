# 👗 Zara Stock Tracker (v4.1)

Track stock availability for Zara products, get instant push notifications on macOS, and analyze price history.

## Features

- **Real-time Stock Tracking**: Checks stock status automatically.
- **Size Specific Alerts**: Get notified only when your desired size is available.
- **macOS Native Notifications**: Instant alerts on your desktop.
- **Menu Bar App**: Runs quietly in the background 24/7.
- **Price History**: Track price changes over time with charts.
- **Sound Alerts**: Optional sound notifications.

## 🚀 Quick Install (macOS)

1. **Clone or Download** this repository checking out `main` branch.
   ```bash
   git clone https://github.com/asilfndk/ZaraStok.git
   cd ZaraStok
   ```

2. **Run Installer**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Launch Apps** from your Applications folder:
   - **Zara Stock Tracker**: Dashboard to add products and view charts.
   - **Zara Tracker Menu**: Background service (looks like a 👗 icon in menu bar).

## 💻 Manual Run (Terminal)

If you prefer running from terminal:

1. **Setup Python Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt  # or: pip install streamlit sqlalchemy httpx pandas pync rumps watchdog
   ```

2. **Run Dashboard**
   ```bash
   streamlit run app.py
   ```

3. **Run Background Tracker**
   ```bash
   python menu_bar_app.py
   ```

## 🛠 Troubleshooting

- **"Operation not permitted"**: Re-run `./install.sh`, it automatically fixes permissions.
- **App doesn't open**: Try running `./install.sh` again to rebuild the apps.
- **No notifications**: Ensure "Do Not Disturb" is off and Notifications are enabled for the app.

## License

MIT License
