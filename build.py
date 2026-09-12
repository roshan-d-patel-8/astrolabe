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
  python3 build.py --push     # build + git commit + push
  python3 build.py --mint     # print the magic link (no build)
"""
import argparse, base64, hashlib, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PBKDF2_ITERS = 310000  # must match template.html
SITE_URL = "https://roshan-d-patel-8.github.io/astrolabe/"
REL = "Artificial Intelligence/Executive Assistant/The Astrolabe.html"
CLAUDE_URL = "https://claude.ai/code/artifact/a891ef55-a02f-4c66-b006-f77d9be28e02"


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
(() => {
  const KEY = 'astrolabe-interview';
  const state = $('#dbstate');
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
    const lines = QS.map((q, i) => { const r = all[q.id]; return (i+1) + '. ' + q.t + ': ' + (r && r.answer ? r.answer.trim() : '(blank)'); });
    const text = 'Astrolabe interview answers · copied ' + new Date().toISOString().slice(0,10) + '\n' + lines.join('\n');
    try { await navigator.clipboard.writeText(text); cn.textContent = 'Copied ' + QS.filter(q => all[q.id] && all[q.id].answer).length + ' of 14 answers.'; }
    catch (e) { window.prompt('Copy these answers:', text); }
  };
  document.getElementById('lockPage').onclick = () => {
    try { localStorage.removeItem('ast-pass'); sessionStorage.removeItem('ast-pass'); } catch (e) {}
    history.replaceState(null, '', location.pathname + location.search);
    location.reload();
  };
})();
</script>"""


def build_page(src_html):
    # The vault file is body content that starts with <title>; wrap into a full document.
    body = re.sub(r"^\s*<title>[^<]*</title>\s*", "", src_html, count=1)
    i = body.find(PERSIST_MARK)
    assert i >= 0, "persistence marker not found in source; refusing to ship the claude-db block"
    j = body.rfind("</script>")
    assert j > i, "script close not found"
    body = body[:i] + PERSIST_NEW.replace("__CLAUDE_URL__", CLAUDE_URL) + body[j + len("</script>"):]
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
    ap.add_argument("--mint", action="store_true", help="print the magic link and exit")
    a = ap.parse_args()
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
        import datetime
        git_push(f"astrolabe: rebuild {datetime.date.today().isoformat()}")


if __name__ == "__main__":
    main()
