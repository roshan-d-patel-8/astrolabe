from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / ".impeccable/review"
URL = "http://127.0.0.1:4173/.preview.html"


def contrast(a, b):
    def luminance(value):
        rgb = [int(value.lstrip("#")[i:i+2], 16) / 255 for i in (0, 2, 4)]
        rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
        return sum(x * weight for x, weight in zip(rgb, (.2126, .7152, .0722)))
    x, y = sorted([luminance(a), luminance(b)])
    return (y + .05) / (x + .05)


def run():
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(URL, wait_until="networkidle")
        snapshot = page.evaluate("ASTRO_SNAPSHOT")
        assert page.locator(".altitude-btn").count() == 5
        for wing in ("h", "s", "both"):
            page.locator(f'.wing-btn[data-wing="{wing}"]').click()
            assert page.locator(".wing-btn:visible").count() == 3
            assert page.locator(".domain-row:visible").count() == (10 if wing == "both" else 5)

        page.locator('[data-pillar="people"]').click()
        assert page.locator("#drawerClose").evaluate("el => el === document.activeElement")
        assert page.locator(".app-shell").evaluate("el => el.inert")
        page.locator("#domainMeasures").click()
        assert page.locator('[data-panel="4"]').is_visible()
        assert set(page.locator(".metric-label > span").all_text_contents()) == {"People"}
        page.get_by_role("button", name="F5 Momentum", exact=True).click()
        assert page.locator("#scopeLabel").inner_text().startswith("Focused on People")
        page.locator("#clearFocus").click()
        assert page.locator(".domain-row.selected").count() == 0
        assert "People" not in page.locator("#lineage").inner_text()
        assert page.locator(".task-card").count() == len(snapshot["tasks"])
        page.locator('[data-stage="forge"]').click()
        assert page.locator(".task-card").count() == sum(t["status"] == "forge" for t in snapshot["tasks"])
        page.locator('[data-priority="high"]').click()
        assert page.locator(".task-card").count() == sum(t["status"] == "forge" and t["priority"] == "high" for t in snapshot["tasks"])
        page.locator("#clearFocus").click()
        page.locator("#taskFilter").fill("no-such-task-xyz")
        assert page.locator(".task-card").count() == 0
        assert page.locator(".flow-segment").evaluate_all("els => els.every(el => el.getBoundingClientRect().width === 0)")
        page.locator("#taskFilter").fill("")
        page.locator(".task-card").first.click()
        page.keyboard.press("Escape")
        assert page.locator(".task-card").first.evaluate("el => el === document.activeElement")
        assert not page.locator("#drawer").is_visible()
        page.locator("#searchButton").click()
        page.locator("#paletteInput").fill("Sheikah")
        assert page.locator(".palette-result").count() >= 1
        page.locator(".palette-result").last.focus()
        page.keyboard.press("Tab")
        assert page.locator("#paletteInput").evaluate("el => el === document.activeElement")
        page.keyboard.press("Escape")
        assert page.locator("#searchButton").evaluate("el => el === document.activeElement")
        page.get_by_role("button", name="F2 Cartography", exact=True).click()
        assert page.locator('.altitude-btn[data-altitude="2"]').evaluate("el => el === document.activeElement")

        for width in (390, 768, 1024, 1440):
            page.set_viewport_size({"width": width, "height": 1000 if width > 800 else 844})
            for theme in ("light", "dark"):
                if page.locator("html").get_attribute("data-theme") != theme:
                    page.locator("#themeToggle").click()
                tokens = page.evaluate("Object.fromEntries(['paper','ink','muted','brass','accent','good','warn','critical','none'].map(k=>[k,getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim()]))")
                for token in ("ink", "muted", "brass", "accent", "good", "warn", "critical", "none"):
                    assert contrast(tokens[token], tokens["paper"]) >= 4.5, (theme, token)
                for altitude in range(1, 6):
                    page.locator(f'[data-altitude="{altitude}"]').click()
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), (width, theme, altitude)
                    assert page.locator("h1").is_visible()
                    if altitude == 5:
                        page.locator("#tasks-gate + .scroll-hint").wait_for(state="visible")
                        assert page.locator("#tasks-gate + .scroll-hint").is_visible()
                        assert str(sum(t["status"] == "gate" for t in snapshot["tasks"])) in page.locator("#tasks-gate + .scroll-hint").inner_text()
                    if width in (390, 1440):
                        page.screenshot(path=str(SHOTS / f"{width}-{theme}-f{altitude}.png"), full_page=True)
                page.locator('[data-altitude="2"]').click()
                if width == 1440 and theme == "dark":
                    page.screenshot(path=str(SHOTS / "desktop.png"))
                if width == 390 and theme == "light":
                    page.screenshot(path=str(SHOTS / "mobile.png"), full_page=True)
        page.get_by_role("button", name="F3 The Real", exact=True).click()
        page.locator("#fleetFilter").fill("no-such-instrument")
        assert page.locator(".fleet-item").count() == 0
        page.locator("#fleetFilter").fill("")
        assert page.locator(".fleet-item").count() == len(snapshot["dashboards"])
        page.get_by_role("button", name="F5 Momentum", exact=True).click()
        page.locator('.wing-btn[data-wing="h"]').click()
        assert page.locator(".task-card").count() == 0
        assert "outside" in page.locator("#scopeLabel").inner_text()
        page.locator("#clearFocus").click()
        assert page.locator(".task-card").count() == len(snapshot["tasks"])

        blocked = browser.new_page(reduced_motion="reduce")
        blocked.add_init_script("Storage.prototype.getItem = () => {throw new Error('blocked')}; Storage.prototype.setItem = () => {throw new Error('blocked')};")
        blocked.on("pageerror", lambda error: errors.append(str(error)))
        blocked.goto(URL, wait_until="networkidle")
        assert blocked.locator(".domain-row").count() == 10
        browser.close()
    assert not errors, errors
    print("makeover PASS: 40 viewport/theme/altitude checks; domain focus, wing switching, proportional zeros, board filters, modal focus, search, excluded Hathi state, blocked storage")


if __name__ == "__main__":
    run()
