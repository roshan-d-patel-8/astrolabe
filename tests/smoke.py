from pathlib import Path
from playwright.sync_api import sync_playwright


def run():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("console", lambda msg: errors.append(f"console:{msg.type}:{msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"page:{error}"))
        page.goto("http://127.0.0.1:4173/.preview.html", wait_until="networkidle")
        page.locator('[data-panel="2"]').wait_for(state="visible")
        assert page.locator(".altitude-btn").count() == 5
        assert page.get_by_role("button", name="F1 Compass").count() == 1
        assert page.get_by_role("button", name="F5 Momentum").count() == 1
        assert page.get_by_role("button", name="F0 Ground").count() == 0
        assert page.get_by_role("button", name="F6 Andon").count() == 0
        assert page.locator(".domain-row").count() == 10
        snapshot = page.evaluate("window.ASTRO_SNAPSHOT")

        page.get_by_role("button", name="F1 Compass").click()
        page.locator('[data-panel="1"]').wait_for(state="visible")
        assert page.locator(".value-label").count() == 5
        assert page.locator(".readout-cell").count() == 5
        page.wait_for_timeout(500)
        page.screenshot(path="/tmp/astrolabe-f1.png", full_page=True)

        page.get_by_role("button", name="F3 Monocle").click()
        page.locator('[data-panel="3"]').wait_for(state="visible")
        assert page.locator(".fleet-item").count() == len(snapshot["dashboards"])
        page.wait_for_timeout(500)
        page.screenshot(path="/tmp/astrolabe-f3.png", full_page=True)

        page.get_by_role("button", name="F4 Lens").click()
        page.locator('[data-panel="4"]').wait_for(state="visible")
        assert page.locator(".metric-row").count() == page.evaluate("window.ASTRO_METRICS.length")
        page.wait_for_timeout(500)
        page.screenshot(path="/tmp/astrolabe-f4.png", full_page=True)

        page.get_by_role("button", name="F5 Momentum").click()
        page.locator('[data-panel="5"]').wait_for(state="visible")
        assert page.locator(".task-card").count() == len(snapshot["tasks"])
        assert page.locator(".flow-stage").count() == 3
        assert page.locator(".priority-row").count() == 3
        page.locator(".task-card").first.click()
        page.locator("#drawer.open").wait_for(state="visible")
        page.locator("#drawerClose").click()

        page.locator("#themeToggle").click()
        assert page.locator("html").get_attribute("data-theme") in {"light", "dark"}
        page.keyboard.press("/")
        page.locator("#palette.open").wait_for(state="visible")
        page.locator("#paletteInput").fill("Sheikah")
        assert page.locator(".palette-result").count() >= 1
        page.keyboard.press("Escape")
        page.screenshot(path="/tmp/astrolabe-desktop.png", full_page=True)

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.on("pageerror", lambda error: errors.append(f"mobile:{error}"))
        mobile.goto("http://127.0.0.1:4173/.preview.html", wait_until="networkidle")
        mobile.get_by_role("button", name="F2 Cartography").click()
        assert mobile.locator(".altitude-rail").is_visible()
        assert mobile.locator('[data-panel="2"]').is_visible()
        mobile.screenshot(path="/tmp/astrolabe-mobile.png", full_page=True)
        browser.close()

    assert not errors, "\n".join(errors)
    for path in ("/tmp/astrolabe-f1.png", "/tmp/astrolabe-f3.png", "/tmp/astrolabe-f4.png", "/tmp/astrolabe-desktop.png", "/tmp/astrolabe-mobile.png"):
        assert Path(path).stat().st_size > 20_000
    print(f"smoke: {len(snapshot['dashboards'])} dashboards, {len(snapshot['tasks'])} active tasks, five visual altitudes, drawer, palette, themes, desktop/mobile PASS")


if __name__ == "__main__":
    run()
