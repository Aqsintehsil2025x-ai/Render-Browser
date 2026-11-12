#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "Tkinter is missing. Run bash install-desktop.sh to install it automatically." >&2
  exit 1
fi
exec python3 "$ROOT/desktop-app.py"
