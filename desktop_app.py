"""Zara Stock Tracker - Desktop Application Launcher"""
import webview
import subprocess
import threading
import time
import requests
import sys
import os

# Configuration
PORT = 8505
URL = f"http://localhost:{PORT}"
APP_DIR = os.path.dirname(os.path.abspath(__file__))


def is_server_running():
    """Check if Streamlit server is running"""
    try:
        response = requests.get(URL, timeout=2)
        return response.status_code == 200
    except:
        return False


def start_streamlit():
    """Start Streamlit server in background"""
    venv_python = os.path.join(APP_DIR, ".venv", "bin", "python")
    streamlit_path = os.path.join(APP_DIR, ".venv", "bin", "streamlit")
    app_path = os.path.join(APP_DIR, "app.py")

    subprocess.Popen(
        [streamlit_path, "run", app_path,
         "--server.port", str(PORT),
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=APP_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def wait_for_server(max_wait=30):
    """Wait for server to be ready"""
    for _ in range(max_wait):
        if is_server_running():
            return True
        time.sleep(1)
    return False


def main():
    # Start server if not running
    if not is_server_running():
        print("Starting Streamlit server...")
        start_streamlit()

        if not wait_for_server():
            print("Error: Could not start server")
            sys.exit(1)

    print("Opening application window...")

    # Create native window
    window = webview.create_window(
        title="Zara Stock Tracker",
        url=URL,
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )

    # Start the GUI
    webview.start()


if __name__ == "__main__":
    main()
