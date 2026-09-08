# ==============================================================================
# MP3fy - PowerShell CLI Hızlı Başlatıcı (Starter)
# ==============================================================================

$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) {
    $ProjectDir = (Get-Location).Path
}

# UTF-8 konsol kodlamasını etkinleştir
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$MainPy = Join-Path $ProjectDir "main.py"

# Ortam kontrolü - yoksa otomatik kurulum çalıştır
if (-not (Test-Path $VenvPython)) {
    Write-Host "[*] MP3fy sanal ortamı bulunamadı. Otomatik kurulum başlatılıyor..." -ForegroundColor Yellow
    $InstallScript = Join-Path $ProjectDir "install.ps1"
    if (Test-Path $InstallScript) {
        & $InstallScript
    } else {
        Write-Host "[!] Hata: install.ps1 bulunamadı." -ForegroundColor Red
        exit 1
    }
}

if (Test-Path $VenvPython) {
    & $VenvPython $MainPy @args
    exit $LASTEXITCODE
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $MainPy @args
    exit $LASTEXITCODE
} else {
    Write-Host "[!] Hata: .venv\Scripts\python.exe veya Python bulunamadı." -ForegroundColor Red
    exit 1
}
