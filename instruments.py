"""Source-backed instrument routing and isolated, non-executable vault previews."""
import html
import base64
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / '.vendor'))
import markdown
from bs4 import BeautifulSoup

# These are navigation relationships, not claims about measured performance.
ROUTES = {
    'Atlas of the Heart': ('Name the emotion before interpreting it', [3,4], ['interior']),
    'Axis Mundi Cockpit': ('Choose the right level of attention', [1,2], []),
    'Chronos and Kairos': ('See the time available, then choose its use', [1,3,5], []),
    'First Contact Board': ('Recruitment pipeline · archived 2026; open the successor in Obsidian', [2,3,5], ['people']),
    'Hall of Faces': ('Find an archetype for the situation', [1,2], ['interior','muses']),
    'Kalpa Corridor': ('Place the present in historical context', [2,3], ['muses']),
    'Kiroshi Optics': ('Examine capacity and recovery · verify sensor freshness', [3,4,5], ['body']),
    'Mount Meru': ('Consult the pantheon of meaning', [1,2], ['interior','muses']),
    "Penelope’s Loom": ('Follow recurring threads and open loops', [3,4,5], ['interior','muses']),
    'R0 Dashboard': ('Return to the operating overview', [2,3,5], []),
    'SOUL Codex': ('Hold values, tensions, and aliveness together', [1,3], ['interior']),
    "Sanjaya’s Chronicle": ('Trace decisions back to the meeting record', [3,4,5], ['people','experience']),
    'Saptarishi Star Chart': ('Bring a council of perspectives to the question', [1,2], ['interior','muses']),
    'Sheikah Slate': ('Navigate the department and its commitments', [2,3,4,5], ['people','access','quality','experience','financial']),
    'The 34 Banners': ('Design around strengths and blind spots', [1,2], ['interior','people']),
    'The Arch': ('Choose a framework and test its application', [2,4,5], []),
    'The Bestiary Grid': ('Encode and retrieve the number-memory palace', [2], ['muses']),
    'The Dojo Wall': ('Move from a problem to an experiment', [4,5], ['body','people','access','quality','experience','financial']),
    'The Forge Floor': ('Inspect the work system and its queues', [4,5], ['people','access','quality','experience','financial']),
    'The Garden': ('Observe the record of lived experience', [3,4], ['interior']),
    'The Grove': ('Connect philosophy with practice', [1,2], ['muses','interior']),
    'The Holodeck Gallery': ('Enter the creative memory palace', [1,2], ['muses']),
    'The Latticework': ('Compare mental models before choosing a strategy', [2,4], []),
    'The Long Hall': ('Recover the institutional context behind today', [2,3], ['people','access','quality','experience','financial']),
    'The Middle Way': ('Hold productive tensions without collapsing them', [1,2], []),
    'The Orrery': ('See how the maps of meaning connect', [2], ['muses']),
    'The Shield Wall': ('Choose the support needed to execute', [2,5], []),
    'The Triskelion Helm': ('Observe the inner state before acting', [3,4], ['interior']),
}

