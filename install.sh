#!/bin/bash
# Zara Stock Tracker - Installation Script for macOS
# This script sets up the project, installs dependencies, builds the app

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🛍️  Zara Stock Tracker - Installation Script"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Detect architecture
ARCH=$(uname -m)
echo "📍 System Information:"
echo "   Architecture: $ARCH"
echo "   macOS: $(sw_vers -productVersion)"
echo "   Project: $SCRIPT_DIR"
echo ""

# ============================================================
# Step 1: Install Rosetta 2 (if needed on Apple Silicon)
# ============================================================
if [[ "$ARCH" == "arm64" ]]; then
    echo "⚠️  Apple Silicon detected. Checking Rosetta 2..."
    if /usr/bin/pgrep oahd >/dev/null 2>&1; then
        echo "   ✓ Rosetta 2 is already installed"
    else
        echo "   Installing Rosetta 2..."
        softwareupdate --install-rosetta --agree-to-license
        echo "   ✓ Rosetta 2 installed"
    fi
fi

# ============================================================
# Step 2: Check/Install Homebrew
# ============================================================
echo ""
echo "📦 Step 1: Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "   Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to PATH for this session
    if [[ "$ARCH" == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    echo "   ✓ Homebrew installed"
else
    echo "   ✓ Homebrew found: $(brew --version | head -1)"
fi

# ============================================================
# Step 3: Install Python 3.11
# ============================================================
echo ""
echo "🐍 Step 2: Setting up Python 3.11..."
if ! brew list python@3.11 &> /dev/null; then
    echo "   Installing Python 3.11 via Homebrew..."
    brew install python@3.11
    echo "   ✓ Python 3.11 installed"
else
    echo "   ✓ Python 3.11 already installed"
fi

# Get Python 3.11 path
if [[ "$ARCH" == "arm64" ]]; then
    PYTHON_PATH="/opt/homebrew/bin/python3.11"
else
    PYTHON_PATH="/usr/local/bin/python3.11"
fi

if [[ ! -f "$PYTHON_PATH" ]]; then
    PYTHON_PATH=$(brew --prefix python@3.11)/bin/python3.11
fi

echo "   Python path: $PYTHON_PATH"
echo "   Version: $($PYTHON_PATH --version)"

# ============================================================
# Step 4: Create Virtual Environment
# ============================================================
echo ""
echo "📁 Step 3: Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "   Removing old .venv..."
    rm -rf .venv
fi

$PYTHON_PATH -m venv .venv
source .venv/bin/activate
echo "   ✓ Virtual environment created and activated"
echo "   Python: $(python --version)"

# ============================================================
# Step 5: Upgrade pip and Install Dependencies
# ============================================================
echo ""
echo "📥 Step 4: Installing dependencies..."
pip install --upgrade pip setuptools wheel -q

echo "   Installing core packages..."
pip install requests sqlalchemy rumps -q

echo "   Installing PyObjC (macOS integration)..."
pip install pyobjc-core pyobjc-framework-Cocoa -q

echo "   Installing Streamlit (web dashboard)..."
pip install streamlit -q

echo "   Installing PyInstaller (app builder)..."
pip install pyinstaller -q

echo "   ✓ All dependencies installed"

# ============================================================
# Step 6: Save Project Path Configuration
# ============================================================
echo ""
echo "⚙️  Step 5: Configuring project paths..."

# Create config directory if not exists
mkdir -p ~/.zara_stock_tracker

# Save project path for the app to find
echo "$SCRIPT_DIR" > ~/.zara_stock_tracker/project_path.txt
echo "   ✓ Project path saved to ~/.zara_stock_tracker/project_path.txt"

# ============================================================
# Step 7: Initialize Database
# ============================================================
echo ""
echo "🗄️  Step 6: Initializing database..."
python -c "
import sys
sys.path.insert(0, 'src')
from zara_tracker.db import init_db
init_db()
print('   ✓ Database initialized')
"

# ============================================================
# Step 8: Build macOS Application
# ============================================================
echo ""
echo "🔨 Step 7: Building macOS application..."
echo "   This may take a few minutes..."

pyinstaller ZaraStockTracker.spec --noconfirm 2>&1 | grep -E "(INFO: Build complete|ERROR|WARNING:.*failed)" || true

if [ -d "dist/Zara Stock Tracker.app" ]; then
    echo "   ✓ Application built successfully!"
    APP_PATH="$SCRIPT_DIR/dist/Zara Stock Tracker.app"
else
    echo "   ❌ Build failed. Check errors above."
    exit 1
fi

# ============================================================
# Step 9: Copy App to Applications
# ============================================================
echo ""
echo "📦 Step 8: Installing to Applications folder..."

# Remove old version if exists
if [ -d "/Applications/Zara Stock Tracker.app" ]; then
    echo "   Removing old version..."
    rm -rf "/Applications/Zara Stock Tracker.app"
fi

# Copy new version
cp -R "dist/Zara Stock Tracker.app" "/Applications/"
echo "   ✓ App installed to /Applications"

INSTALLED_APP="/Applications/Zara Stock Tracker.app"

# ============================================================
# Step 10: Create Helper Scripts
# ============================================================
echo ""
echo "📝 Step 9: Creating helper scripts..."

# Start script
cat > start.sh << 'SCRIPT'
#!/bin/bash
open "/Applications/Zara Stock Tracker.app"
SCRIPT
chmod +x start.sh

# Dashboard script
cat > dashboard.sh << 'SCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
streamlit run app.py --server.port 8505
SCRIPT
chmod +x dashboard.sh

# Dev run script (without build)
cat > run_dev.sh << 'SCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python menu_bar_app.py
SCRIPT
chmod +x run_dev.sh

echo "   ✓ Helper scripts created"

# ============================================================
# Step 11: Launch Application
# ============================================================
echo ""
echo "🚀 Step 10: Launching application..."
open "$INSTALLED_APP"

# ============================================================
# Complete!
# ============================================================
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ INSTALLATION COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "The application is now running in your menu bar (🛍️ icon)."
echo ""
echo "📍 App installed to: /Applications/Zara Stock Tracker.app"
echo ""
echo "To open the app:"
echo "  • From Finder: Go to Applications → Zara Stock Tracker"
echo "  • From Terminal: ./start.sh"
echo "  • From Spotlight: Cmd+Space → type 'Zara'"
echo ""
echo "To add products (web dashboard):"
echo "  ./dashboard.sh"
echo ""
echo "Note: On first run, macOS may ask for permissions."
echo "      Go to System Preferences > Security & Privacy to allow."
echo ""
