#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_tkinter() {
  if python3 -c 'import tkinter' >/dev/null 2>&1; then
    echo "Tkinter is already installed."; return 0
  fi
  echo "Tkinter is missing. Installing the system package…"
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required to install Tkinter. Install python3-tk with your package manager." >&2; exit 1
  fi
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3-tk
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3-tkinter
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm tk
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper --non-interactive install python3-tk
  else
    echo "Unsupported package manager. Install Tkinter for Python 3 manually." >&2; exit 1
  fi
  python3 -c 'import tkinter' >/dev/null
}

install_tkinter
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps"
install -m 644 "$ROOT/xyrin-flower.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/xyrin-flower.svg"
cat > "$HOME/.local/share/applications/render-browser-local-ai.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Xyrin Flower - Render AI
Comment=Xyrin Flower neural desktop and offline AI chat
Exec=$ROOT/run-desktop.sh
Icon=$HOME/.local/share/icons/hicolor/scalable/apps/xyrin-flower.svg
Terminal=false
Categories=Utility;Development;
StartupNotify=true
EOF
chmod +x "$ROOT/run-desktop.sh"
chmod +x "$HOME/.local/share/applications/render-browser-local-ai.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi
echo "Installed in your desktop application menu: Xyrin Flower - Render AI"
echo "Icon: $HOME/.local/share/icons/hicolor/scalable/apps/xyrin-flower.svg"