def instrument(path, meta, body, vault):
    # Normalize typographic apostrophes without weakening coverage checks.
    key = next((k for k in ROUTES if k.replace('’', "'") == path.stem.replace('’', "'")), None)
    if key is None:
        raise ValueError(f'Unmapped dashboard: {path.name}; assign its focus and domain relationships')
    purpose, levels, domains = ROUTES[key]
    runtime = len(re.findall(r'```(?:dataviewjs|dataview)|!\[\[[^\]]+\.base', body))
    # Do not execute Obsidian queries or scripts in the web export.
    # Render Markdown before sanitizing HTML. Preserve native dashboard HTML verbatim.
    def callout(match):
        title = html.escape(match[2] or match[1].split('|')[0].title())
        content = re.sub(r'^> ?', '', match[3], flags=re.M)
        return '\n<section class="vault-callout" markdown="1"><h2>'+title+'</h2>\n\n'+content+'\n</section>\n'
    body = re.sub(r'^>\s*\[!([^\]]+)\][+-]?\s*([^\n]*)\n((?:>[^\n]*(?:\n|$))*)', callout, body, flags=re.M)
    body = re.sub(r'^[ \t>]*```(?:dataviewjs|dataview)[^\n]*\n[\s\S]*?^[ \t>]*```', '\n\n<details class="runtime-note"><summary>Obsidian live view · open in source</summary><p>This section runs in the canonical note. It is not a live web reading.</p></details>\n\n', body, flags=re.M)
    def source_embed(match):
        parts=match[1].split('|')
        filename=parts[0]
        title=parts[-1] if len(parts)>1 and not re.fullmatch(r'\d+(?:x\d+)?',parts[-1]) else Path(filename).stem
        if Path(filename).suffix.lower() in {'.png','.jpg','.jpeg','.webp'}:
            candidates=[vault/filename] if (vault/filename).is_file() else list(vault.rglob(Path(filename).name))
            for candidate in candidates:
                if candidate.resolve().is_relative_to(vault.resolve()) and candidate.is_file() and candidate.stat().st_size<500_000:
                    mime='jpeg' if candidate.suffix.lower() in {'.jpg','.jpeg'} else candidate.suffix[1:].lower()
                    data=base64.b64encode(candidate.read_bytes()).decode()
                    return '<figure class="source-image"><img alt="'+html.escape(title,quote=True)+'" src="data:image/'+mime+';base64,'+data+'"><figcaption>'+html.escape(title)+'</figcaption></figure>'
        return '<div class="source-embed"><span>Linked source</span><b>'+html.escape(title)+'</b><small>Open the canonical note to explore this embedded view.</small></div>'
    body = re.sub(r'!\[\[([^\]]+)\]\]', source_embed, body)
    body = re.sub(r'\[\[([^\]]+)\]\]', lambda m:'<a class="internal-link" title="Vault reference">'+html.escape(m[1].split('|')[-1])+'</a>', body)
    body = re.sub(r'^>\s*\[!([^\]]+)\][+-]?\s*(.*)$', lambda m:'> **'+(m[2] or m[1].title())+'**',body,flags=re.M)
    soup = BeautifulSoup(markdown.markdown(body, extensions=['tables','fenced_code','sane_lists','md_in_html']), 'html.parser')
    zones=soup.select_one('.lh-zones')
    hall=soup.select_one('.lh-map')
    if zones and hall:
        hall.insert(0,zones.extract())
    for panel in soup.select('details.lw-domain')[1:]:
        panel.attrs.pop('open',None)
    for sky in soup.select('.sr-sky'):
        wrapper=soup.new_tag('div',attrs={'class':'sky-scroll'})
        sky.wrap(wrapper)
    for region in soup.select('.lh-map, .bestiary-wrap, .board-wall, .sky-scroll'):
        region['tabindex']='0'
        region['role']='region'
        region['aria-label']='Scrollable visual map'
        cue=soup.new_tag('p',attrs={'class':'scroll-cue'})
        cue.string='Explore across → Scroll horizontally; keyboard arrows work when the map is focused.'
        region.insert_before(cue)
    # Give source maintenance prose and backlink indexes a quiet, explicit home.
    source_notes=[]
    for p in list(soup.find_all('p',recursive=False)):
        if re.search(r'best viewed|snippet|Settings\s*→|Reading mode',p.get_text(),re.I):
            source_notes.append(str(p.extract()))
    for heading in list(soup.find_all(['h2','h3'],recursive=False)):
        if heading.get_text().strip().lower()=='backlinks':
            for sibling in list(heading.next_siblings):
                source_notes.append(str(sibling.extract()))
            heading.decompose()
    if source_notes:
        disclosure=BeautifulSoup('<details class="source-notes"><summary>Source notes and references</summary>'+''.join(source_notes)+'</details>','html.parser')
        soup.append(disclosure)
    today = soup.select_one('.ck-panel--today')
    glance = today.get_text(' ', strip=True) if today else ''
    if key == 'Chronos and Kairos' and soup.select_one('.ck-app'):
        # The surrounding Markdown is maintenance documentation, not dashboard UI.
        soup = BeautifulSoup(str(soup.select_one('.ck-app')), 'html.parser')
    for el in soup.find_all(['script','iframe','object','embed','form','link','meta','base']):
        el.decompose()
    for el in soup.find_all(True):
        for attr in list(el.attrs):
            if el.name=='img' and attr=='src' and re.fullmatch(r'data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+',str(el[attr])):
                continue
            if attr.lower().startswith('on') or attr in {'src','srcset','href','action','formaction','srcdoc'}:
                del el[attr]
    snippet = str(meta.get('snippet', 'r0-dashboard' if key == 'R0 Dashboard' else '')).removesuffix('.css')
    csspath = vault / '.obsidian/snippets' / (snippet + '.css')
    css = csspath.read_text() if snippet and csspath.is_file() else ''
    # Only the source's Google Fonts stylesheets are allowed, never arbitrary imports.
    imports=[]
    def font_import(match):
        if re.search(r'https://fonts\.googleapis\.com/css[?2]',match[0]): imports.append(match[0])
        return ''
    css = re.sub(r'''@import\s+(?:url\([^)]*\)|"[^"]*"|'[^']*')[^;]*;''', font_import, css, flags=re.I)
    css = re.sub(r'url\(([^)]*)\)', lambda m: m[0] if m[1].strip(' \"\'').startswith('#') else 'none', css, flags=re.I)
    if key == 'Chronos and Kairos':
        css += '\n.ck-app{margin:0!important}.ck-app .ck-month-label{fill:#d8d2c4}.ck-app .ck-season-label{fill:#b8b09e}'
    css = css.replace('</', '<\\/')
    classes = meta.get('cssclasses', [])
    if isinstance(classes, str): classes = [classes]
    hostclasses=html.escape(' '.join(classes),quote=True)
    foundation=(Path(__file__).resolve().parent/'instrument-base.css').read_text()
    preview = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" '
        'content="default-src \'none\'; style-src \'unsafe-inline\' https://fonts.googleapis.com; img-src data:; font-src https://fonts.gstatic.com; form-action \'none\'">'
        '<style>'+''.join(imports)+foundation+css+'\n'+(Path(__file__).resolve().parent/'instrument-polish.css').read_text()+'</style>'
        '<body class="theme-dark"><main class="markdown-preview-view markdown-rendered '+hostclasses+'"><div class="markdown-preview-sizer markdown-preview-section">'+str(soup)+'</div></main></body>')
    return {'key': key, 'purpose': purpose, 'levels': levels, 'domains': domains,
            'runtimeBlocks': runtime, 'archived': key == 'First Contact Board', 'preview': preview,
            'glance': glance,
            'successor': 'obsidian://open?vault=_R0&file=First%20Contact%20Board%202027' if key == 'First Contact Board' else ''}
