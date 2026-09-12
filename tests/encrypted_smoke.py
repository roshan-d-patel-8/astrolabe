import base64
import os
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright


def keychain_passphrase():
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "astrolabe-site", "-w"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def run():
    base = os.environ.get("ASTROLABE_TEST_URL", "http://127.0.0.1:4173").rstrip("/")
    token = base64.urlsafe_b64encode(keychain_passphrase().encode()).decode().rstrip("=")
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        locked = browser.new_context().new_page()
        locked.goto(f"{base}/index.html", wait_until="domcontentloaded")
        assert locked.get_by_role("button", name="Unlock").is_visible()

        page = browser.new_context().new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{base}/index.html#k={token}", wait_until="networkidle")
        page.locator('[data-panel="2"]').wait_for(state="visible")
        assert page.locator(".altitude-btn").count() == 5
        assert page.locator(".domain-row").count() == 10
        assert page.locator(".task-card").count() == len(page.evaluate("window.ASTRO_SNAPSHOT.tasks"))
        assert page.locator('link[href="atlas.css?v=4.1.0"]').count() == 1
        assert page.evaluate("window.ASTRO_SNAPSHOT.dashboards.every(d => d.preview.includes('markdown-preview-sizer'))")
        assert page.locator('#instrumentShelf .instrument-card').count() > 0
        assert page.evaluate('typeof window.ASTRO_CONNECTION') == 'undefined'
        assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--rail').trim()") in {"216px", "174px", "0px"}
        if os.environ.get("ASTROLABE_TEST_URL"):
            page.set_viewport_size({"width": 1440, "height": 1100})
            if page.locator("html").get_attribute("data-theme") != "dark":
                page.locator("#themeToggle").click()
            shots = Path(__file__).resolve().parents[1] / ".impeccable/review"
            shots.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(shots / "live.png"))
        browser.close()
    assert not errors, "\n".join(errors)
    print("encrypted shell: locked gate + magic-link decrypt + application boot PASS")


if __name__ == "__main__":
    run()
