#!/usr/bin/env bash
# ==============================================================================
# MP3fy - Linux / macOS One-Click Starter Script
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================="
echo "🎵 MP3fy - Spotify MP3 İndirici & Dönüştürücü"
echo "=================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Hata: Python 3 bulunamadı. Lütfen Python 3 kurun."
    exit 1
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "[!] Uyarı: ffmpeg sistemde bulunamadı."
    echo "    MP3 dönüştürme için ffmpeg gereklidir."
    echo "    Ubuntu/Debian: sudo apt install ffmpeg"
    echo "    macOS: brew install ffmpeg"
    echo ""
fi

# Check / create virtual environment
if [ ! -d ".venv" ]; then
    echo "[*] Sanal ortam oluşturuluyor (.venv)..."
    python3 -m venv .venv
    echo "[*] Bağımlılıklar yükleniyor..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Launch application
echo "[*] Uygulama başlatılıyor..."
python3 main.py "$@"
