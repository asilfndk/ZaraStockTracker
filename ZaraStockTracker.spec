# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Zara Stock Tracker macOS App"""

import os
import sys
from pathlib import Path

# Get the directory containing this spec file
SPEC_DIR = Path(SPECPATH)

block_cipher = None

# Collect all source files
a = Analysis(
    ['menu_bar_app.py'],
    pathex=[str(SPEC_DIR), str(SPEC_DIR / 'src')],
    binaries=[],
    datas=[
        ('src/zara_tracker', 'zara_tracker'),
        ('icon.png', '.'),
        ('icon.icns', '.'),
    ],
    hiddenimports=[
        'rumps',
        'AppKit',
        'Foundation',
        'objc',
        'PyObjCTools',
        'sqlalchemy',
        'sqlalchemy.orm',
        'sqlalchemy.engine',
        'requests',
        'zara_tracker',
        'zara_tracker.config',
        'zara_tracker.models',
        'zara_tracker.models.product',
        'zara_tracker.models.settings',
        'zara_tracker.db',
        'zara_tracker.db.engine',
        'zara_tracker.db.tables',
        'zara_tracker.db.repository',
        'zara_tracker.scraper',
        'zara_tracker.scraper.zara',
        'zara_tracker.scraper.cache',
        'zara_tracker.services',
        'zara_tracker.services.product_service',
        'zara_tracker.services.stock_service',
        'zara_tracker.services.notification_service',
        'zara_tracker.ui',
        'zara_tracker.ui.native_dashboard',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'streamlit',
        'pandas',
        'matplotlib',
        'numpy',
        'PIL',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Zara Stock Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Zara Stock Tracker',
)

app = BUNDLE(
    coll,
    name='Zara Stock Tracker.app',
    icon='icon.icns',
    bundle_identifier='com.zarastocktracker.app',
    info_plist={
        'CFBundleName': 'Zara Stock Tracker',
        'CFBundleDisplayName': 'Zara Stock Tracker',
        'CFBundleExecutable': 'Zara Stock Tracker',
        'CFBundleIdentifier': 'com.zarastocktracker.app',
        'CFBundleVersion': '6.0.0',
        'CFBundleShortVersionString': '6.0',
        'LSMinimumSystemVersion': '10.13.0',
        'LSUIElement': True,  # Hide from Dock, menu bar app only
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': 'Zara Stock Tracker needs to send notifications.',
        'LSBackgroundOnly': False,
    },
)
