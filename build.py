#!/usr/bin/env python3
"""
THE ASTROLABE — encrypted GitHub Pages build.

Reads the canonical page from the vault
  Artificial Intelligence/Executive Assistant/The Astrolabe.html
patches the interview persistence (Claude artifact db -> browser localStorage,
plus a "Copy answers" button), AES-256-GCM-encrypts the whole page
(PBKDF2-SHA256, 310k iters — same wire format as conjunction), and injects the
ciphertext into template.html at __PAYLOAD__  ->  index.html.

Passphrase: $ASTROLABE_PASS, else macOS Keychain item `astrolabe-site`
  security add-generic-password -a "$USER" -s astrolabe-site -w '<pass>'

  python3 build.py            # build index.html
  python3 build.py --preview  # write a local plaintext preview for QA
  python3 build.py --push     # build + git commit + push
  python3 build.py --mint     # print the magic link (no build)
"""
import argparse, base64, datetime, hashlib, html, json, os, re, subprocess, sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PBKDF2_ITERS = 310000  # must match template.html
SITE_URL = "https://roshan-d-patel-8.github.io/astrolabe/"
REL = "Artificial Intelligence/Executive Assistant/The Astrolabe.html"
CLAUDE_URL = "https://claude.ai/code/artifact/a891ef55-a02f-4c66-b006-f77d9be28e02"
VAULT = Path.home() / "Vaults/_R0"
TASKS = VAULT / "TaskNotes/Tasks"
DASHBOARDS = VAULT / "Dashboards"


def find_source():
    env = os.environ.get("ASTROLABE_SRC")
    cands = [Path(env)] if env else []
    home = Path.home()
    cands += [home / "Vaults/_R0" / REL, home / "_R0" / REL]  # MBP, mini
    for c in cands:
        if c.is_file():
            return c
    sys.exit("[BUILD] source not found; set $ASTROLABE_SRC")


PERSIST_MARK = "// Interview persistence via the page's database."
PERSIST_NEW = r"""// Interview persistence for the GitHub copy: browser localStorage on this device,
// plus "Copy answers" so they can be pasted back to Claude. The claude.ai copy keeps the shared db.
window.addEventListener('astrolabe-ready', () => {
  const KEY = 'astrolabe-interview';
  const state = document.querySelector('#dbstate');
  if (!state) return;
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } };
  const store = (o) => { try { localStorage.setItem(KEY, JSON.stringify(o)); return true; } catch (e) { return false; } };
  let ok = true; try { localStorage.setItem(KEY + ':t', '1'); localStorage.removeItem(KEY + ':t'); } catch (e) { ok = false; }
  state.innerHTML = ok
    ? 'This copy remembers answers on <b>this device only</b>. Press <b>Copy answers</b> and paste them to Claude, or answer in the <a href="__CLAUDE_URL__">claude.ai copy</a>, which has shared memory. · <button class="save" id="copyAns">Copy answers</button> <button class="trace" id="lockPage">Lock this page</button><span id="copyNote" style="margin-left:8px"></span>'
    : 'This browser blocks storage: answers typed here will not persist. Use the <a href="__CLAUDE_URL__">claude.ai copy</a>. · <button class="trace" id="lockPage">Lock this page</button>';
  const saved = load();
  document.querySelectorAll('textarea[data-q]').forEach(a => {
    const q = a.dataset.q, btn = document.querySelector('.save[data-q="' + q + '"]'), note = document.querySelector('.saved[data-q="' + q + '"]');
    if (saved[q] && typeof saved[q].answer === 'string') { a.value = saved[q].answer; if (note && saved[q].updatedAt) note.textContent = 'Saved ' + new Date(saved[q].updatedAt).toLocaleDateString(); }
    a.addEventListener('input', () => { btn.disabled = false; });
    btn.disabled = !ok;
    btn.onclick = () => {
      const all = load(); all[q] = { answer: a.value, updatedAt: new Date().toISOString() };
      if (store(all)) { note.textContent = 'Saved ' + new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}); btn.disabled = true; }
      else note.textContent = 'Could not save on this device.';
    };
  });
  const copyBtn = document.getElementById('copyAns');
  if (copyBtn) copyBtn.onclick = async () => {
    const all = load(); const cn = document.getElementById('copyNote');
    const questions = window.ASTRO_QUESTIONS || [];
    const lines = questions.map((q, i) => { const r = all[q.id]; return (i+1) + '. ' + q.t + ': ' + (r && r.answer ? r.answer.trim() : '(blank)'); });
    const text = 'Astrolabe interview answers · copied ' + new Date().toISOString().slice(0,10) + '\n' + lines.join('\n');
    try { await navigator.clipboard.writeText(text); cn.textContent = 'Copied ' + questions.filter(q => all[q.id] && all[q.id].answer).length + ' of ' + questions.length + ' answers.'; }
    catch (e) { window.prompt('Copy these answers:', text); }
  };
  document.getElementById('lockPage').onclick = () => {
    try { localStorage.removeItem('ast-pass'); sessionStorage.removeItem('ast-pass'); } catch (e) {}
    history.replaceState(null, '', location.pathname + location.search);
    location.reload();
  };
});
</script>"""


