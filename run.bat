@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

if not exist ".venv\Scripts\python.exe" (
    echo [*] MP3fy ortami bulunamadi, kurulum baslatiliyor...
    powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "%~dp0main.py" %*
) else (
    python "%~dp0main.py" %*
)
endlocal & exit /b %ERRORLEVEL%
