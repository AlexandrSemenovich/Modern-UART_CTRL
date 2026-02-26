#!/usr/bin/env bash
set -euo pipefail

# Simple Linux build script for Modern UART Control.
# Usage: bash packaging/build_linux.sh

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

VENV="$ROOT/venv"
if [[ ! -d "$VENV" ]]; then
    echo "[ERROR] Virtual environment not found at $VENV"
    exit 1
fi

source "$VENV/bin/activate"
pyinstaller --clean --noconfirm packaging/OrbSterm.spec

echo "\nBuild finished. Dist folder: $ROOT/dist"