def _frontmatter(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}, text
    try:
        _, raw, body = text.split("---", 2)
        return yaml.safe_load(raw) or {}, body.strip()
    except (ValueError, yaml.YAMLError):
        return {}, text


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _obsidian_uri(relative_path):
    from urllib.parse import quote
    return "obsidian://open?vault=_R0&file=" + quote(str(relative_path.with_suffix("")), safe="")


def task_snapshot():
    records = []
    for path in sorted(TASKS.glob("*.md")):
        meta, body = _frontmatter(path)
        status = str(meta.get("status", "gate")).lower()
        if status not in {"gate", "forge", "flow"}:
            continue
        realms = [str(v) for v in _as_list(meta.get("realm"))]
        tags = [str(v).lstrip("#") for v in _as_list(meta.get("tags"))]
        if any("Hathi" in value for value in realms) or {"hathi-domain", "migrated-to-reminders"} & set(tags):
            continue
        title = path.stem
        excerpt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\[\[[^\]]+\]\]", " ", body)).strip()[:220]
        records.append({
            "id": hashlib.sha1(str(path.relative_to(VAULT)).encode()).hexdigest()[:10],
            "title": title,
            "status": status,
            "priority": str(meta.get("priority", "normal")).lower(),
            "type": str(meta.get("type", "task")).lower(),
            "scheduled": str(meta.get("scheduled", "")),
            "due": str(meta.get("due", "")),
            "realms": realms,
            "tags": tags,
            "parentProject": str(meta.get("parentProject", "")),
            "excerpt": excerpt,
            "uri": _obsidian_uri(path.relative_to(VAULT)),
        })
    priority = {"high": 0, "normal": 1, "low": 2, "none": 3}
    records.sort(key=lambda x: ({"flow": 0, "forge": 1, "gate": 2}[x["status"]], priority.get(x["priority"], 3), x["scheduled"] or "9999", x["title"].lower()))
    return records


def dashboard_snapshot():
    records = []
    candidates = sorted(DASHBOARDS.glob("*.md"))
    root_dashboard = VAULT / "R0 Dashboard.md"
    if root_dashboard.is_file():
        candidates.append(root_dashboard)
    for path in candidates:
        meta, body = _frontmatter(path)
        heading = re.search(r"^#\s+(.+)$", body, re.M)
        title = re.sub(r"^[^\w]+\s*", "", heading.group(1)).strip() if heading else path.stem
        intro = re.search(r"^\*([^*]+)\*", body, re.M)
        tags = [str(v).lstrip("#") for v in _as_list(meta.get("tags"))]
        # The Bridge is the registry around the fleet rather than a fleet hull.
        # Older veterans (notably R0 Dashboard) predate the dashboard tag.
        if path.stem == "The Bridge":
            continue
        records.append({
            "title": title,
            "refreshed": str(meta.get("refreshed", "")),
            "tags": tags,
            "snippet": str(meta.get("snippet", "")),
            "description": html.unescape(re.sub(r"<[^>]+>|\[\[|\]\]", "", intro.group(1))).strip() if intro else "Vault dashboard",
            "uri": _obsidian_uri(path.relative_to(VAULT)),
        })
    return records


