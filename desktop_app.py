"""Zara Stock Tracker - Desktop Application Launcher with improved reliability"""
import subprocess
import time
import sys
import os
import atexit
import signal
import socket

# Configuration
PORT = 8505
URL = f"http://localhost:{PORT}"
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Global reference to streamlit process
streamlit_process = None


def is_port_open(port: int, host: str = "localhost") -> bool:
    """Check if a port is open using socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def find_python_executable() -> str:
    """Find the Python executable to use"""
    # Try virtual environment first
    venv_python = os.path.join(APP_DIR, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python

    # Fall back to current Python
    return sys.executable


def find_streamlit_executable() -> str:
    """Find the Streamlit executable to use"""
    # Try virtual environment first
    venv_streamlit = os.path.join(APP_DIR, ".venv", "bin", "streamlit")
    if os.path.exists(venv_streamlit):
        return venv_streamlit

    # Try to find in PATH
    import shutil
    streamlit_path = shutil.which("streamlit")
    if streamlit_path:
        return streamlit_path

    # Fall back to running as module
    return None


def start_streamlit() -> subprocess.Popen:
    """Start Streamlit server in background"""
    global streamlit_process

    app_path = os.path.join(APP_DIR, "app.py")
    streamlit_exe = find_streamlit_executable()

    if streamlit_exe:
        cmd = [
            streamlit_exe, "run", app_path,
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType", "none"
        ]
    else:
        # Run as Python module
        python_exe = find_python_executable()
        cmd = [
            python_exe, "-m", "streamlit", "run", app_path,
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType", "none"
        ]

    # Create log file for debugging
    log_path = os.path.join(APP_DIR, "streamlit.log")
    log_file = open(log_path, "w")

    streamlit_process = subprocess.Popen(
        cmd,
        cwd=APP_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid if os.name != 'nt' else None
    )

    return streamlit_process


def wait_for_server(max_wait: int = 60) -> bool:
    """Wait for server to be ready - increased timeout"""
    print(f"Waiting for server on port {PORT}...")
    for i in range(max_wait):
        if is_port_open(PORT):
            print(f"Server ready after {i+1} seconds")
            return True
        time.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"Still waiting... ({i}s)")
    return False


def cleanup() -> None:
    """Cleanup function to stop Streamlit server on exit"""
    global streamlit_process

    if streamlit_process:
        try:
            # Kill the process group
            if os.name != 'nt':
                os.killpg(os.getpgid(streamlit_process.pid), signal.SIGTERM)
            else:
                streamlit_process.terminate()

            # Wait for process to end
            streamlit_process.wait(timeout=5)
        except Exception:
            try:
                streamlit_process.kill()
            except Exception:
                pass

        streamlit_process = None


def on_window_closed() -> None:
    """Handle window close event"""
    cleanup()


def main() -> None:
    """Main entry point"""
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())

    # Start server if not running
    if not is_port_open(PORT):
        print("Starting Streamlit server...")
        start_streamlit()

        if not wait_for_server():
            print("Error: Could not start server")
            print(
                f"Check {os.path.join(APP_DIR, 'streamlit.log')} for details")
            cleanup()
            sys.exit(1)

    print("Opening application window...")

    # Import webview here to avoid slow startup
    import webview

    # Create native window
    window = webview.create_window(
        title="Zara Stock Tracker",
        url=URL,
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600),
        confirm_close=False
    )

    # Register close handler
    window.events.closed += on_window_closed

    # Start the GUI
    webview.start()

    # Cleanup after window closes
    cleanup()


if __name__ == "__main__":
    main()
