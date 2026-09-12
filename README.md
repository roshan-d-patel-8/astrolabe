# The Astrolabe

Polaris on one plate: mission, vision, values, ten pillars, current condition, the bowling chart, and the week's bench, at seven altitudes (Focus Mundi F0–F6) across two wings (Hathi · home, Skoll · work).

This repo holds only ciphertext plus the unlock shell. The page is AES-256-GCM encrypted (PBKDF2-SHA256, 310k iterations) and decrypts in the browser; nothing leaves the page. The canonical source lives in the Obsidian vault and is rebuilt with `build.py`. Interview answers on this copy persist in the device's browser storage; the claude.ai copy holds the shared memory.
