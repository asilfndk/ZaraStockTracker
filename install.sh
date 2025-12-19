#!/bin/bash
# Zara Stock Tracker - Quick Install Script
# Run this on any Mac to set up the app

set -e

echo "🛍️  Zara Stock Tracker - Installation"
echo "======================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3 first:"
    echo "   brew install python3"
    exit 1
fi

echo "✓ Python 3 found"

# Go to script directory
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install dependencies
echo "📥 Installing dependencies..."
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q streamlit pywebview sqlalchemy httpx pandas pync rumps

echo "✓ Dependencies installed"

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from database import init_db; init_db()"

# Create macOS app bundles
echo "🍎 Creating macOS apps..."

# 1. Main Dashboard App
APP_NAME="Zara Stock Tracker"
APP_DIR="$HOME/Applications/$APP_NAME.app"
rm -rf "$APP_DIR" 2>/dev/null || true
mkdir -p "$APP_DIR/Contents/MacOS"

# Create launcher that runs from project directory
cat > "$APP_DIR/Contents/MacOS/$APP_NAME" << LAUNCHER
#!/bin/bash
cd "$PROJECT_DIR"
source .venv/bin/activate
python desktop_app.py
LAUNCHER
chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"

cat > "$APP_DIR/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Zara Stock Tracker</string>
    <key>CFBundleExecutable</key>
    <string>Zara Stock Tracker</string>
    <key>CFBundleIdentifier</key>
    <string>com.zara.stock-tracker</string>
    <key>CFBundleVersion</key>
    <string>4.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# 2. Menu Bar Background App
MENU_APP_NAME="Zara Tracker Menu"
MENU_APP_DIR="$HOME/Applications/$MENU_APP_NAME.app"
rm -rf "$MENU_APP_DIR" 2>/dev/null || true
mkdir -p "$MENU_APP_DIR/Contents/MacOS"

cat > "$MENU_APP_DIR/Contents/MacOS/$MENU_APP_NAME" << LAUNCHER
#!/bin/bash
cd "$PROJECT_DIR"
source .venv/bin/activate
python menu_bar_app.py
LAUNCHER
chmod +x "$MENU_APP_DIR/Contents/MacOS/$MENU_APP_NAME"

cat > "$MENU_APP_DIR/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Zara Tracker Menu</string>
    <key>CFBundleExecutable</key>
    <string>Zara Tracker Menu</string>
    <key>CFBundleIdentifier</key>
    <string>com.zara.stock-tracker-menu</string>
    <key>CFBundleVersion</key>
    <string>4.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

echo ""
echo "✅ Installation complete!"
echo ""
echo "📍 Apps installed:"
echo "   • $APP_DIR (Full Dashboard)"
echo "   • $MENU_APP_DIR (Menu Bar 24/7 Tracker)"
echo ""
echo "To use:"
echo "  1. 'Zara Stock Tracker' - Full dashboard app"
echo "  2. 'Zara Tracker Menu' - Menu bar background tracker (24/7)"
echo ""
echo "The menu bar app runs in background with a 👗 icon!"
echo ""

# Ask to launch
read -p "🚀 Launch the menu bar app now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "$MENU_APP_DIR"
fi
