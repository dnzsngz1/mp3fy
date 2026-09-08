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
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
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
                    $PythonExe = if ($check.Source) { $check.Source } else { $check.Definition }
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
$foundFfmpegPath = $null

if ($ffmpegCmd) {
    $foundFfmpegPath = $ffmpegCmd.Source
    Write-Host "[✓] FFmpeg sistemde hazır: $foundFfmpegPath" -ForegroundColor Green
} else {
    $commonFfmpeg = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ffmpeg.exe",
        "C:\ffmpeg\bin\ffmpeg.exe",
        "C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        "$HOME\scoop\apps\ffmpeg\current\bin\ffmpeg.exe",
        "$HOME\scoop\shims\ffmpeg.exe",
        "$HOME\AppData\Local\ffmpeg\bin\ffmpeg.exe",
        "C:\ProgramData\chocolatey\bin\ffmpeg.exe"
    )
    foreach ($path in $commonFfmpeg) {
        if (Test-Path $path) {
            $foundFfmpegPath = $path
            break
        }
    }

    # WinGet Paket dizini taraması
    if (-not $foundFfmpegPath -and (Test-Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages")) {
        $wingetFfmpeg = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ffmpeg.exe" -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($wingetFfmpeg) {
            $foundFfmpegPath = $wingetFfmpeg.FullName
        }
    }

    if ($foundFfmpegPath) {
        Write-Host "[✓] FFmpeg tespit edildi: $foundFfmpegPath" -ForegroundColor Green
        # Oturum PATH'ine ekle
        $ffmpegDir = Split-Path -Parent $foundFfmpegPath
        if (($env:Path -split ';') -notcontains $ffmpegDir) {
            $env:Path = "$ffmpegDir;$env:Path"
        }
    } else {
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

$installedWithUv = $false
if ($uvCmd) {
    Write-Host "`n[*] 'uv' bulundu, ultra-hızlı sanal ortam ve paket kurulumu deneniyor..." -ForegroundColor Yellow
    try {
        if (-not (Test-Path $VenvDir)) {
            & uv venv "$VenvDir"
        }
        & uv pip install --python "$VenvPython" -e "$ProjectDir"
        if (Test-Path $VenvPython) {
            $installedWithUv = $true
        }
    } catch {
        Write-Host "[-] uv ile kurulum tamamlanamadı, standart pip yöntemine geçiliyor..." -ForegroundColor Gray
    }
}

if (-not $installedWithUv) {
    if (-not (Test-Path $VenvDir)) {
        Write-Host "`n[*] Sanal ortam (.venv) oluşturuluyor..." -ForegroundColor Yellow
        if ($PythonCmd -eq "py") {
            & py -3 -m venv "$VenvDir"
        } else {
            & $PythonCmd -m venv "$VenvDir"
        }
    }
    Write-Host "[*] Bağımlılıklar yükleniyor (pip)..." -ForegroundColor Yellow
    try {
        & "$VenvPython" -m pip install --upgrade pip --quiet -ErrorAction SilentlyContinue
    } catch {}
    & "$VenvPython" -m pip install -e "$ProjectDir"
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Hata: Sanal ortam yürütücüsü bulunamadı: $VenvPython" -ForegroundColor Red
    exit 1
}

# 5. Global CLI Başlatıcıları (Launcher) Oluşturma
$UserHome = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$UserBinDir = Join-Path $UserHome "bin"
if (-not (Test-Path $UserBinDir)) {
    New-Item -ItemType Directory -Path $UserBinDir -Force | Out-Null
}

$UserCmdContent = @"
@echo off
setlocal
set "MP3FY_DIR=$ProjectDir"
chcp 65001 >nul
if exist "%MP3FY_DIR%\.venv\Scripts\python.exe" (
    "%MP3FY_DIR%\.venv\Scripts\python.exe" "%MP3FY_DIR%\main.py" %*
) else (
    python "%MP3FY_DIR%\main.py" %*
)
endlocal & exit /b %ERRORLEVEL%
"@

$UserPs1Content = @"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
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

# Global kullanıcı PATH dizinine ($HOME\bin) yükle
$UserCmd = Join-Path $UserBinDir "mp3fy.cmd"
$UserPs1 = Join-Path $UserBinDir "mp3fy.ps1"
Set-Content -Path $UserCmd -Value $UserCmdContent -Encoding UTF8
Set-Content -Path $UserPs1 -Value $UserPs1Content -Encoding UTF8

Write-Host "`n[✓] Global komut başlatıcıları oluşturuldu:" -ForegroundColor Green
Write-Host "    -> $UserCmd" -ForegroundColor Gray
Write-Host "    -> $UserPs1" -ForegroundColor Gray

# Kullanıcı PATH Değişkeni Kontrolü ve Güncellemesi
$UserEnvPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
$pathParts = if ($UserEnvPath) { $UserEnvPath -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" } } else { @() }

if ($pathParts -notcontains $UserBinDir) {
    Write-Host "`n[*] '$UserBinDir' kullanıcı PATH ortam değişkenine ekleniyor..." -ForegroundColor Yellow
    $NewUserPath = ($pathParts + $UserBinDir) -join ';'
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
    `$python = "$VenvPython"
    if (-not (Test-Path `$python)) {
        `$python = "python"
    }
    & `$python "$ProjectDir\main.py" @args
}
"@
        if ($profileContent -match "function\s+mp3fy\s*\{") {
            # Mevcut eski veya hatalı tanımı güncelle
            $newProfileContent = [regex]::Replace($profileContent, "(?s)#\s*MP3fy CLI Shortcut.*?function\s+mp3fy\s*\{.*?\}", $mp3fySnippet.Trim())
            if ($newProfileContent -eq $profileContent) {
                $newProfileContent = [regex]::Replace($profileContent, "(?s)function\s+mp3fy\s*\{.*?\}", $mp3fySnippet.Trim())
            }
            Set-Content -Path $PROFILE -Value $newProfileContent -Encoding UTF8
            Write-Host "[✓] PowerShell Profilindeki ($PROFILE) 'mp3fy' fonksiyonu güncellendi." -ForegroundColor Green
        } else {
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
Write-Host "    mp3fy `"https://open.spotify.com/playlist/...`"" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
