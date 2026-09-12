"""Source-backed instrument routing and isolated, non-executable vault previews."""
import html
import re
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
    body = re.sub(r'```[\s\S]*?```', '<p class="runtime-note">Query/code block available in the canonical Obsidian note.</p>', body)
    body = re.sub(r'!\[\[[^\]]+\]\]', '<p class="runtime-note">Embedded vault content available in Obsidian.</p>', body)
    body = re.sub(r'\[\[([^\]]+)\]\]', lambda m: html.escape(m[1].split('|')[-1]), body)
    soup = BeautifulSoup(body, 'html.parser')
    today = soup.select_one('.ck-panel--today')
    glance = today.get_text(' ', strip=True) if today else ''
    if key == 'Chronos and Kairos' and soup.select_one('.ck-app'):
        # The surrounding Markdown is maintenance documentation, not dashboard UI.
        soup = BeautifulSoup(str(soup.select_one('.ck-app')), 'html.parser')
    for el in soup.find_all(['script','iframe','object','embed','form','link','meta','base']):
        el.decompose()
    for el in soup.find_all(True):
        for attr in list(el.attrs):
            if attr.lower().startswith('on') or attr in {'src','srcset','href','action','formaction','srcdoc'}:
                del el[attr]
    snippet = str(meta.get('snippet', 'r0-dashboard' if key == 'R0 Dashboard' else '')).removesuffix('.css')
    csspath = vault / '.obsidian/snippets' / (snippet + '.css')
    css = csspath.read_text() if snippet and csspath.is_file() else ''
    css = re.sub(r'''@import\s+(?:url\([^)]*\)|"[^"]*"|'[^']*')[^;]*;''', '', css, flags=re.I)
    css = re.sub(r'url\(([^)]*)\)', lambda m: m[0] if m[1].strip(' \"\'').startswith('#') else 'none', css, flags=re.I)
    if key == 'Chronos and Kairos':
        css += '\n.ck-app{margin:0!important}.ck-app .ck-month-label{fill:#d8d2c4}.ck-app .ck-season-label{fill:#b8b09e}'
    css = css.replace('</', '<\\/')
    classes = meta.get('cssclasses', [])
    if isinstance(classes, str): classes = [classes]
    preview = ('<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" '
        'content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; font-src \'none\'; form-action \'none\'">'
        '<style>:root{--background-primary:#102329;--background-secondary:#182f35;--text-normal:#e3ede7;--text-muted:#a5b9bb;--text-accent:#87c7cd;--interactive-accent:#87c7cd;}body{margin:0;padding:24px;background:#102329;color:#e3ede7;font:15px/1.6 system-ui;overflow-wrap:anywhere}img{max-width:100%}.runtime-note{border:1px dashed #789;padding:12px}'+css+'</style>'
        '<body class="theme-dark '+html.escape(' '.join(classes), quote=True)+'"><div class="markdown-preview-view markdown-rendered">'+str(soup)+'</div></body>')
    return {'key': key, 'purpose': purpose, 'levels': levels, 'domains': domains,
            'runtimeBlocks': runtime, 'archived': key == 'First Contact Board', 'preview': preview,
            'glance': glance,
            'successor': 'obsidian://open?vault=_R0&file=First%20Contact%20Board%202027' if key == 'First Contact Board' else ''}
