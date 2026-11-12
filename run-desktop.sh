#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "Python Tkinter is missing. Install your distro's python3-tk package, then retry." >&2
  exit 1
fi
exec python3 "$ROOT/desktop-app.py"
