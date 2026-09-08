try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if (-not $scriptDir) {
    $scriptDir = (Get-Location).Path
}

$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
$mainPy = Join-Path $scriptDir "main.py"

if (Test-Path $pythonExe) {
    & $pythonExe $mainPy @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $mainPy @args
} else {
    Write-Host "[!] Hata: .venv\Scripts\python.exe veya Python bulunamadı." -ForegroundColor Red
    exit 1
}
exit $LASTEXITCODE

