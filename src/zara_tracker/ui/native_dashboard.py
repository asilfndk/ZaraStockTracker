"""
Native macOS Dashboard for Zara Stock Tracker.
Uses PyObjC/Cocoa for a fully portable, Streamlit-free experience.
"""

from zara_tracker.db.repository import ProductRepository, StockRepository
from zara_tracker.db import get_db
from zara_tracker.services import ProductService, StockService
import os
import sys
import threading
from datetime import datetime

# Ensure src is in path
APP_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if os.path.join(APP_DIR, "src") not in sys.path:
    sys.path.insert(0, os.path.join(APP_DIR, "src"))

try:
    import objc
    import AppKit
    from AppKit import (
        NSApplication, NSWindow, NSWindowStyleMask, NSBackingStoreBuffered,
        NSTableView, NSScrollView, NSTableColumn, NSTextField, NSButton,
        NSView, NSFont, NSColor, NSObject, NSBezelStyleRounded,
        NSTableViewSelectionHighlightStyleRegular, NSLayoutAttributeTop,
        NSLayoutAttributeLeading, NSLayoutAttributeTrailing, NSLayoutAttributeBottom,
        NSLayoutAttributeHeight, NSLayoutAttributeWidth, NSLayoutRelationEqual,
        NSLayoutConstraint, NSAlert, NSAlertStyleInformational, NSAlertStyleWarning,
        NSStackView, NSUserInterfaceLayoutOrientationVertical,
        NSUserInterfaceLayoutOrientationHorizontal
    )
    from Foundation import NSMakeRect, NSObject
    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False


class ProductTableDataSource(NSObject):
    """Data source for product table."""

    def init(self):
        self = objc.super(ProductTableDataSource, self).init()
        if self is None:
            return None
        self._products = []
        self._stock_map = {}
        return self

    def reload_data(self):
        """Reload products from database."""
        with get_db() as db:
            self._products = ProductRepository.get_all_active(db)
            self._stock_map = {}
            for p in self._products:
                stocks = StockRepository.get_by_product(db, p.id)
                self._stock_map[p.id] = {s.size: s for s in stocks}
        return self._products

    def numberOfRowsInTableView_(self, table_view):
        return len(self._products)

    def tableView_objectValueForTableColumn_row_(self, table_view, column, row):
        if row >= len(self._products):
            return ""

        product = self._products[row]
        col_id = column.identifier()

        if col_id == "name":
            return product.product_name[:40] + "..." if len(product.product_name) > 40 else product.product_name
        elif col_id == "size":
            return product.desired_size
        elif col_id == "price":
            if product.old_price and product.old_price > product.price:
                return f"₺{product.price:.0f} (was ₺{product.old_price:.0f})"
            return f"₺{product.price:.0f}"
        elif col_id == "status":
            stocks = self._stock_map.get(product.id, {})
            size_stock = stocks.get(product.desired_size)
            if size_stock:
                if size_stock.in_stock:
                    return "✅ In Stock"
                else:
                    return "❌ Out of Stock"
            return "❓ Unknown"
        return ""

    def get_product_at_row(self, row):
        if 0 <= row < len(self._products):
            return self._products[row]
        return None


class NativeDashboardDelegate(NSObject):
    """Delegate for handling dashboard actions."""

    def initWithDashboard_(self, dashboard):
        self = objc.super(NativeDashboardDelegate, self).init()
        if self is None:
            return None
        self._dashboard = dashboard
        return self

    def addProductClicked_(self, sender):
        self._dashboard.show_add_product_dialog()

    def deleteProductClicked_(self, sender):
        self._dashboard.delete_selected_product()

    def refreshClicked_(self, sender):
        self._dashboard.refresh_products()

    def checkStockClicked_(self, sender):
        self._dashboard.check_stock()


