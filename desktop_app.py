"""Zara Stock Tracker - Browser-based Desktop Application Launcher"""
import subprocess
import time
import sys
import os
import atexit
import signal
import socket
import webbrowser

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


def find_streamlit_executable() -> str:
    """Find the Streamlit executable to use"""
    venv_streamlit = os.path.join(APP_DIR, ".venv", "bin", "streamlit")
    if os.path.exists(venv_streamlit):
        return venv_streamlit

    import shutil
    streamlit_path = shutil.which("streamlit")
    if streamlit_path:
        return streamlit_path

    return None


def start_streamlit() -> subprocess.Popen:
    """Start Streamlit server in background"""
    global streamlit_process

    app_path = os.path.join(APP_DIR, "app.py")
    streamlit_exe = find_streamlit_executable()
    python_exe = os.path.join(APP_DIR, ".venv", "bin", "python")

    if streamlit_exe:
        cmd = [
            streamlit_exe, "run", app_path,
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType", "none"
        ]
    else:
        cmd = [
            python_exe, "-m", "streamlit", "run", app_path,
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType", "none"
        ]

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


def wait_for_server(max_wait: int = 30) -> bool:
    """Wait for server to be ready"""
    for i in range(max_wait):
        if is_port_open(PORT):
            return True
        time.sleep(1)
    return False


def cleanup() -> None:
    """Cleanup function to stop Streamlit server on exit"""
    global streamlit_process

    if streamlit_process:
        try:
            if os.name != 'nt':
                os.killpg(os.getpgid(streamlit_process.pid), signal.SIGTERM)
            else:
                streamlit_process.terminate()
            streamlit_process.wait(timeout=5)
        except Exception:
            try:
                streamlit_process.kill()
            except Exception:
                pass
        streamlit_process = None


def main() -> None:
    """Main entry point - opens in browser"""
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())

    # Start server if not running
    if not is_port_open(PORT):
        print("Starting Streamlit server...")
        start_streamlit()

        if not wait_for_server():
            print("Error: Could not start server")
            cleanup()
            sys.exit(1)

    print(f"Opening browser at {URL}...")
    webbrowser.open(URL)

    print("\n" + "="*50)
    print("Zara Stock Tracker is running!")
    print(f"Open in browser: {URL}")
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")

    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        cleanup()


if __name__ == "__main__":
    main()
