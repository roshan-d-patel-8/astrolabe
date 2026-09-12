"""All mutation tests use a temporary vault. Never edit Roshan's tasks for QA."""
import hashlib
import json
import re
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
import companion
from playwright.sync_api import sync_playwright

def run():
    with tempfile.TemporaryDirectory(prefix='astrolabe-qa-') as directory:
        vault = Path(directory)
        tasks = vault / 'TaskNotes/Tasks'; tasks.mkdir(parents=True)
        (vault / 'Dashboards').mkdir()
        note = tasks / 'Draft a one-paragraph acceptance test.md'
        original = '---\ntype: task\nstatus: gate\npriority: normal\nrealm: "[[Skoll - People and Culture]]"\nparentProject: ""\ncustom: preserve exactly\n---\n\nUser writing **must survive**.\n[[Original backlink]]\n'
        note.write_text(original)
        build.VAULT,build.TASKS,build.DASHBOARDS=vault,tasks,vault/'Dashboards'
        with socket.socket() as s: s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
        threading.Thread(target=companion.serve,args=(port,),daemon=True).start()
        origin=f'http://127.0.0.1:{port}'
        for _ in range(30):
            try: page=urllib.request.urlopen(origin).read().decode(); break
            except OSError: time.sleep(.1)
        token=json.loads(re.search(r'window.ASTRO_CONNECTION=(\{[^<]+\});',page)[1])['token']
        def request(path,method='GET',data=None,headers=None):
            req=urllib.request.Request(origin+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers=headers or {})
            try:
                with urllib.request.urlopen(req) as r: return r.status,json.loads(r.read())
            except urllib.error.HTTPError as e: return e.code,json.loads(e.read())
        headers={'Origin':origin,'X-Astrolabe-Token':token,'Content-Type':'application/json'}
        task=build.task_snapshot()[0]
        payload={'revision':task['revision'],'changes':{'status':'forge','parentProject':'[[QA project]]'}}
        assert request('/api/snapshot')[0]==403
        assert request('/api/snapshot',headers={'Host':'evil.example','X-Astrolabe-Token':token})[0]==403
        assert request('/api/tasks/'+task['id'],'PATCH',payload,{**headers,'Origin':'https://evil.example'})[0]==403
        assert note.read_text()==original
        assert request('/api/tasks/'+task['id'],'PATCH',payload,headers)[0]==200
        assert note.read_text().split('\n---',1)[1]==original.split('\n---',1)[1]
        assert 'custom: preserve exactly' in note.read_text()
        assert (vault/'.astrolabe-backups'/f'{task["revision"]}.md').read_text()==original
        assert request('/api/tasks/'+task['id'],'PATCH',payload,headers)[0]==409
        latest=build.task_snapshot()[0]
        bad={'revision':latest['revision'],'changes':{'status':'erase'}}
        assert request('/api/tasks/'+task['id'],'PATCH',bad,headers)[0]==400
        assert request('/api/tasks','POST',{'title':'../escape','type':'task'},headers)[0]==400
        assert request('/api/tasks','POST',{'title':'QA project','type':'project'},headers)[0]==200
        assert len(build.vault_snapshot()['projects'])==1
        assert len(build.vault_snapshot()['tasks'])==1
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page()
            page.goto(origin,wait_until='networkidle')
            page.locator('[data-altitude="5"]').click()
            page.locator('.task-card').click()
            page.locator('#taskEditor [name="priority"]').select_option('high')
            page.locator('#taskEditor button[type="submit"]').click()
            page.locator('#drawer').wait_for(state='hidden')
            assert build.task_snapshot()[0]['priority']=='high'
            page.locator('.task-card').click()
            # Simulate an Obsidian edit while the form remains open.
            note.write_text(note.read_text()+'\nAnother user-written line.\n')
            page.locator('#taskEditor button[type="submit"]').click()
            page.locator('#editResult').get_by_text(re.compile('changed in Obsidian')).wait_for()
            assert 'Another user-written line.' in note.read_text()
            page.keyboard.press('Escape')
            page.locator('#newWork').click()
            page.locator('#createWork [name="title"]').fill('Verify a specific visible result')
            page.locator('#createWork button').click()
            page.locator('#drawer').wait_for(state='hidden')
            assert len(build.task_snapshot())==2
            browser.close()
        print('PASS: fixture-only browser create/edit; body preservation; revision conflict; backups; invalid values/paths; project separation; origin/token/Host rejection')

if __name__=='__main__':run()
