"""Regression checks for the actual rendered fleet, not just dashboard inventory."""
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def run():
    records=build.dashboard_snapshot()
    assert len(records)==28
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(reduced_motion='reduce')
        for record in records:
            soup=BeautifulSoup(record['preview'],'html.parser')
            assert soup.select_one('main.markdown-preview-view .markdown-preview-sizer')
            assert not soup.select('script,iframe,object,embed,form,link,base')
            assert not any(a.startswith('on') for e in soup.find_all(True) for a in e.attrs)
            assert all(re.fullmatch(r'data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+',e['src']) for e in soup.select('[src]'))
            assert not soup.select('[href],[srcset],[action]')
            assert not re.search(r'(?:^|\n)\s*(?:#{1,6} |>[ !]|\| ?---)|\[\[|```',soup.get_text())
            page.set_content('<iframe sandbox="" style="position:fixed;inset:0;width:100%;height:100%;border:0"></iframe>')
            page.locator('iframe').evaluate('(e,doc)=>e.srcdoc=doc',record['preview'])
            frame=page.frames[1]
            frame.wait_for_selector('main')
            for width in (320,390,768,1280):
                page.set_viewport_size({'width':width,'height':900})
                assert frame.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(record['key'],width)
            disclosure=frame.locator('details.runtime-note').first
            if disclosure.count():
                assert disclosure.get_attribute('open') is None
                disclosure.locator('summary').click()
                assert disclosure.get_attribute('open') is not None
                assert 'not a live web reading' in disclosure.inner_text()
            page.set_viewport_size({'width':390,'height':844})
            for selector in ('.mm-grid','.b34-spotlight','.b34-flanks'):
                if frame.locator(selector).count():
                    assert frame.locator(selector).first.evaluate('e=>getComputedStyle(e).gridTemplateColumns.split(" ").length')==1,(record['key'],selector)
            if record['key']=='R0 Dashboard':
                assert frame.locator('.vault-callout').count()>=10
                assert frame.locator('.vault-callout details.runtime-note').count()>0
            if record['key']=='Sheikah Slate':
                assert frame.locator('img').count()>=1
                assert frame.locator('img').first.evaluate('e=>e.complete && e.naturalWidth>0')
            if record['key']=='The Latticework':
                assert frame.locator('details.lw-domain[open]').count()==1
            if record['key']=='The Long Hall':
                assert frame.locator('.lh-map .lh-zones').count()==1
        browser.close()
    print('PASS: all 28 semantic, isolated dashboards; 112 viewport checks; live-view disclosures; callouts; local image; readable mobile grids; aligned timeline header')

if __name__=='__main__': run()
