# ==============================================================================
# MP3fy - Windows / PowerShell CLI Kurulum Scripti (Installer)
# ==============================================================================
[CmdletBinding()]
param(
    [switch]$SkipProfile,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# UTF-8 konsol kodlamasını etkinleştir
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎵 MP3fy PowerShell & Windows Kurulumu Başlatılıyor..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Proje Dizinini Belirle
$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) {
    $ProjectDir = (Get-Location).Path
}
Set-Location -Path $ProjectDir
Write-Host "[+] Proje Dizini: $ProjectDir" -ForegroundColor Gray

# 2. Python Tespiti ve Doğrulaması
Write-Host "`n[*] Python kontrol ediliyor..." -ForegroundColor Yellow
$PythonCmd = $null
$PythonExe = $null

$candidates = @("python", "py", "python3")
foreach ($cmd in $candidates) {
    try {
        $check = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($check) {
            $verOutput = & $cmd --version 2>&1
            if ($verOutput -match "Python\s+3\.(\d+)") {
                $minor = [int]$matches[1]
                if ($minor -ge 9) {
                    $PythonCmd = $cmd
                    $PythonExe = $check.Source
                    Write-Host "[✓] Python bulundu: $PythonExe ($verOutput)" -ForegroundColor Green
                    break
                }
            }
        }
    } catch {}
}

if (-not $PythonCmd) {
    Write-Host "[!] Hata: Python 3.9 veya üzeri bulunamadı!" -ForegroundColor Red
    Write-Host "    Lütfen Python yükleyin veya PATH ortam değişkeninize ekleyin." -ForegroundColor Yellow
    Write-Host "    Hızlı yükleme için PowerShell'de çalıştırabilirsiniz:" -ForegroundColor Yellow
    Write-Host "        winget install Python.Python.3.11" -ForegroundColor Cyan
    Write-Host "    Veya resmi siteden indirin: https://www.python.org/downloads/" -ForegroundColor Cyan
    exit 1
}

# 3. FFmpeg Kontrolü ve Yönlendirme
Write-Host "`n[*] FFmpeg kontrol ediliyor..." -ForegroundColor Yellow
$ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpegCmd) {
    Write-Host "[✓] FFmpeg sistemde hazır: $($ffmpegCmd.Source)" -ForegroundColor Green
} else {
    $commonFfmpeg = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages",
        "C:\ffmpeg\bin\ffmpeg.exe",
        "$HOME\scoop\apps\ffmpeg\current\bin\ffmpeg.exe",
        "$HOME\scoop\shims\ffmpeg.exe",
        "$HOME\AppData\Local\ffmpeg\bin\ffmpeg.exe",
        "C:\ProgramData\chocolatey\bin\ffmpeg.exe"
    )
    $foundFfmpeg = $false
    foreach ($path in $commonFfmpeg) {
        if (Test-Path $path) {
            Write-Host "[✓] FFmpeg tespit edildi: $path" -ForegroundColor Green
            $foundFfmpeg = $true
            break
        }
    }
    if (-not $foundFfmpeg) {
        Write-Host "[!] Uyarı: 'ffmpeg' komutu sistemde bulunamadı!" -ForegroundColor Yellow
        Write-Host "    MP3 dönüştürme işlemi için FFmpeg gereklidir." -ForegroundColor Yellow
        Write-Host "    PowerShell üzerinden tek komutla yükleyebilirsiniz:" -ForegroundColor Yellow
        Write-Host "        winget install Gyan.FFmpeg" -ForegroundColor Cyan
        Write-Host "    veya Scoop/Chocolatey ile:" -ForegroundColor Yellow
        Write-Host "        scoop install ffmpeg  |  choco install ffmpeg" -ForegroundColor Cyan
    }
}

# 4. Sanal Ortam (.venv) Kurulumu
$VenvDir = Join-Path $ProjectDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue

if ($uvCmd) {
    Write-Host "`n[*] 'uv' bulundu, ultra-hızlı sanal ortam ve paket kurulumu yapılıyor..." -ForegroundColor Yellow
    if (-not (Test-Path $VenvDir)) {
        & uv venv "$VenvDir"
    }
    & uv pip install --python "$VenvPython" -e "$ProjectDir"
} else {
    if (-not (Test-Path $VenvDir)) {
        Write-Host "`n[*] Sanal ortam (.venv) oluşturuluyor..." -ForegroundColor Yellow
        & $PythonCmd -m venv "$VenvDir"
    }
    Write-Host "[*] Bağımlılıklar yükleniyor (pip)..." -ForegroundColor Yellow
    & "$VenvPython" -m pip install --upgrade pip --quiet
    & "$VenvPython" -m pip install -e "$ProjectDir"
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Hata: Sanal ortam yürütücüsü bulunamadı: $VenvPython" -ForegroundColor Red
    exit 1
}

