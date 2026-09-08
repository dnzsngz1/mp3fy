#!/usr/bin/env bash
# ==============================================================================
# MP3fy - Linux CLI Kurulum Scripti (Installer)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================="
echo "🎵 MP3fy Linux CLI Kurulumu Başlatılıyor..."
echo "=================================================="

# Python 3 ve Sürüm Kontrolü (>= 3.9)
if ! command -v python3 &> /dev/null; then
    echo "[!] Hata: Python 3 sistemde bulunamadı. Lütfen python3 yükleyin."
    exit 1
fi

PYTHON_BIN=$(command -v python3)
PY_VER=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    echo "[!] Hata: Python 3.9 veya daha yeni bir sürüm gereklidir (Tespit edilen: $PY_VER)."
    exit 1
fi

echo "[+] Python tespit edildi: $PYTHON_BIN (v$PY_VER)"

# FFmpeg Kontrolü
if ! command -v ffmpeg &> /dev/null; then
    if [ -f "$HOME/.local/bin/ffmpeg" ] || [ -f "$HOME/.local/share/ffmpeg/ffmpeg" ]; then
        echo "[+] FFmpeg yerel dizinde bulundu (~/.local/bin/ffmpeg)."
    else
        echo "[!] Uyarı: ffmpeg sistem genelinde bulunamadı."
        echo "    MP3 dönüştürme işlemi için ffmpeg gereklidir."
        echo "    Yüklemek için: sudo apt install ffmpeg"
    fi
else
    echo "[+] FFmpeg hazır: $(command -v ffmpeg)"
fi

# Sanal Ortam (.venv) Kurulumu
if command -v uv &> /dev/null; then
    echo "[*] 'uv' ile hızlı sanal ortam ve paket kurulumu yapılıyor..."
    if [ ! -d ".venv" ]; then
        uv venv .venv
    fi
    uv pip install --python .venv/bin/python -e .
else
    if [ ! -d ".venv" ]; then
        echo "[*] python3 -m venv ile sanal ortam oluşturuluyor..."
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e .
fi

# ~/.local/bin dizinine mp3fy komutunu bağlama
mkdir -p "$HOME/.local/bin"
LAUNCHER="$HOME/.local/bin/mp3fy"

cat << LAUNCHER_EOF > "$LAUNCHER"
#!/usr/bin/env bash
# MP3fy CLI Launcher
PROJECT_DIR="$DIR"
if [ -f "\$PROJECT_DIR/.venv/bin/python" ]; then
    exec "\$PROJECT_DIR/.venv/bin/python" "\$PROJECT_DIR/main.py" "\$@"
elif [ -f "\$PROJECT_DIR/.venv/bin/python3" ]; then
    exec "\$PROJECT_DIR/.venv/bin/python3" "\$PROJECT_DIR/main.py" "\$@"
else
    exec python3 "\$PROJECT_DIR/main.py" "\$@"
fi
LAUNCHER_EOF

chmod +x "$LAUNCHER"
chmod +x "$DIR/main.py"

echo "--------------------------------------------------"
echo "[✓] Kurulum başarıyla tamamlandı!"
echo "[✓] Komut oluşturuldu: $LAUNCHER"
echo ""
echo "Artık terminalde herhangi bir dizindeyken şu komutu çalıştırabilirsiniz:"
echo "    mp3fy"
echo "veya doğrudan parametrelerle:"
echo "    mp3fy <spotify_linki>"
echo "--------------------------------------------------"
