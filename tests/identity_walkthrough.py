"""Private visual evidence for the vault-derived Astrolabe identity."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

def run(phase,url):
    out=Path(__file__).resolve().parents[1]/'.impeccable/review/identity'/phase
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1600,'height':1100},reduced_motion='reduce')
        page.goto(url,wait_until='networkidle')
        for width in (1600,390):
            page.set_viewport_size({'width':width,'height':1100 if width>800 else 844})
            for theme in ('dark','light'):
                if page.locator('html').get_attribute('data-theme')!=theme: page.locator('#themeToggle').click()
                for altitude in range(1,6):
                    page.locator(f'.altitude-btn[data-altitude="{altitude}"]').click()
                    page.wait_for_timeout(200)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,theme,altitude)
                    page.screenshot(path=str(out/f'{width}-{theme}-f{altitude}.png'))
        browser.close()
    print('PASS: visual walkthrough, five focus levels in two themes at desktop and phone widths')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase');parser.add_argument('--url',default='http://127.0.0.1:8795/');args=parser.parse_args();run(args.phase,args.url)
