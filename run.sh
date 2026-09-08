#!/usr/bin/env bash
# ==============================================================================
# MP3fy - Linux CLI Starter Script
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Ensure environment is installed
if [ ! -d "$DIR/.venv" ]; then
    echo "[*] MP3fy ortamı bulunamadı, otomatik kurulum başlatılıyor..."
    bash "$DIR/install.sh"
    INSTALL_EXIT=$?
    if [ $INSTALL_EXIT -ne 0 ]; then
        echo "[!] Hata: Kurulum başarısız oldu (Çıkış kodu: $INSTALL_EXIT)." >&2
        exit $INSTALL_EXIT
    fi
fi

if [ -f "$DIR/.venv/bin/python3" ]; then
    VENV_PY="$DIR/.venv/bin/python3"
elif [ -f "$DIR/.venv/bin/python" ]; then
    VENV_PY="$DIR/.venv/bin/python"
else
    VENV_PY="python3"
fi

"$VENV_PY" "$DIR/main.py" "$@"
EXIT_CODE=$?
exit $EXIT_CODE
