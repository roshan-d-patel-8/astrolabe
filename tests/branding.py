"""The approved wordmark loads without font software or layout changes."""
from pathlib import Path
from playwright.sync_api import sync_playwright

def run():
    out=Path(__file__).resolve().parents[1]/'.impeccable/review/red5'
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(reduced_motion='reduce')
        requested=[]
        page.on('request',lambda r: requested.append(r.url))
        page.goto('http://127.0.0.1:4173/.preview.html',wait_until='networkidle')
        assert page.title()=='Red5'
        assert page.locator('.brand-mark').count()==0
        assert page.locator('.rail-dial,.domain-orientation').count()==0
        assert page.locator('.red5-wordmark path').count()==4
        assert not any('TNG_Title' in url or 'red5.ttf' in url for url in requested)
        assert page.locator('#paletteInput').get_attribute('aria-label')=='Search Red5'
        for width in (1440,390,320):
            page.set_viewport_size({'width':width,'height':1000 if width==1440 else 844})
            for theme in ('light','dark'):
                if page.locator('html').get_attribute('data-theme')!=theme: page.locator('#themeToggle').click()
                assert page.get_by_role('img',name='Red5',exact=True).is_visible()
                fill=page.locator('.red5-wordmark path').last.evaluate('e=>getComputedStyle(e).fill')
                assert fill==('rgb(185, 50, 40)' if theme=='light' else 'rgb(241, 134, 112)')
                for altitude in range(1,6):
                    page.locator(f'[data-altitude="{altitude}"]').click()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,theme,altitude)
                page.locator('[data-altitude="2"]').click()
                page.screenshot(path=str(out/f'{width}-{theme}.png'))
        browser.close()
    print('branding PASS: accessible SVG, theme colors, no font request, 30 viewport/theme/altitude checks')

if __name__=='__main__':run()
