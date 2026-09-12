import base64
import subprocess
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
    token = base64.urlsafe_b64encode(keychain_passphrase().encode()).decode().rstrip("=")
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        locked = browser.new_context().new_page()
        locked.goto("http://127.0.0.1:4173/index.html", wait_until="domcontentloaded")
        assert locked.get_by_role("button", name="Unlock").is_visible()

        page = browser.new_context().new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"http://127.0.0.1:4173/index.html#k={token}", wait_until="networkidle")
        page.locator('[data-panel="2"]').wait_for(state="visible")
        assert page.get_by_text("The dashboard fleet").count() == 1
        assert page.locator(".task-card").count() == len(page.evaluate("window.ASTRO_SNAPSHOT.tasks"))
        browser.close()
    assert not errors, "\n".join(errors)
    print("encrypted shell: locked gate + magic-link decrypt + application boot PASS")


if __name__ == "__main__":
    run()