def vault_snapshot():
    tasks = task_snapshot()
    dashboards = dashboard_snapshot()
    counts = {stage: sum(1 for task in tasks if task["status"] == stage) for stage in ("gate", "forge", "flow")}
    return {
        "generatedAt": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
        "tasks": tasks,
        "taskCounts": counts,
        "dashboards": dashboards,
        "source": "TaskNotes/Views/kanban-default.base + Dashboards/",
    }


def build_page(src_html):
    # The vault file is body content that starts with <title>; wrap into a full document.
    body = re.sub(r"^\s*<title>[^<]*</title>\s*", "", src_html, count=1)
    i = body.find(PERSIST_MARK)
    assert i >= 0, "persistence marker not found in source; refusing to ship the claude-db block"
    j = body.rfind("</script>")
    assert j > i, "script close not found"
    body = body[:i] + PERSIST_NEW.replace("__CLAUDE_URL__", CLAUDE_URL) + body[j + len("</script>"):]
    snapshot = json.dumps(vault_snapshot(), ensure_ascii=False).replace("</", "<\\/")
    assert "__VAULT_SNAPSHOT__" in body, "vault snapshot marker not found"
    body = body.replace("__VAULT_SNAPSHOT__", snapshot)
    body = body.replace("__BUILD_DATE__", datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"))
    assert "window.claude" not in body, "claude runtime reference survived the patch"
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>The Astrolabe</title></head><body>' + body + '</body></html>')


def encrypt(plaintext, passphrase):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, nonce = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, PBKDF2_ITERS, 32)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(salt + nonce + ct).decode()


def resolve_pass():
    p = os.environ.get("ASTROLABE_PASS")
    if p:
        return p
    r = subprocess.run(["security", "find-generic-password", "-s", "astrolabe-site", "-w"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    sys.exit("[BUILD] no passphrase: set $ASTROLABE_PASS or Keychain item astrolabe-site")


def magic_link(p):
    return SITE_URL + "#k=" + base64.urlsafe_b64encode(p.encode()).decode().rstrip("=")


def git_push(msg):
    def run(*a): subprocess.run(["git", "-C", str(HERE), *a], check=True)
    run("add", "index.html")
    if subprocess.run(["git", "-C", str(HERE), "diff", "--cached", "--quiet"]).returncode == 0:
        print("[BUILD] nothing to commit"); return
    run("commit", "-m", msg); run("push"); run("fetch", "origin")
    subprocess.run(["git", "-C", str(HERE), "diff", "--quiet", "HEAD", "origin/main", "--", "index.html"], check=True)
    print("[BUILD] pushed and verified against origin/main")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--preview", action="store_true", help="write .preview.html without encryption")
    ap.add_argument("--mint", action="store_true", help="print the magic link and exit")
    a = ap.parse_args()
    if a.preview:
        src = find_source()
        page = build_page(src.read_text(encoding="utf-8"))
        (HERE / ".preview.html").write_text(page, encoding="utf-8")
        print(f"[PREVIEW] {src} -> .preview.html ({len(page):,} bytes)")
        return
    p = resolve_pass()
    if a.mint:
        print(magic_link(p)); return
    src = find_source()
    page = build_page(src.read_text(encoding="utf-8"))
    tpl = (HERE / "template.html").read_text(encoding="utf-8")
    assert "__PAYLOAD__" in tpl
    out = tpl.replace("__PAYLOAD__", encrypt(page, p))
    (HERE / "index.html").write_text(out, encoding="utf-8")
    print(f"[BUILD] {src} -> index.html ({len(out):,} bytes, plaintext {len(page):,})")
    if a.push:
        git_push(f"astrolabe: rebuild {datetime.date.today().isoformat()}")


if __name__ == "__main__":
    main()
