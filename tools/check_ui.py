"""Exercise real Flask routes in Chromium with disposable preview data.

Run: python tools/check_ui.py
Screenshots are regenerated in docs/images/ from fictional sample data.
"""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import re
import threading

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server
from preview import create_preview

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs/images"


def check():
    portal = create_preview()
    server = make_server("127.0.0.1", 0, portal.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    IMAGES.mkdir(parents=True, exist_ok=True)
    errors, external = [], []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width": 1440, "height": 1050}, reduced_motion="reduce")

            def local_only(route):
                if not route.request.url.startswith(base):
                    external.append(route.request.url)
                    route.abort()
                else:
                    route.continue_()

            context.route("**/*", local_only)
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base + "/portal")
            expect(page.get_by_role("heading", name="Good WiFi starts here.")).to_be_visible()
            expect(page.locator(".rate-card")).to_have_count(8)
            page.locator(".card").screenshot(path=str(IMAGES / "portal.png"))
            # Available plans lead to the request form and populate its hidden fields.
            page.locator("#tab-type .rate-card").nth(1).click()
            expect(page.get_by_role("tab", name="Request", exact=True)).to_have_attribute("aria-selected", "true")
            expect(page.locator("#lobby-plan-min")).to_have_value("60")
            page.locator("#lobby-submit").click()
            expect(page.locator(".lobby-confirm")).to_be_visible()
            expect(page.locator("#tab-request")).to_be_visible()
            page.locator(".card").screenshot(path=str(IMAGES / "request.png"))
            # Arrow keys switch tabs; voucher errors keep the portal usable.
            page.get_by_role("tab", name="Enter code", exact=True).click()
            page.get_by_role("tab", name="Enter code", exact=True).press("ArrowRight")
            expect(page.get_by_role("tab", name="Scan QR", exact=True)).to_be_focused()
            assert page.evaluate("typeof jsQR") == "function"
            page.get_by_role("tab", name="Enter code", exact=True).click()
            page.locator("#code-input").fill("BAD-CODE")
            page.get_by_role("button", name="Connect to internet").click()
            expect(page.get_by_role("alert")).to_contain_text("Invalid")
            # A two-hour voucher must remain on /status; regression for the modulo timer bug.
            page.locator("#code-input").fill("WIFI-2026")
            page.get_by_role("button", name="Connect to internet").click()
            expect(page).to_have_url(base + "/status")
            expect(page.locator("#countdown")).to_have_text(re.compile(r"01:59:5[5-9]"), timeout=3000)
            page.wait_for_timeout(1100)
            assert page.url.endswith("/status"), "Long sessions must not expire on an hour boundary"
            assert "low" not in page.locator("#countdown").get_attribute("class")
            page.locator(".card").screenshot(path=str(IMAGES / "session.png"))
            page.get_by_role("button", name="Pause Session").click()
            expect(page.locator(".paused-badge")).to_be_visible()
            page.get_by_role("button", name="Resume Session").click()
            expect(page.locator(".paused-badge")).to_have_count(0)
            # Freeze a second browser page at precisely two hours remaining.
            db = portal.get_db()
            expiry = db.execute("SELECT expires_at FROM codes WHERE code='WIFI-2026'").fetchone()[0]
            db.close()
            timer_page = context.new_page()
            timer_page.on("pageerror", lambda error: errors.append(str(error)))
            timer_page.clock.set_fixed_time(datetime.fromisoformat(expiry).replace(tzinfo=timezone.utc) - timedelta(hours=2))
            timer_page.goto(base + "/status")
            expect(timer_page.locator("#countdown")).to_have_text("02:00:00")
            timer_page.wait_for_timeout(1100)
            expect(timer_page).to_have_url(base + "/status")
            assert "low" not in timer_page.locator("#countdown").get_attribute("class")
            timer_page.close()
            # Authentication and all ten operator sections render with no JS errors.
            page.goto(base + "/admin")
            expect(page).to_have_url(base + "/admin/login")
            page.locator(".card").screenshot(path=str(IMAGES / "login.png"))
            page.get_by_label("Admin password").fill("wrong-password")
            page.get_by_role("button", name="Sign in").click()
            expect(page.get_by_role("alert")).to_be_visible()
            page.get_by_label("Admin password").fill(portal.ADMIN_SECRET)
            page.get_by_role("button", name="Sign in").click()
            expect(page.locator("#d-rx-speed")).to_have_text("24.80")
            page.screenshot(path=str(IMAGES / "dashboard.png"))
            page.get_by_role("button", name="＋ Create vouchers").click()
            expect(page.locator("#page-vouchers")).to_be_visible()
            for name in ("dashboard", "sessions", "charts", "lobby", "devices", "vouchers", "diagnostics", "settings", "analytics", "audit"):
                page.evaluate("name => navigateTo(name)", name)
                expect(page.locator("#page-" + name)).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), name
                page.wait_for_timeout(250)
            assert page.evaluate("typeof Chart") == "function"
            page.evaluate("navigateTo('vouchers')")
            page.screenshot(path=str(IMAGES / "vouchers.png"))
            # Breakpoints: content remains within the viewport and mobile drawers support Escape.
            for width in (320, 390, 768, 1024):
                page.set_viewport_size({"width": width, "height": 900})
                for name in ("sessions", "charts", "lobby", "devices", "vouchers", "diagnostics", "settings", "analytics", "audit"):
                    page.evaluate("name => navigateTo(name)", name)
                    overflow = page.evaluate("Array.from(document.querySelectorAll('.page.active *')).filter(el => el.getBoundingClientRect().right > innerWidth + 1 && !el.closest('.table-wrap')).slice(0, 6).map(el => el.outerHTML.slice(0, 200))")
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"{name} overflow at {width}: {overflow}"
                page.evaluate("navigateTo('dashboard')")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Admin overflow at {width}"
                if width < 768:
                    menu = page.locator(".topbar-hamburger")
                    menu.click()
                    expect(menu).to_have_attribute("aria-expanded", "true")
                    page.keyboard.press("Escape")
                    expect(menu).to_have_attribute("aria-expanded", "false")
                    expect(menu).to_be_focused()
                    page.screenshot(path=str(ROOT / "test-results" / f"admin-{width}.png"))
                page.goto(base + "/portal")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Portal overflow at {width}"
                if width == 390:
                    page.screenshot(path=str(IMAGES / "portal-mobile.png"), full_page=True)
                page.goto(base + "/admin")
            browser.close()
        assert not errors, errors
        assert not external, f"UI unexpectedly requested external resources: {external}"
        print("PASS: portal plans, request, keyboard tabs, invalid/valid vouchers, two-hour timer, pause/resume, admin login, ten pages, local assets, four responsive widths, drawer Escape.")
    finally:
        server.shutdown()
        server.server_close()
        portal.preview_directory.cleanup()


if __name__ == "__main__":
    (ROOT / "test-results").mkdir(exist_ok=True)
    check()
