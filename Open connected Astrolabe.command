#!/bin/zsh
set -eu
cd "$(dirname "$0")"
if curl --silent --fail --max-time 1 http://127.0.0.1:8795/api/health | grep -q '"service": "astrolabe"'; then
  open http://127.0.0.1:8795/
  exit 0
fi
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 companion.py &
astrolabe_pid=$!
trap 'kill "$astrolabe_pid" 2>/dev/null || true' EXIT
for attempt in {1..30}; do
  if curl --silent --fail --max-time 1 http://127.0.0.1:8795/api/health | grep -q '"service": "astrolabe"'; then
    open http://127.0.0.1:8795/
    break
  fi
  sleep 0.2
done
wait "$astrolabe_pid"
