"""Identity-specific checks; never mutate canonical vault records."""
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:4173/.preview.html'

def run():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width':1600,'height':1100})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL, wait_until='networkidle')
        assert page.locator('html').get_attribute('data-theme') == 'dark'
        assert page.locator('.altitude-btn svg').count() == 5
        assert page.locator('.domain-seal svg').count() == 10
        assert page.locator('.relic-image').evaluate('e=>e.complete && e.naturalWidth>0')
        page.locator('[data-focus-jump="1"]').click()
        assert page.locator('#dialFocus').inner_text() == 'F1'
        assert page.locator('.polaris-relic .ambient #starfield').count() == 1
        assert page.locator('.polaris-relic img').evaluate('e=>e.complete && e.naturalWidth>0')
        page.locator('[data-altitude="2"]').click()
        page.locator('[data-focus-jump="5"]').click()
        assert page.locator('#dialFocus').inner_text() == 'F5'
        assert page.locator('.planning-notes').get_attribute('open') is None
        page.locator('.planning-notes summary').click()
        assert page.locator('.planning-notes').get_attribute('open') is not None
        page.locator('[data-altitude="3"]').click()
        assert page.locator('.instrument-card:visible').count() == 4
        page.locator('#expandInstruments').click()
        assert page.locator('.instrument-card:visible').count() == page.locator('.instrument-card').count()
        page.locator('#themeToggle').click()
        page.reload(wait_until='networkidle')
        assert page.locator('html').get_attribute('data-theme') == 'light'
        page.set_viewport_size({'width':320,'height':740})
        for n in range(1,6):
            page.locator(f'[data-altitude="{n}"]').click()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), n
            for control in ('#searchButton','#observatoryButton','#themeToggle'):
                assert page.locator(control).is_visible()
                box = page.locator(control).bounding_box()
                assert box['x'] >= 0 and box['x'] + box['width'] <= 320
        offline = browser.new_page(reduced_motion='reduce')
        offline.on('pageerror', lambda error: errors.append(str(error)))
        offline.route('https://**/*', lambda route: route.abort())
        offline.goto(URL, wait_until='networkidle')
        assert offline.locator('.relic-image').evaluate('e=>e.complete && e.naturalWidth>0')
        offline.locator('[data-altitude="1"]').click()
        assert offline.locator('.polaris-relic').is_visible()
        browser.close()
    assert not errors, errors
    print('identity PASS: source art, glyphs, focus dial/jumps, shelf expansion, persisted theme, 320px controls, blocked-CDN fallback, normal/reduced motion boot')

if __name__ == '__main__':
    run()
