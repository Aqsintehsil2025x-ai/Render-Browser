#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "Tkinter is missing; installing the distro package first…"
  bash "$ROOT/install-desktop.sh"
fi
python3 -c 'import tkinter' >/dev/null 2>&1 || {
  echo "Tkinter installation did not complete. Please install your distro's Tk package." >&2
  exit 1
}
exec python3 "$ROOT/desktop-app.py"
