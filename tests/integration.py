"""Acceptance tests follow the original intent, not merely inventory counts."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import build
from instruments import ROUTES

def run():
    snapshot = build.vault_snapshot()
    assert len(snapshot['dashboards']) == len(ROUTES) == 28
    for d in snapshot['dashboards']:
        assert d['levels'] and all(1 <= n <= 5 for n in d['levels'])
        soup = BeautifulSoup(d['preview'], 'html.parser')
        assert not soup.find(['script','iframe','object','embed','form','link','base'])
        assert not any(a.lower().startswith('on') for e in soup.find_all(True) for a in e.attrs)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:4173/.preview.html',wait_until='networkidle')
        for n in range(1,6):
            page.locator(f'[data-altitude="{n}"]').click()
            expected = sum(n in d['levels'] for d in snapshot['dashboards'])
            assert page.locator('#instrumentShelf .instrument-card').count() == expected
        for n in (1,3,5):
            page.locator(f'[data-altitude="{n}"]').click()
            page.locator('#instrumentShelf [data-open-instrument="Chronos and Kairos"]').click()
            assert page.locator('#instrumentWorkspace').is_visible()
            assert page.locator('#instrumentFrame').get_attribute('sandbox') == ''
            assert page.frame_locator('#instrumentFrame').get_by_text("TODAY'S WINDOW",exact=True).is_visible()
            assert page.locator('#instrumentSource').get_attribute('href').startswith('obsidian://')
            page.screenshot(path=str(build.HERE / '.impeccable/review/chronos-integrated.png'))
            page.locator('#instrumentBack').click()
            assert page.locator(f'[data-panel="{n}"]').is_visible()
            assert page.locator('#instrumentShelf [data-open-instrument="Chronos and Kairos"]').evaluate('e=>e===document.activeElement')
        page.locator('[data-altitude="2"]').click()
        page.locator('[data-pillar="people"]').click()
        page.locator('#domainMeasures').click()
        actual = page.locator('#instrumentShelf .instrument-card').count()
        assert actual == sum(4 in d['levels'] and (not d['domains'] or 'people' in d['domains']) for d in snapshot['dashboards'])
        page.locator('#clearFocus').click()
        page.locator('[data-altitude="5"]').click()
        page.locator('#dateFilter').select_option('undated')
        assert page.locator('.task-card').count() == sum(not t['due'] and not t['scheduled'] for t in snapshot['tasks'])
        page.locator('#dateFilter').select_option('all')
        assert 'Unassigned' in page.locator('#projectReadout').inner_text()
        page.locator('.task-card').first.click()
        assert page.locator('#taskEditor').count() == 0
        assert 'Published snapshot' in page.locator('#drawerBody').inner_text()
        page.keyboard.press('Escape')
        page.locator('#searchButton').click()
        page.locator('#paletteInput').fill('Chronos')
        page.locator('.palette-result').click()
        assert page.locator('#instrumentWorkspace').is_visible()
        page.keyboard.press('Escape')
        assert not page.locator('#instrumentWorkspace').is_visible()
        for width in (390,1440):
            page.set_viewport_size({'width':width,'height':900})
            for theme in ('light','dark'):
                if page.locator('html').get_attribute('data-theme') != theme: page.locator('#themeToggle').click()
                for n in (2,3,5):
                    page.locator(f'[data-altitude="{n}"]').click()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(build.HERE / f'.impeccable/review/integration-{width}-{theme}-f{n}.png'))
        browser.close()
    assert not errors, errors
    print('PASS: 28 isolated captures; all focus/domain routes; Chronos in F1/F3/F5; in-site search; project/date views; public write boundary; desktop/mobile light/dark')

if __name__ == '__main__': run()
