#!/bin/zsh
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then echo 'Python 3 is required'; read -k 1; exit 1; fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python3 -m pip install -r requirements.txt
open http://127.0.0.1:8765 || true
exec python3 app.py