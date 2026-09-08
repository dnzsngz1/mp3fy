@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
chcp 65001 >nul
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%main.py" %*
) else (
    python "%SCRIPT_DIR%main.py" %*
)
endlocal
