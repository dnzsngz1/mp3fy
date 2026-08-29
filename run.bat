@echo off
REM ============================================================================
REM MP3fy - Windows One-Click Starter Script
REM ============================================================================

title MP3fy - Spotify MP3 Indirici
echo ==================================================
echo   MP3fy - Spotify MP3 Indirici ^& Donusturucu
echo ==================================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Hata: Python bulunamadi. Lutfen Python 3 yukleyin ve PATH'e ekleyin.
    pause
    exit /b 1
)

REM Check Virtual Environment
if not exist ".venv" (
    echo [*] Sanal ortam olusturuluyor (.venv)...
    python -m venv .venv
    echo [*] Bagimliliklar yukleniyor...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM Run App
echo [*] Uygulama baslatiliyor...
python main.py %*

pause
