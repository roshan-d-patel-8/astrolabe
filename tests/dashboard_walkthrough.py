"""Capture every instrument, not a representative sample. Outputs stay ignored/private."""
import argparse
import base64
import html
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
from playwright.sync_api import sync_playwright

def run(phase):
    dest=build.HERE/'.impeccable/review/dashboards'/phase
    dest.mkdir(parents=True,exist_ok=True)
    records=build.dashboard_snapshot()
    diagnostics=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce')
        for i,d in enumerate(records):
            page.set_content('<iframe sandbox="" style="position:fixed;inset:0;width:100%;height:100%;border:0"></iframe>')
            page.locator('iframe').evaluate('(e,doc)=>e.srcdoc=doc',d['preview'])
            frame=page.frames[1]
            frame.wait_for_selector('body')
            frame.evaluate('()=>Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,2500))])')
            page.wait_for_timeout(120)
            stats=frame.evaluate('''()=>({width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,height:document.body.scrollHeight,headings:document.querySelectorAll('h1,h2,h3').length,rawMarkdown:(document.body.innerText.match(/(?:^|\\n)\\s*(?:#{1,6} |>[ !]|\\| ?---)|\\[\\[|```/g)||[]).length,background:getComputedStyle(document.querySelector('.markdown-preview-view')).backgroundColor,text:document.body.innerText.slice(0,180)})''')
            page.screenshot(path=str(dest/f'{i:02}-desktop.png'))
            frame.evaluate('window.scrollTo(0,document.body.scrollHeight/2)')
            page.screenshot(path=str(dest/f'{i:02}-detail.png'))
            page.set_viewport_size({'width':390,'height':844})
            frame.evaluate('window.scrollTo(0,0)')
            stats['mobileOverflow']=frame.evaluate('document.documentElement.scrollWidth-innerWidth')
            page.screenshot(path=str(dest/f'{i:02}-mobile.png'))
            page.set_viewport_size({'width':1280,'height':900})
            diagnostics.append({'index':i,'key':d['key'],**stats})
        for kind in ('desktop','mobile','detail'):
            for start in range(0,len(records),4):
                cards=[]
                for i in range(start,min(start+4,len(records))):
                    data=base64.b64encode((dest/f'{i:02}-{kind}.png').read_bytes()).decode()
                    cards.append(f'<section><h2>{i+1:02} {html.escape(records[i]["key"])}</h2><img src="data:image/png;base64,{data}"></section>')
                page.set_viewport_size({'width':1440,'height':1100})
                page.set_content('<style>body{margin:0;background:#d9dede;font:14px system-ui;display:grid;grid-template-columns:1fr 1fr;gap:10px}section{height:540px;background:#fff;overflow:hidden}h2{font-size:16px;margin:10px}img{width:100%;height:490px;object-fit:contain;object-position:top;background:#f6f6f6}</style>'+''.join(cards))
                page.screenshot(path=str(dest/f'contact-{kind}-{start//4}.png'))
        browser.close()
    (dest/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
    print(json.dumps([{k:v for k,v in r.items() if k!='text'} for r in diagnostics],indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase');run(parser.parse_args().phase)
