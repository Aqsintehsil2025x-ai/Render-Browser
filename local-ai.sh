#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="celalkartoglu/turkish-assistant-gemma3-12b-Q4_K_M-GGUF:Q4_K_M"

if ! command -v llama >/dev/null 2>&1; then
  echo "llama command not found. Install the official llama.cpp CLI first (see OFFLINE_AI.md)." >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to serve the local chat page." >&2
  exit 1
fi

echo "Starting local model server on 127.0.0.1:8081."
echo "First run downloads the model; later runs use the local cache."
llama serve -hf "$MODEL" --alias render-gemma3-12b --host 127.0.0.1 --port 8081 --ctx-size 2048 --n-predict 256 --parallel 1 --cors-origins localhost &
MODEL_PID=$!
cleanup(){ kill "$MODEL_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "Starting chat page at http://127.0.0.1:8000"
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$ROOT/ai-ui"
