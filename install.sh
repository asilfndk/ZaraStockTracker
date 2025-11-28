#!/bin/bash
# Zara Stock Tracker - Installer for macOS
# This script installs the Zara Stock Tracker application

echo "🛍️ Zara Stock Tracker Installer"
echo "================================"
echo ""

# Check if Python 3.12+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.12 or later from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION found"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "✅ uv package manager ready"

# Set installation directory
INSTALL_DIR="$HOME/ZaraStockTracker"
APP_NAME="Zara Stock Tracker"

echo ""
echo "📁 Installing to: $INSTALL_DIR"

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Copy application files
cp -r app.py database.py zara_scraper.py desktop_app.py pyproject.toml "$INSTALL_DIR/"

cd "$INSTALL_DIR"

# Create virtual environment and install dependencies
echo "📦 Installing dependencies..."
uv venv
source .venv/bin/activate
uv pip install streamlit pandas sqlalchemy requests pywebview

echo "✅ Dependencies installed"

# Create macOS Application Bundle
APP_PATH="$HOME/Applications/$APP_NAME.app"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Create launcher script
cat > "$APP_PATH/Contents/MacOS/$APP_NAME" << LAUNCHER
#!/bin/bash
cd "$INSTALL_DIR"
source .venv/bin/activate
python desktop_app.py
LAUNCHER

chmod +x "$APP_PATH/Contents/MacOS/$APP_NAME"

# Create Info.plist
cat > "$APP_PATH/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.zarastocktracker.app</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>3.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 You can now:"
echo "   1. Open '$APP_NAME' from ~/Applications"
echo "   2. Or run: open \"$APP_PATH\""
echo "   3. Add to Dock by dragging from Applications folder"
echo ""
echo "Enjoy tracking Zara stocks! 👗"
