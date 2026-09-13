"""F4 visual isolation, data honesty, controls and responsive evidence."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from makeover import contrast

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.impeccable/review/f4-terminal'

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:4173/.preview.html',wait_until='networkidle')
        # Disabling the new stylesheet must not change any incumbent F view.
        styles="""Object.fromEntries(['body','.topbar','.workspace','.altitude-rail','.altitude-btn','.brand-name'].map(s=>{const e=document.querySelector(s),c=getComputedStyle(e),b=e.getBoundingClientRect();return [s,[c.color,c.backgroundColor,c.fontFamily,c.fontSize,c.display,b.x,b.y,b.width,b.height]]}))"""
        for altitude in (1,2,3,5):
            page.locator(f'[data-altitude="{altitude}"]').click()
            original=page.evaluate(styles)
            page.locator('link[href*="f4-terminal.css"]').evaluate('e=>e.disabled=true')
            assert page.evaluate(styles)==original,altitude
            page.locator('link[href*="f4-terminal.css"]').evaluate('e=>e.disabled=false')
        root_theme=page.locator('html').get_attribute('data-theme')
        page.locator('[data-altitude="4"]').click()
        assert page.locator('body').get_attribute('data-lens-theme')=='dark'
        assert page.locator('.metric-row').count()==int(page.locator('#lensSourceCount').inner_text())
        counts=[int(x) for x in page.locator('.condition-line b').all_text_contents()]
        assert sum(counts)==page.locator('.metric-row').count()
        for i,n in enumerate(counts):
            value=page.locator('.condition-track i').nth(i).evaluate('e=>parseFloat(e.style.getPropertyValue("--share"))')
            assert abs(value-n/sum(counts)*100)<.001
        page.locator('.wing-btn[data-wing="h"]').click()
        assert page.locator('#lensScope').inner_text()=='Hathi'
        assert int(page.locator('#lensSourceCount').inner_text())==page.locator('.metric-row').count()
        page.locator('.wing-btn[data-wing="both"]').click()
        page.locator('#lensInstruments').click()
        assert page.locator('#instrumentShelf .instrument-card').first.evaluate('e=>e===document.activeElement')
        page.locator('#instrumentShelf .instrument-card').first.click()
        assert page.locator('#instrumentWorkspace').is_visible()
        page.locator('#instrumentBack').click()
        for width in (2048,1440,390,320):
            page.set_viewport_size({'width':width,'height':1152 if width==2048 else 1000 if width==1440 else 844})
            for theme in ('dark','light'):
                if page.locator('body').get_attribute('data-lens-theme')!=theme:page.locator('#themeToggle').click()
                assert page.locator('html').get_attribute('data-theme')==root_theme
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,theme)
                tokens=page.evaluate("Object.fromEntries(['paper','ink','muted','accent','good','warn','critical','none'].map(k=>[k,getComputedStyle(document.body).getPropertyValue('--'+k).trim()]))")
                for k in ('ink','muted','accent','good','warn','critical','none'):assert contrast(tokens[k],tokens['paper'])>=4.5,(theme,k)
                page.evaluate('document.fonts.ready')
                assert page.evaluate('document.fonts.check(\'16px "Share Tech Mono"\') && document.fonts.check(\'76px "VT323"\')')
                page.evaluate('scrollTo(0,0)')
                if width in (1440,390) or (width==2048 and theme=='dark'):
                    page.screenshot(path=str(OUT/f'{width}-{theme}.png'))
                if width in (1440,390) and theme=='dark':
                    page.screenshot(path=str(OUT/f'{width}-dark-full.png'),full_page=True)
        page.reload(wait_until='networkidle')
        assert page.locator('body').get_attribute('data-lens-theme')=='light'
        page.locator('[data-altitude="2"]').click()
        assert page.locator('html').get_attribute('data-theme')==root_theme
        browser.close()
    assert not errors,errors
    print('F4 PASS: isolated themes, exact condition proportions, scope, instrument navigation, persisted preference, 4 widths/2 modes, contrast, fonts')

if __name__=='__main__':run()
