#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/render-browser-local-ai.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Render Browser Local AI
Comment=Chat with a local offline language model
Exec=$ROOT/run-desktop.sh
Icon=applications-internet
Terminal=false
Categories=Utility;Development;
StartupNotify=true
EOF
chmod +x "$ROOT/run-desktop.sh"
chmod +x "$HOME/.local/share/applications/render-browser-local-ai.desktop"
echo "Installed in your desktop application menu: Render Browser Local AI"
