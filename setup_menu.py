from setuptools import setup

APP = ['menu_bar_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': '',  # İsterseniz bir .icns dosyası eklenebilir, şimdilik varsayılan
    'plist': {
        'CFBundleName': 'Zara Tracker Menu',
        'CFBundleDisplayName': 'Zara Tracker Menu',
        'CFBundleVersion': '4.1',
        'CFBundleIdentifier': 'com.zara.stock-tracker-menu',
        'LSUIElement': True,  # Menu bar app olduğu için dock'ta görünmez
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps', 'httpx', 'sqlalchemy', 'pandas', 'watchdog'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
