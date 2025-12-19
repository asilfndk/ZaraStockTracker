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
# Use direct path to pip to avoid activation issues in some shells
"$PROJECT_DIR/.venv/bin/pip" install -q --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install -q streamlit sqlalchemy httpx pandas pync rumps watchdog

echo "✓ Dependencies installed"

# Initialize database
echo "🗄️  Initializing database..."
"$PROJECT_DIR/.venv/bin/python" -c "from database import init_db; init_db()"

# Create macOS app bundles
echo "🍎 Creating macOS apps..."

# Common wrapper script content generator
# We use direct path to python in venv to avoid permission issues with 'source'
create_launcher() {
    local app_name="$1"
    local script_name="$2"
    local dest="$3"
    
    cat > "$dest" << LAUNCHER
#!/bin/bash
cd "$PROJECT_DIR"
"$PROJECT_DIR/.venv/bin/python" "$script_name"
LAUNCHER
    chmod +x "$dest"
}

# 1. Main Dashboard App
APP_NAME="Zara Stock Tracker"
APP_DIR="$HOME/Applications/$APP_NAME.app"
rm -rf "$APP_DIR" 2>/dev/null || true
mkdir -p "$APP_DIR/Contents/MacOS"

create_launcher "$APP_NAME" "desktop_app.py" "$APP_DIR/Contents/MacOS/$APP_NAME"

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
    <string>4.1</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Release quarantine (fix for "Operation not permitted")
xattr -rd com.apple.quarantine "$APP_DIR" 2>/dev/null || true


# 2. Menu Bar Background App
MENU_APP_NAME="Zara Tracker Menu"
MENU_APP_DIR="$HOME/Applications/$MENU_APP_NAME.app"
rm -rf "$MENU_APP_DIR" 2>/dev/null || true
mkdir -p "$MENU_APP_DIR/Contents/MacOS"

create_launcher "$MENU_APP_NAME" "menu_bar_app.py" "$MENU_APP_DIR/Contents/MacOS/$MENU_APP_NAME"

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
    <string>4.1</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Release quarantine
xattr -rd com.apple.quarantine "$MENU_APP_DIR" 2>/dev/null || true

echo ""
echo "✅ Installation complete!"
echo ""
echo "📍 Apps installed in your Applications folder:"
echo "   • $APP_NAME (Dashboard)"
echo "   • $MENU_APP_NAME (Menu Bar 24/7)"
echo ""
echo "🚀 To start now, type:"
echo "   open \"$APP_DIR\""
echo "   open \"$MENU_APP_DIR\""
echo ""
