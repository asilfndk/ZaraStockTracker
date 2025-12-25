"""
Zara Stock Tracker - Menu Bar Background Service
Runs in background and monitors stock 24/7 with menu bar icon
"""
from zara_tracker.services import StockService, send_notification
from zara_tracker.db.repository import ProductRepository, SettingsRepository
from zara_tracker.db import init_db, get_db
import rumps
import os
import sys
import subprocess
import threading
import time
from datetime import datetime

# Add src to path before imports
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(APP_DIR, "src"))


class ZaraStockTrackerApp(rumps.App):
    """Menu bar application for Zara Stock Tracker."""

    def __init__(self):
        # Find icon
        icon_path = os.path.join(APP_DIR, "icon.png")
        icon_exists = os.path.exists(icon_path)

        super().__init__(
            name="Zara Stock Tracker",
            title=None if icon_exists else "🛍️",
            quit_button=None
        )

        if icon_exists:
            self.icon = icon_path

        # Initialize database
        init_db()

        # State
        with get_db() as db:
            self.check_interval = int(
                SettingsRepository.get(db, "menu_bar_interval", "300"))

        self.running = True
        self.streamlit_process = None
        self.last_check = None

        # Build menu
        self.menu = [
            rumps.MenuItem("🔄 Check Now", callback=self.check_now),
            rumps.MenuItem("📊 Open Dashboard", callback=self.open_dashboard),
            None,
            self._build_interval_menu(),
            None,
            rumps.MenuItem("📦 Tracking: ...", callback=None),
            rumps.MenuItem("📅 Last Check: Never", callback=None),
            None,
            rumps.MenuItem("❌ Quit", callback=self.quit_app),
        ]

        self.update_menu_stats()

        # Start background checker
        self.checker_thread = threading.Thread(
            target=self.background_checker, daemon=True)
        self.checker_thread.start()

        rumps.notification(
            "Zara Stock Tracker",
            "Background service started",
            f"Monitoring every {self.check_interval // 60} minute(s)"
        )

    def _build_interval_menu(self):
        """Build interval selection submenu."""
        menu = rumps.MenuItem("⏱️ Check Interval")
        menu.add(rumps.MenuItem(
            "1 minute", callback=lambda _: self.set_interval(60)))
        menu.add(rumps.MenuItem(
            "5 minutes", callback=lambda _: self.set_interval(300)))
        menu.add(rumps.MenuItem("15 minutes",
                 callback=lambda _: self.set_interval(900)))
        menu.add(rumps.MenuItem("30 minutes",
                 callback=lambda _: self.set_interval(1800)))
        return menu

    def set_interval(self, seconds):
        """Set check interval."""
        self.check_interval = seconds
        with get_db() as db:
            SettingsRepository.set(db, "menu_bar_interval", str(seconds))
        rumps.notification("Zara Stock Tracker", "",
                           f"Check interval set to {seconds // 60} minute(s)")

    def update_menu_stats(self):
        """Update menu with current stats."""
        try:
            with get_db() as db:
                count = ProductRepository.count_active(db)

            for key in self.menu.keys():
                if key.startswith("📦"):
                    self.menu[key].title = f"📦 Tracking: {count} products"
                    break
        except Exception:
            pass

    def check_now(self, _):
        """Manual check trigger."""
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        """Perform stock check."""
        try:
            with get_db() as db:
                country = SettingsRepository.get(db, "country_code", "tr")
                language = SettingsRepository.get(db, "language", "en")

            result = StockService.check_all_products(country, language)

            # Send notifications
            for alert in result.alerts:
                send_notification(
                    title="🎉 Size Available!",
                    message=f"{alert.product_name} - {alert.size} is now in stock! (₺{alert.price:.0f})"
                )

            # Update menu
            self.last_check = datetime.now()
            for key in self.menu.keys():
                if key.startswith("📅"):
                    self.menu[key].title = f"📅 Last Check: {self.last_check.strftime('%H:%M')}"
                    break

            self.update_menu_stats()

        except Exception as e:
            print(f"Check error: {e}")

    def background_checker(self):
        """Background thread that checks periodically."""
        time.sleep(10)  # Initial delay
        while self.running:
            self._do_check()
            time.sleep(self.check_interval)

    def open_dashboard(self, _):
        """Open Streamlit dashboard."""
        self._open_streamlit_dashboard()

    def _open_streamlit_dashboard(self):
        """Open Streamlit dashboard."""
        try:
            import urllib.request

            # Check if already running
            try:
                urllib.request.urlopen("http://localhost:8505", timeout=1)
                subprocess.run(["open", "http://localhost:8505"])
                return
            except:
                pass

            if self.streamlit_process and self.streamlit_process.poll() is None:
                subprocess.run(["open", "http://localhost:8505"])
                return

            # Use absolute paths - project root
            project_root = "/Users/asilfndk/Documents/GitHub/ZaraStok"
            streamlit_path = os.path.join(
                project_root, ".venv", "bin", "streamlit")
            app_path = os.path.join(project_root, "app.py")

            if not os.path.exists(streamlit_path):
                # Fallback to system streamlit
                result = subprocess.run(
                    ["which", "streamlit"], capture_output=True, text=True)
                if result.returncode == 0:
                    streamlit_path = result.stdout.strip()
                else:
                    rumps.notification("Zara Stock Tracker",
                                       "Error", "Streamlit not found")
                    return

            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.join(project_root, "src")

            self.streamlit_process = subprocess.Popen(
                [streamlit_path, "run", app_path, "--server.port", "8505"],
                cwd=project_root,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            time.sleep(3)
            subprocess.run(["open", "http://localhost:8505"])

        except Exception as e:
            rumps.notification("Zara Stock Tracker", "Error", str(e))

    def quit_app(self, _):
        """Quit the app."""
        self.running = False
        if self.streamlit_process:
            self.streamlit_process.terminate()
        rumps.quit_application()


def main():
    """Main entry point."""
    result = subprocess.run(
        ["pgrep", "-f", "menu_bar_app.py"], capture_output=True, text=True)
    pids = [p for p in result.stdout.strip().split(
        '\n') if p and p != str(os.getpid())]

    if pids:
        print("Menu bar app is already running!")
        subprocess.run(["open", "http://localhost:8505"])
        sys.exit(0)

    ZaraStockTrackerApp().run()


if __name__ == "__main__":
    main()
