#!/usr/bin/env bash
# ==============================================================================
# MP3fy - Linux CLI Starter Script
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Ensure environment is installed
if [ ! -d "$DIR/.venv" ]; then
    echo "[*] MP3fy ortamı bulunamadı, otomatik kurulum başlatılıyor..."
    ./install.sh
fi

exec "$DIR/.venv/bin/python3" "$DIR/main.py" "$@"
