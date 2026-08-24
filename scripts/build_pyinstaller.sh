#!/usr/bin/env bash
# Build portátil (one-folder). Requer: pip install pyinstaller
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python -m pip install -q pyinstaller Pillow psutil 2>/dev/null || true
pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name ASFDesktop \
  --add-data "ui/icons/png:ui/icons/png" \
  --hidden-import PIL \
  --hidden-import psutil \
  main.py
echo "Artefato: $ROOT/dist/ASFDesktop/"