class NativeDashboard:
    """Native macOS dashboard window."""

    _instance = None
    _window = None

    @classmethod
    def show(cls):
        """Show the dashboard window."""
        if not PYOBJC_AVAILABLE:
            print("PyObjC not available. Cannot show native dashboard.")
            return False

        if cls._window is not None and cls._window.isVisible():
            cls._window.makeKeyAndOrderFront_(None)
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            return True

        cls._instance = cls()
        cls._instance._create_window()
        return True

    def _create_window(self):
        """Create the dashboard window."""
        # Window dimensions
        width, height = 700, 500

        # Create window
        style = (NSWindowStyleMask.Titled |
                 NSWindowStyleMask.Closable |
                 NSWindowStyleMask.Miniaturizable |
                 NSWindowStyleMask.Resizable)

        self._class_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 200, width, height),
            style,
            NSBackingStoreBuffered,
            False
        )
        NativeDashboard._window = self._class_window

        self._class_window.setTitle_("Zara Stock Tracker")
        self._class_window.setMinSize_((500, 400))

        # Create delegate
        self._delegate = NativeDashboardDelegate.alloc().initWithDashboard_(self)

        # Create content view
        content = self._class_window.contentView()
        content.setWantsLayer_(True)

        # Create main vertical stack
        main_stack = NSStackView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        main_stack.setOrientation_(NSUserInterfaceLayoutOrientationVertical)
        main_stack.setSpacing_(10)
        main_stack.setEdgeInsets_((20, 20, 20, 20))
        main_stack.setTranslatesAutoresizingMaskIntoConstraints_(False)

        # Header
        header = NSTextField.labelWithString_("🛍️ Zara Stock Tracker")
        header.setFont_(NSFont.boldSystemFontOfSize_(24))
        main_stack.addArrangedSubview_(header)

        # Button bar
        button_bar = NSStackView.alloc().initWithFrame_(NSMakeRect(0, 0, width, 40))
        button_bar.setOrientation_(NSUserInterfaceLayoutOrientationHorizontal)
        button_bar.setSpacing_(10)

        # Add Product button
        add_btn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, 120, 32))
        add_btn.setTitle_("➕ Add Product")
        add_btn.setBezelStyle_(NSBezelStyleRounded)
        add_btn.setTarget_(self._delegate)
        add_btn.setAction_("addProductClicked:")
        button_bar.addArrangedSubview_(add_btn)

        # Delete button
        del_btn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 32))
        del_btn.setTitle_("🗑️ Delete")
        del_btn.setBezelStyle_(NSBezelStyleRounded)
        del_btn.setTarget_(self._delegate)
        del_btn.setAction_("deleteProductClicked:")
        button_bar.addArrangedSubview_(del_btn)

        # Refresh button
        refresh_btn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 32))
        refresh_btn.setTitle_("🔄 Refresh")
        refresh_btn.setBezelStyle_(NSBezelStyleRounded)
        refresh_btn.setTarget_(self._delegate)
        refresh_btn.setAction_("refreshClicked:")
        button_bar.addArrangedSubview_(refresh_btn)

        # Check Stock button
        check_btn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, 120, 32))
        check_btn.setTitle_("📡 Check Stock")
        check_btn.setBezelStyle_(NSBezelStyleRounded)
        check_btn.setTarget_(self._delegate)
        check_btn.setAction_("checkStockClicked:")
        button_bar.addArrangedSubview_(check_btn)

        main_stack.addArrangedSubview_(button_bar)

        # Create table view
        scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(0, 0, width - 40, height - 150))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setBorderType_(1)  # NSBezelBorder

        self._table = NSTableView.alloc().initWithFrame_(scroll_view.bounds())
        self._table.setSelectionHighlightStyle_(
            NSTableViewSelectionHighlightStyleRegular)
        self._table.setUsesAlternatingRowBackgroundColors_(True)
        self._table.setRowHeight_(28)

        # Add columns
        columns = [
            ("name", "Product Name", 280),
            ("size", "Size", 60),
            ("price", "Price", 150),
            ("status", "Status", 120),
        ]

        for col_id, title, width in columns:
            column = NSTableColumn.alloc().initWithIdentifier_(col_id)
            column.headerCell().setStringValue_(title)
            column.setWidth_(width)
            column.setMinWidth_(50)
            self._table.addTableColumn_(column)

        # Set data source
        self._data_source = ProductTableDataSource.alloc().init()
        self._data_source.reload_data()
        self._table.setDataSource_(self._data_source)

        scroll_view.setDocumentView_(self._table)
        main_stack.addArrangedSubview_(scroll_view)

        # Status bar
        self._status_label = NSTextField.labelWithString_("Ready")
        self._status_label.setFont_(NSFont.systemFontOfSize_(12))
        self._status_label.setTextColor_(NSColor.secondaryLabelColor())
        main_stack.addArrangedSubview_(self._status_label)

        # Add main stack to content view
        content.addSubview_(main_stack)

        # Setup constraints
        NSLayoutConstraint.activateConstraints_([
            main_stack.topAnchor().constraintEqualToAnchor_(content.topAnchor()),
            main_stack.leadingAnchor().constraintEqualToAnchor_(content.leadingAnchor()),
            main_stack.trailingAnchor().constraintEqualToAnchor_(content.trailingAnchor()),
            main_stack.bottomAnchor().constraintEqualToAnchor_(content.bottomAnchor()),
        ])

        # Show window
        self._class_window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

        self._update_status(
            f"Tracking {len(self._data_source._products)} products")

    def _update_status(self, message):
        """Update status label."""
        if hasattr(self, '_status_label'):
            self._status_label.setStringValue_(message)

    def show_add_product_dialog(self):
        """Show dialog to add a new product."""
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Add Product")
        alert.setInformativeText_(
            "Enter the Zara product URL and desired size:")
        alert.addButtonWithTitle_("Add")
        alert.addButtonWithTitle_("Cancel")
        alert.setAlertStyle_(NSAlertStyleInformational)

        # Create input fields
        accessory = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 400, 70))

        url_label = NSTextField.labelWithString_("URL:")
        url_label.setFrame_(NSMakeRect(0, 45, 50, 20))
        accessory.addSubview_(url_label)

        url_field = NSTextField.alloc().initWithFrame_(NSMakeRect(55, 45, 340, 22))
        url_field.setPlaceholderString_("https://www.zara.com/...")
        accessory.addSubview_(url_field)

        size_label = NSTextField.labelWithString_("Size:")
        size_label.setFrame_(NSMakeRect(0, 15, 50, 20))
        accessory.addSubview_(size_label)

        size_field = NSTextField.alloc().initWithFrame_(NSMakeRect(55, 15, 100, 22))
        size_field.setPlaceholderString_("M, L, 38...")
        accessory.addSubview_(size_field)

        alert.setAccessoryView_(accessory)

        # Show dialog
        response = alert.runModal()

        if response == 1000:  # First button (Add)
            url = url_field.stringValue()
            size = size_field.stringValue()

            if url and size:
                self._update_status("Adding product...")

                # Add product in background thread
                def add_product():
                    from zara_tracker.db.repository import SettingsRepository
                    with get_db() as db:
                        country = SettingsRepository.get(
                            db, "country_code", "tr")
                        language = SettingsRepository.get(db, "language", "en")

                    result = ProductService.add_product(
                        url, size, country, language)

                    # Update UI on main thread
                    def update_ui():
                        if result.success:
                            self._data_source.reload_data()
                            self._table.reloadData()
                            self._update_status(result.message)
                        else:
                            self._show_error(result.message)

                    # Schedule on main thread
                    from AppKit import NSOperationQueue
                    NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

                threading.Thread(target=add_product, daemon=True).start()
            else:
                self._show_error("Please enter both URL and size")

    def delete_selected_product(self):
        """Delete the selected product."""
        row = self._table.selectedRow()
        if row < 0:
            self._show_error("Please select a product to delete")
            return

        product = self._data_source.get_product_at_row(row)
        if not product:
            return

        # Confirm deletion
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Delete Product")
        alert.setInformativeText_(
            f"Are you sure you want to delete '{product.product_name}'?")
        alert.addButtonWithTitle_("Delete")
        alert.addButtonWithTitle_("Cancel")
        alert.setAlertStyle_(NSAlertStyleWarning)

        response = alert.runModal()

        if response == 1000:  # Delete
            ProductService.delete_product(product.id)
            self._data_source.reload_data()
            self._table.reloadData()
            self._update_status(f"Deleted '{product.product_name}'")

    def refresh_products(self):
        """Refresh product list from database."""
        self._data_source.reload_data()
        self._table.reloadData()
        self._update_status(
            f"Tracking {len(self._data_source._products)} products")

    def check_stock(self):
        """Trigger stock check for all products."""
        self._update_status("Checking stock...")

        def do_check():
            from zara_tracker.db.repository import SettingsRepository
            from zara_tracker.services import send_notification

            with get_db() as db:
                country = SettingsRepository.get(db, "country_code", "tr")
                language = SettingsRepository.get(db, "language", "en")

            result = StockService.check_all_products(country, language)

            # Send notifications for alerts
            for alert in result.alerts:
                send_notification(
                    title="🎉 Size Available!",
                    message=f"{alert.product_name} - {alert.size} is now in stock! (₺{alert.price:.0f})"
                )

            def update_ui():
                self._data_source.reload_data()
                self._table.reloadData()
                now = datetime.now().strftime("%H:%M")
                self._update_status(
                    f"Checked at {now} - {result.checked} products, {len(result.alerts)} alerts")

            from AppKit import NSOperationQueue
            NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        threading.Thread(target=do_check, daemon=True).start()

    def _show_error(self, message):
        """Show error alert."""
        self._update_status(f"Error: {message}")
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Error")
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_("OK")
        alert.setAlertStyle_(NSAlertStyleWarning)
        alert.runModal()


# Simple fallback for when PyObjC is not available
def show_simple_dashboard():
    """Fallback: open Streamlit if PyObjC unavailable."""
    import subprocess
    import os

    app_dir = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    venv_streamlit = os.path.join(app_dir, ".venv", "bin", "streamlit")

    if os.path.exists(venv_streamlit):
        app_path = os.path.join(app_dir, "app.py")
        subprocess.Popen(
            [venv_streamlit, "run", app_path, "--server.port", "8505"])
        subprocess.run(["open", "http://localhost:8505"])
        return True
    return False
