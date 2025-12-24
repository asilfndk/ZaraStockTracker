# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Zara Stock Tracker Menu Bar App

Build command:
    .venv/bin/pyinstaller ZaraStockTracker.spec
"""

block_cipher = None

a = Analysis(
    ['menu_bar_app.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.png', '.')],
    hiddenimports=[
        'database',
        'zara_scraper',
        'notifications',
        'cache',
        'config',
        'exceptions',
        'rumps',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.ext.declarative',
        'httpx',
        'requests',
        'certifi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'streamlit',
        'pandas',
        'numpy',
        'matplotlib',
        'PIL',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
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
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
    bundle_identifier='com.zarastock.menubar',
    info_plist={
        'CFBundleName': 'Zara Stock Tracker',
        'CFBundleDisplayName': 'Zara Stock Tracker',
        'CFBundleVersion': '5.0.0',
        'CFBundleShortVersionString': '5.0.0',
        'LSUIElement': True,  # Hide from Dock (menu bar only)
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
)