# 5. Global CLI Başlatıcıları (Launcher) Oluşturma
$UserBinDir = Join-Path $HOME "bin"
if (-not (Test-Path $UserBinDir)) {
    New-Item -ItemType Directory -Path $UserBinDir -Force | Out-Null
}

$CmdContent = @"
@echo off
setlocal
set "MP3FY_DIR=$ProjectDir"
chcp 65001 >nul
if exist "%MP3FY_DIR%\.venv\Scripts\python.exe" (
    "%MP3FY_DIR%\.venv\Scripts\python.exe" "%MP3FY_DIR%\main.py" %*
) else (
    python "%MP3FY_DIR%\main.py" %*
)
endlocal
"@

$Ps1Content = @"
[CmdletBinding()]
param()
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    `$OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}
`$mp3fyDir = "$ProjectDir"
`$pythonExe = Join-Path `$mp3fyDir ".venv\Scripts\python.exe"
`$mainPy = Join-Path `$mp3fyDir "main.py"
if (Test-Path `$pythonExe) {
    & `$pythonExe `$mainPy @args
} else {
    & python `$mainPy @args
}
exit `$LASTEXITCODE
"@

# Proje kökündeki başlatıcılar
Set-Content -Path (Join-Path $ProjectDir "mp3fy.cmd") -Value $CmdContent -Encoding ASCII
Set-Content -Path (Join-Path $ProjectDir "mp3fy.ps1") -Value $Ps1Content -Encoding UTF8

# Kullanıcı PATH dizinine ($HOME\bin) kopyala
$UserCmd = Join-Path $UserBinDir "mp3fy.cmd"
$UserPs1 = Join-Path $UserBinDir "mp3fy.ps1"
Set-Content -Path $UserCmd -Value $CmdContent -Encoding ASCII
Set-Content -Path $UserPs1 -Value $Ps1Content -Encoding UTF8

Write-Host "`n[✓] Komut başlatıcıları oluşturuldu:" -ForegroundColor Green
Write-Host "    -> $UserCmd" -ForegroundColor Gray
Write-Host "    -> $UserPs1" -ForegroundColor Gray

# Kullanıcı PATH Değişkeni Kontrolü ve Güncellemesi
$UserEnvPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
$pathParts = $UserEnvPath -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

if ($pathParts -notcontains $UserBinDir) {
    Write-Host "`n[*] '$UserBinDir' kullanıcı PATH ortam değişkenine ekleniyor..." -ForegroundColor Yellow
    $NewUserPath = if ($UserEnvPath) { "$UserEnvPath;$UserBinDir" } else { $UserBinDir }
    [Environment]::SetEnvironmentVariable("Path", $NewUserPath, [EnvironmentVariableTarget]::User)
    $env:Path = "$UserBinDir;$env:Path"
    Write-Host "[✓] PATH güncellendi! Yeni PowerShell pencerelerinde doğrudan 'mp3fy' çalışacaktır." -ForegroundColor Green
} else {
    Write-Host "[✓] '$UserBinDir' zaten kullanıcı PATH değişkeninde kayıtlı." -ForegroundColor Green
    if (($env:Path -split ';') -notcontains $UserBinDir) {
        $env:Path = "$UserBinDir;$env:Path"
    }
}

# 6. PowerShell Profili ($PROFILE) Entegrasyonu
if (-not $SkipProfile) {
    try {
        $ProfileDir = Split-Path -Parent $PROFILE
        if (-not (Test-Path $ProfileDir)) {
            New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
        }
        if (-not (Test-Path $PROFILE)) {
            New-Item -ItemType File -Path $PROFILE -Force | Out-Null
        }
        $profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
        $mp3fySnippet = @"

# MP3fy CLI Shortcut
function mp3fy {
    [CmdletBinding()]
    param()
    & "$VenvPython" "$ProjectDir\main.py" @args
}
"@
        if (-not $profileContent -or $profileContent -notmatch "function mp3fy") {
            Add-Content -Path $PROFILE -Value $mp3fySnippet -Encoding UTF8
            Write-Host "[✓] PowerShell Profiline ($PROFILE) 'mp3fy' fonksiyonu eklendi." -ForegroundColor Green
        }
    } catch {
        Write-Host "[-] Not: PowerShell profili otomatik güncellenemedi (isteğe bağlı adım)." -ForegroundColor Gray
    }
}

Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "[✓] Kurulum Başarıyla Tamamlandı!" -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Artık PowerShell terminalinde doğrudan şu komutu çalıştırabilirsiniz:" -ForegroundColor White
Write-Host "    mp3fy" -ForegroundColor Yellow
Write-Host "veya parametrelerle doğrudan indirme:" -ForegroundColor White
Write-Host "    mp3fy https://open.spotify.com/playlist/..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
