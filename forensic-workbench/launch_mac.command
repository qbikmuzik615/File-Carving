#!/bin/zsh
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3.10+ is required. Install: brew install python'; read -k 1; exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then
  echo 'Python 3.10+ is required. Install: brew install python'; read -k 1; exit 1
fi
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  echo 'FFmpeg/FFprobe missing: install for full video analysis: brew install ffmpeg'
fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM
sleep 2
open http://127.0.0.1:8765 || true
wait "$SERVER_PID"