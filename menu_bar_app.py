"""
Zara Stock Tracker - Menu Bar Background Service
Runs in background and monitors stock 24/7 with menu bar icon
"""
from database import (
    init_db, get_session, ZaraProduct, ZaraStockStatus,
    get_setting, set_setting, add_price_history
)
from scraper import get_scraper_for_url
from notifications import send_notification
import rumps
import threading
import time
from datetime import datetime
import subprocess
import os
import sys

# Add project directory to path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)


class ZaraStockTrackerApp(rumps.App):
    """Menu bar application for Zara Stock Tracker"""

    def __init__(self):
        # Find icon path
        icon_path = os.path.join(APP_DIR, "icon.png")
        if not os.path.exists(icon_path):
            # Try in Resources folder (when bundled)
            icon_path = os.path.join(os.path.dirname(
                APP_DIR), "Resources", "icon.png")

        icon_exists = os.path.exists(icon_path)

        super().__init__(
            name="Zara Stock Tracker",
            title=None if icon_exists else "�️",
            quit_button=None  # Custom quit button
        )

        # Set icon after init if exists
        if icon_exists:
            self.icon = icon_path

        # Initialize database
        init_db()

        # State
        self.check_interval = int(get_setting(
            "menu_bar_interval", "300"))  # 5 min default
        self.running = True
        self.streamlit_process = None
        self.last_check = None

        # Build menu
        self.menu = [
            rumps.MenuItem("🔄 Check Now", callback=self.check_now),
            rumps.MenuItem("📊 Open Dashboard", callback=self.open_dashboard),
            None,  # Separator
            self._build_interval_menu(),
            None,  # Separator
            rumps.MenuItem("📦 Tracking: ...", callback=None),
            rumps.MenuItem("📅 Last Check: Never", callback=None),
            None,  # Separator
            rumps.MenuItem("❌ Quit", callback=self.quit_app),
        ]

        # Update stats
        self.update_menu_stats()

        # Start background checker
        self.checker_thread = threading.Thread(
            target=self.background_checker, daemon=True
        )
        self.checker_thread.start()

        # Initial notification
        rumps.notification(
            "Zara Stock Tracker",
            "Background service started",
            f"Monitoring every {self.check_interval // 60} minute(s)"
        )

    def _build_interval_menu(self):
        """Build interval selection submenu"""
        interval_menu = rumps.MenuItem("⏱️ Check Interval")
        interval_menu.add(rumps.MenuItem(
            "1 minute", callback=lambda _: self.set_interval(60)))
        interval_menu.add(rumps.MenuItem(
            "5 minutes", callback=lambda _: self.set_interval(300)))
        interval_menu.add(rumps.MenuItem(
            "15 minutes", callback=lambda _: self.set_interval(900)))
        interval_menu.add(rumps.MenuItem(
            "30 minutes", callback=lambda _: self.set_interval(1800)))
        return interval_menu

    def set_interval(self, seconds):
        """Set check interval"""
        self.check_interval = seconds
        set_setting("menu_bar_interval", str(seconds))
        rumps.notification(
            "Zara Stock Tracker",
            "",
            f"Check interval set to {seconds // 60} minute(s)"
        )

    def update_menu_stats(self):
        """Update menu with current tracking stats"""
        try:
            session = get_session()
            count = session.query(ZaraProduct).filter(
                ZaraProduct.active == 1
            ).count()
            session.close()

            # Find and update the tracking menu item
            for key in self.menu.keys():
                if key.startswith("📦"):
                    self.menu[key].title = f"📦 Tracking: {count} products"
                    break
        except Exception as e:
            print(f"Stats update error: {e}")

    def check_now(self, _):
        """Manual check trigger"""
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        """Perform stock check for all products"""
        try:
            # 1. Get list of active products quickly
            session = get_session()
            db_products = session.query(ZaraProduct).filter(
                ZaraProduct.active == 1
            ).all()

            # Convert to list of dicts to detach from session
            products_to_check = []
            for p in db_products:
                products_to_check.append({
                    'id': p.id,
                    'url': p.url,
                    'product_name': p.product_name,
                    'desired_size': p.desired_size
                })

            session.close()

            if not products_to_check:
                return

            alerts = []

            # 2. Process each product independently
            for p_data in products_to_check:
                try:
                    # A. Scrape (takes time, no DB lock)
                    scraper = get_scraper_for_url(p_data['url'])
                    result = scraper.get_stock_status(p_data['url'])

                    if not result:
                        continue

                    # B. Update DB (fast, short lock)
                    session = get_session()
                    product = session.query(ZaraProduct).filter(
                        ZaraProduct.id == p_data['id']).first()

                    if not product:  # Generated if deleted while scraping
                        session.close()
                        continue

                    # Record price history
                    add_price_history(
                        product.id, result.price,
                        result.old_price, result.discount
                    )

                    # Update sizes
                    for size_info in result.sizes:
                        current_stock = session.query(ZaraStockStatus).filter(
                            ZaraStockStatus.zara_product_id == product.id,
                            ZaraStockStatus.size == size_info.size
                        ).first()

                        new_stock = 1 if size_info.in_stock else 0

                        if current_stock:
                            # Check if desired size came in stock
                            if (new_stock == 1 and current_stock.in_stock == 0 and
                                p_data['desired_size'] and
                                    size_info.size.upper() == p_data['desired_size'].upper()):
                                alerts.append({
                                    'name': p_data['product_name'],
                                    'size': size_info.size,
                                    'price': result.price
                                })

                            current_stock.in_stock = new_stock
                            current_stock.stock_status = size_info.stock_status
                            current_stock.last_updated = datetime.now()
                        else:
                            # New size found (e.g. added later)
                            new_status = ZaraStockStatus(
                                zara_product_id=product.id,
                                size=size_info.size,
                                in_stock=new_stock,
                                stock_status=size_info.stock_status,
                                last_updated=datetime.now()
                            )
                            session.add(new_status)

                    product.price = result.price
                    product.old_price = result.old_price
                    product.discount = result.discount
                    product.last_check = datetime.now()

                    session.commit()
                    session.close()

                except Exception as e:
                    print(f"Error checking {p_data.get('product_name')}: {e}")
                    # Ensure session is closed if error occurs during DB update
                    try:
                        session.close()
                    except:
                        pass

            # Send notifications for alerts
            for alert in alerts:
                send_notification(
                    title="🎉 Size Available!",
                    message=f"{alert['name']} - {alert['size']} is now in stock! (₺{alert['price']:.0f})"
                )

            # Update menu
            self.last_check = datetime.now()
            for key in self.menu.keys():
                if key.startswith("📅"):
                    self.menu[key].title = f"📅 Last Check: {self.last_check.strftime('%H:%M')}"
                    break

            self.update_menu_stats()

            # Notification for alerts (no icon change)
            if alerts:
                pass  # Notifications already sent above

        except Exception as e:
            print(f"Check error: {e}")

    def background_checker(self):
        """Background thread that checks periodically"""
        # Wait a bit before first check
        time.sleep(10)

        while self.running:
            self._do_check()
            time.sleep(self.check_interval)

    def open_dashboard(self, _):
        """Open the full Streamlit dashboard"""
        try:
            # First, try to just open the browser if something is already running on port 8505
            import urllib.request
            try:
                urllib.request.urlopen("http://localhost:8505", timeout=1)
                subprocess.run(["open", "http://localhost:8505"])
                return
            except:
                pass  # Not running, need to start

            # Check if Streamlit is already running via our process
            if self.streamlit_process and self.streamlit_process.poll() is None:
                subprocess.run(["open", "http://localhost:8505"])
                return

            # Get the project directory - prefer environment variable or known location
            project_dir = os.environ.get("ZARA_PROJECT_DIR")
            if not project_dir:
                # Try common locations
                possible_paths = [
                    os.path.expanduser("~/Documents/GitHub/ZaraStok"),
                    "/Users/asilfndk/Documents/GitHub/ZaraStok",
                    APP_DIR,
                ]
                for path in possible_paths:
                    if os.path.exists(os.path.join(path, "app.py")):
                        project_dir = path
                        break

            if not project_dir or not os.path.exists(os.path.join(project_dir, "app.py")):
                rumps.notification(
                    "Zara Stock Tracker",
                    "Dashboard Unavailable",
                    "Run 'streamlit run app.py' manually from project folder"
                )
                return

            # Find streamlit executable
            venv_streamlit = os.path.join(
                project_dir, ".venv", "bin", "streamlit")
            if os.path.exists(venv_streamlit):
                streamlit_path = venv_streamlit
            else:
                # Try to find streamlit in PATH
                result = subprocess.run(
                    ["which", "streamlit"], capture_output=True, text=True)
                if result.returncode == 0:
                    streamlit_path = result.stdout.strip()
                else:
                    rumps.notification(
                        "Zara Stock Tracker",
                        "Streamlit Not Found",
                        "Install Streamlit or run from project folder"
                    )
                    return

            app_path = os.path.join(project_dir, "app.py")

            self.streamlit_process = subprocess.Popen(
                [streamlit_path, "run", app_path, "--server.port", "8505"],
                cwd=project_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait for server to start
            time.sleep(3)
            subprocess.run(["open", "http://localhost:8505"])

        except Exception as e:
            rumps.notification(
                "Zara Stock Tracker",
                "Error",
                f"Could not open dashboard: {e}"
            )

    def quit_app(self, _):
        """Quit the app"""
        self.running = False

        # Stop Streamlit if running
        if self.streamlit_process:
            self.streamlit_process.terminate()

        rumps.quit_application()


def main():
    """Main entry point"""
    # Check if already running
    result = subprocess.run(
        ["pgrep", "-f", "menu_bar_app.py"],
        capture_output=True, text=True
    )
    pids = [p for p in result.stdout.strip().split(
        '\n') if p and p != str(os.getpid())]

    if pids:
        # Already running - open dashboard instead
        print("Menu bar app is already running! Opening dashboard...")
        subprocess.run(["open", "http://localhost:8505"])
        sys.exit(0)

    # Run the app
    ZaraStockTrackerApp().run()


if __name__ == "__main__":
    main()
