# 🛍️ Zara Stock Tracker - Installation Guide

## System Requirements
- macOS 10.13 (High Sierra) or later
- Internet connection (for downloading dependencies)
- ~500MB free disk space

---

## Quick Installation (Single Command)

### 1️⃣ Copy the project folder
Transfer the entire `ZaraStok` folder to your Mac via USB, AirDrop, or any other method.

### 2️⃣ Open Terminal and navigate to the project
```bash
cd /path/to/ZaraStok
```

### 3️⃣ Run the installation script
```bash
chmod +x install.sh
./install.sh
```

**That's it!** The script will automatically:
- Install Homebrew (if not present)
- Install Python 3.11
- Create virtual environment
- Install all dependencies
- Build the macOS application
- **Install app to /Applications folder**
- Launch the app

---

## What the Install Script Does

| Step | Description |
|------|-------------|
| 1 | Check/install Rosetta 2 (for Apple Silicon) |
| 2 | Check/install Homebrew |
| 3 | Install Python 3.11 via Homebrew |
| 4 | Create `.venv` virtual environment |
| 5 | Install all Python dependencies |
| 6 | Update project configuration paths |
| 7 | Initialize SQLite database |
| 8 | Build `.app` bundle with PyInstaller |
| 9 | **Copy app to /Applications folder** |
| 10 | Create helper scripts |
| 11 | Launch the application |

---

## Opening the App

After installation, you can open the app in three ways:

### From Finder
1. Open Finder
2. Go to **Applications**
3. Double-click **Zara Stock Tracker**

### From Spotlight
1. Press `Cmd + Space`
2. Type "Zara"
3. Press Enter

### From Terminal
```bash
./start.sh
```

---

## Usage

### Menu Bar Application
The app runs in the menu bar with a 🛍️ icon.

**Features:**
- 🔄 **Check Now** - Manually check all products
- 📊 **Open Dashboard** - Open web interface
- ⏱️ **Check Interval** - Set auto-check frequency (1, 5, 15, 30 minutes)
- Automatic notifications when sizes become available

### Web Dashboard (Add/Manage Products)
```bash
./dashboard.sh
```
Opens in browser at: http://localhost:8505

**Features:**
- Add new Zara products to track
- View all tracked products
- See price history
- Configure settings

---

## Troubleshooting

### "Permission denied" error
```bash
chmod +x install.sh start.sh dashboard.sh
```

### "Command not found: brew" after installation
Close and reopen Terminal, then try again.

### App doesn't appear in menu bar
- Check System Preferences > Security & Privacy
- Allow the app to run
- Try `./run_dev.sh` to see error messages

### Build fails
Try cleaning and rebuilding:
```bash
rm -rf build dist
source .venv/bin/activate
pyinstaller ZaraStockTracker.spec --noconfirm
cp -R "dist/Zara Stock Tracker.app" /Applications/
```

---

## File Structure

```
ZaraStok/
├── install.sh          # Installation script
├── start.sh            # Launch app from Applications
├── dashboard.sh        # Launch web dashboard
├── run_dev.sh          # Run without building
├── requirements.txt    # Python dependencies
├── app.py              # Streamlit dashboard
├── menu_bar_app.py     # Menu bar application
├── ZaraStockTracker.spec  # PyInstaller config
├── src/
│   └── zara_tracker/   # Main package
└── .venv/              # Virtual environment
```

**Installed App Location:** `/Applications/Zara Stock Tracker.app`

---

## Uninstalling

```bash
# Remove app from Applications
rm -rf "/Applications/Zara Stock Tracker.app"

# Remove app data
rm -rf ~/.zara_stock_tracker

# Remove project folder (optional)
rm -rf /path/to/ZaraStok
```

---

## Support

For issues and feature requests, please use GitHub Issues.
