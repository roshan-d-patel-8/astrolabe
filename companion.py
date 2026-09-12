#!/usr/bin/env python3
"""Loopback-only TaskNotes companion. No CORS, tunnels, or public write endpoint."""
import argparse
import datetime
import hashlib
import json
import re
import secrets
import threading
import os
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml
import build

LOCK = threading.Lock()
FIELDS = {'status', 'priority', 'scheduled', 'due', 'parentProject'}

def update_note(path, changes, revision, vault):
    """Surgical frontmatter changes; keep body and unrelated properties byte-for-byte."""
    raw = path.read_text()
    if hashlib.sha256(path.read_bytes()).hexdigest() != revision:
        raise FileExistsError('The note changed in Obsidian. Reload before saving; your edit was not applied.')
    if not changes or set(changes) - FIELDS:
        raise ValueError('Unsupported or empty change')
    for key, value in changes.items():
        if not isinstance(value, str) or len(value) > 250 or '\n' in value:
            raise ValueError('Invalid field value')
        if key == 'status' and value not in {'gate','forge','flow','done'}:
            raise ValueError('Invalid status')
        if key == 'priority' and value not in {'high','normal','low','none'}:
            raise ValueError('Invalid priority')
        if key in {'scheduled','due'} and value:
            datetime.date.fromisoformat(value)
        if key == 'parentProject' and value and not re.fullmatch(r'\[\[[^\[\]\n]+\]\]', value):
            raise ValueError('Project must be a wikilink')
    match = re.match(r'\A---\n(.*?)\n---(?=\n|$)', raw, re.S)
    if not match: raise ValueError('Missing valid frontmatter; edit this note in Obsidian')
    head = match[1]
    for key, value in changes.items():
        # Refuse multiline fields rather than risk consuming unrelated user content.
        pattern = rf'(?m)^{key}:([^\n]*)$'
        old = re.search(pattern, head)
        if old and not old[1].strip() and re.match(r'\n[ \t]+\S', head[old.end():]):
            raise ValueError(f'Multiline {key} must be edited in Obsidian')
        line = key + ': ' + json.dumps(value, ensure_ascii=False)
        head = re.sub(pattern, lambda _: line, head) if old else head + '\n' + line
    updated = '---\n' + head + '\n---' + raw[match.end():]
    yaml.safe_load(head)
    backup = vault / '.astrolabe-backups'
    backup.mkdir(exist_ok=True, mode=0o700)
    backup_path = backup / (revision + '.md')
    if not backup_path.exists():
        with backup_path.open('x') as file: file.write(raw)
        backup_path.chmod(0o600)
    # A second check closes the normal read/validate race with external edits.
    if hashlib.sha256(path.read_bytes()).hexdigest() != revision:
        raise FileExistsError('Concurrent note change; reload before saving')
    fd, temporary = tempfile.mkstemp(prefix='.astrolabe-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            file.write(updated); file.flush(); os.fsync(file.fileno())
        os.chmod(temporary, path.stat().st_mode)
        if hashlib.sha256(path.read_bytes()).hexdigest() != revision:
            raise FileExistsError('Concurrent note change; reload before saving')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def create_note(data, vault):
    title = data.get('title', '').strip()
    kind = data.get('type', 'task')
    if not title or len(title) > 160 or re.search(r'[/\\:\x00-\x1f\[\]#]', title) or kind not in {'task','project'}:
        raise ValueError('Use a clear title without path separators or markup')
    today = datetime.datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
    name = title + ('' if '(init.' in title else f' (init. {today})')
    path = vault / 'TaskNotes/Tasks' / (name + '.md')
    realm = data.get('realm', 'Skoll')
    if realm not in {'Skoll','Skoll - People and Culture','Skoll - Care Availability','Skoll - Quality and Safety','Skoll - Care Experience','Skoll - Financial Health'}:
        raise ValueError('Choose an available Skoll domain')
    meta = {'type': kind, 'status': 'gate', 'priority': 'normal', 'tags': ['task', 'ClaudeAI'],
            'dateCreated': today, 'parentProject': '', 'realm': '[['+realm+']]'}
    with path.open('x') as file:
        file.write('---\n' + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) +
                   '---\n\n' + ('- [ ] ' if kind == 'task' else '') + title +
                   '\n\n## Backlinks\n\n[[F5]]\n[[Focus - Axis Mundi]]\n')

def serve(port=8795):
    token = secrets.token_urlsafe(32)
    origin = f'http://127.0.0.1:{port}'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # Never log private titles or tokens.
        def send(self, status, payload, kind='application/json'):
            blob = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.end_headers(); self.wfile.write(blob)
        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{port}'
        def do_GET(self):
            if not self.valid_host(): return self.send(403, {'error':'Invalid host'})
            route = self.path.split('?')[0]
            if route == '/api/health':
                return self.send(200, {'service':'astrolabe','version':'4.0.0'})
            if route == '/':
                page = build.build_page(build.find_source().read_text())
                config = '<script>window.ASTRO_CONNECTION=' + json.dumps({'token':token}) + ';</script>'
                return self.send(200, page.replace('<head>', '<head>'+config, 1), 'text/html')
            if route == '/api/snapshot':
                if self.headers.get('X-Astrolabe-Token') != token:
                    return self.send(403, {'error':'Session required'})
                return self.send(200, build.vault_snapshot())
            if route in {'/app.js','/atlas.css'}:
                return self.send(200, (build.HERE / route[1:]).read_text(), 'text/javascript' if route.endswith('.js') else 'text/css')
            return self.send(404, {'error':'Not found'})
        def mutate(self):
            if not self.valid_host() or self.headers.get('Origin') != origin or self.headers.get('X-Astrolabe-Token') != token:
                return self.send(403, {'error':'Same-origin session required'})
            try:
                length = int(self.headers.get('Content-Length','0'))
                if length < 1 or length > 4096: raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(length))
                with LOCK:
                    if self.command == 'POST' and self.path == '/api/tasks':
                        create_note(data, build.VAULT)
                    elif self.command == 'PATCH' and re.fullmatch(r'/api/tasks/[a-f0-9]{10}', self.path):
                        ident = self.path.rsplit('/',1)[-1]
                        path = next((p for p in build.TASKS.glob('*.md') if hashlib.sha1(str(p.relative_to(build.VAULT)).encode()).hexdigest()[:10] == ident), None)
                        if path is None or path.is_symlink(): raise ValueError('Unknown task')
                        if not any(t['id'] == ident for t in build.task_snapshot()): raise ValueError('Task outside active canonical board')
                        update_note(path, data.get('changes',{}), data.get('revision',''), build.VAULT)
                    else: return self.send(404, {'error':'Not found'})
                self.send(200, build.vault_snapshot())
            except FileExistsError as exc: self.send(409, {'error':str(exc)})
            except (ValueError, TypeError, KeyError, yaml.YAMLError) as exc: self.send(400, {'error':str(exc)})
            except Exception: self.send(500, {'error':'Could not save. Check the canonical note before retrying.'})
        do_PATCH = mutate
        do_POST = mutate
    server = ThreadingHTTPServer(('127.0.0.1',port), Handler)
    print(f'Connected Astrolabe: {origin} (this Mac only)', flush=True)
    server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8795)
    serve(parser.parse_args().port)
