"""
Zara Stock Tracker - Menu Bar Background Service
Runs in background and monitors stock 24/7 with menu bar icon
"""
from notifications import send_notification
from zara_scraper import ZaraScraper
from database import init_db, get_session, ZaraProduct, ZaraStockStatus, get_setting, add_price_history
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
    def __init__(self):
        super().__init__(
            name="Zara Stock Tracker",
            title="👗",
            quit_button=None  # We'll add our own
        )

        # Initialize database
        init_db()

        # Menu items
        self.menu = [
            rumps.MenuItem("🔄 Check Now", callback=self.check_now),
            rumps.MenuItem("📊 Open Dashboard", callback=self.open_dashboard),
            None,  # Separator
            rumps.MenuItem("⏱️ Check Interval", callback=None),
            None,  # Separator
            rumps.MenuItem("📦 Tracking: Loading...", callback=None),
            rumps.MenuItem("📅 Last Check: Never", callback=None),
            None,  # Separator
            rumps.MenuItem("❌ Quit", callback=self.quit_app),
        ]

        # Interval submenu
        self.interval_menu = self.menu["⏱️ Check Interval"]
        self.interval_menu.add(rumps.MenuItem(
            "1 minute", callback=self.set_interval_1))
        self.interval_menu.add(rumps.MenuItem(
            "5 minutes", callback=self.set_interval_5))
        self.interval_menu.add(rumps.MenuItem(
            "15 minutes", callback=self.set_interval_15))
        self.interval_menu.add(rumps.MenuItem(
            "30 minutes", callback=self.set_interval_30))

        # Settings
        self.check_interval = int(get_setting(
            "menu_bar_interval", "300"))  # Default 5 min
        self.running = True
        self.streamlit_process = None

        # Start background checker
        self.checker_thread = threading.Thread(
            target=self.background_checker, daemon=True)
        self.checker_thread.start()

        # Update menu with current stats
        self.update_menu_stats()

    def update_menu_stats(self):
        """Update menu with current tracking stats"""
        try:
            session = get_session()
            count = session.query(ZaraProduct).filter(
                ZaraProduct.active == 1).count()
            session.close()
            self.menu["📦 Tracking: Loading..."].title = f"📦 Tracking: {count} products"
        except:
            pass

    def set_interval_1(self, _):
        self.check_interval = 60
        rumps.notification("Zara Stock Tracker", "",
                           "Check interval set to 1 minute")

    def set_interval_5(self, _):
        self.check_interval = 300
        rumps.notification("Zara Stock Tracker", "",
                           "Check interval set to 5 minutes")

    def set_interval_15(self, _):
        self.check_interval = 900
        rumps.notification("Zara Stock Tracker", "",
                           "Check interval set to 15 minutes")

    def set_interval_30(self, _):
        self.check_interval = 1800
        rumps.notification("Zara Stock Tracker", "",
                           "Check interval set to 30 minutes")

    def check_now(self, _):
        """Manual check trigger"""
        self.title = "🔄"
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        """Perform stock check"""
        try:
            session = get_session()
            products = session.query(ZaraProduct).filter(
                ZaraProduct.active == 1).all()

            if not products:
                self.title = "👗"
                return

            scraper = ZaraScraper()
            alerts = []

            for product in products:
                try:
                    result = scraper.get_stock_status(product.url)

                    if result:
                        # Record price history
                        add_price_history(
                            product.id, result.price, result.old_price, result.discount)

                        # Check each size
                        for size_info in result.sizes:
                            current_stock = session.query(ZaraStockStatus).filter(
                                ZaraStockStatus.zara_product_id == product.id,
                                ZaraStockStatus.size == size_info.size
                            ).first()

                            new_stock = 1 if size_info.in_stock else 0

                            if current_stock:
                                # Check if desired size came in stock
                                if (new_stock == 1 and current_stock.in_stock == 0 and
                                    product.desired_size and
                                        size_info.size.upper() == product.desired_size.upper()):
                                    alerts.append({
                                        'name': product.product_name,
                                        'size': size_info.size,
                                        'price': result.price
                                    })

                                current_stock.in_stock = new_stock
                                current_stock.stock_status = size_info.stock_status
                                current_stock.last_updated = datetime.now()

                        product.price = result.price
                        product.old_price = result.old_price
                        product.discount = result.discount
                        product.last_check = datetime.now()

                except Exception as e:
                    print(f"Error checking {product.product_name}: {e}")

            session.commit()
            session.close()

            # Send notifications for alerts
            for alert in alerts:
                send_notification(
                    title="🎉 Size Available!",
                    message=f"{alert['name']} - {alert['size']} is now in stock! (₺{alert['price']:.0f})"
                )

            # Update menu
            self.menu["📅 Last Check: Never"].title = f"📅 Last Check: {datetime.now().strftime('%H:%M')}"
            self.update_menu_stats()

            # Flash icon if alerts
            if alerts:
                self.title = "🔔"
                time.sleep(2)

            self.title = "👗"

        except Exception as e:
            print(f"Check error: {e}")
            self.title = "⚠️"
            time.sleep(2)
            self.title = "👗"

    def background_checker(self):
        """Background thread that checks periodically"""
        while self.running:
            time.sleep(self.check_interval)
            if self.running:
                self._do_check()

    def open_dashboard(self, _):
        """Open the full Streamlit dashboard"""
        # Start Streamlit if not running
        if not self.streamlit_process or self.streamlit_process.poll() is not None:
            streamlit_path = os.path.join(APP_DIR, ".venv", "bin", "streamlit")
            app_path = os.path.join(APP_DIR, "app.py")

            self.streamlit_process = subprocess.Popen(
                [streamlit_path, "run", app_path, "--server.port", "8505"],
                cwd=APP_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(3)  # Wait for server to start

        # Open in browser
        subprocess.run(["open", "http://localhost:8505"])

    def quit_app(self, _):
        """Quit the app"""
        self.running = False

        # Stop Streamlit if running
        if self.streamlit_process:
            self.streamlit_process.terminate()

        rumps.quit_application()


if __name__ == "__main__":
    # Check if already running
    import subprocess
    result = subprocess.run(
        ["pgrep", "-f", "menu_bar_app.py"],
        capture_output=True, text=True
    )
    pids = [p for p in result.stdout.strip().split(
        '\n') if p and p != str(os.getpid())]

    if pids:
        print("Menu bar app is already running!")
        sys.exit(0)

    # Run the app
    ZaraStockTrackerApp().run()
