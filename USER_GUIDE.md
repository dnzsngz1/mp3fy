# 🎵 MP3fy - PowerShell & Terminal User Guide (English)

**MP3fy** is a fast, modern command-line Spotify to MP3 converter and downloader designed for PowerShell and Linux terminals. It converts Spotify playlists, albums, and tracks into high-fidelity (320 kbps) MP3 files with original high-resolution album cover art and complete ID3 tags embedded, saving directly to your chosen destination folder.

---

## 📑 Table of Contents
1. [Key Features](#-key-features)
2. [Prerequisites & Installation](#-prerequisites--installation)
   - [Windows / PowerShell Installation](#windows--powershell-installation)
   - [Linux Installation](#linux-installation)
3. [Running via the `mp3fy` Command](#-running-via-the-mp3fy-command)
4. [Usage Workflows](#-usage-workflows)
   - [1. Interactive Wizard](#1-interactive-wizard)
   - [2. Direct CLI Command & Flags](#2-direct-cli-command--flags)
   - [3. 100-Track Batching](#3-100-track-batching)
   - [4. Bitrate & Concurrency](#4-bitrate--concurrency)
5. [Complete CLI Flags Reference](#-complete-cli-flags-reference)
6. [PowerShell & Windows Tips](#-powershell--windows-tips)
7. [FAQ & Troubleshooting](#-faq--troubleshooting)

---

## 🌟 Key Features

- **⚡ Global Terminal Command (`mp3fy`):** Simply type `mp3fy` in any PowerShell or terminal window to launch the tool.
- **🪟 Native PowerShell & Windows Support:** Compatible with Windows PowerShell 5.1 and PowerShell Core 7+, with automatic PATH and `$PROFILE` registration, and UTF-8 console output.
- **🔒 Zero-Configuration Spotify Resolver:** Fetch any public playlist, album, or track without needing Spotify developer API keys.
- **📦 100-Track Batching (Pagination):** Large playlists (100, 200, 500+ tracks) are automatically organized into 100-track sections; download batch-by-batch (`--batch 1`) or all at once.
- **📁 Smart Folder Management:** Saves music to your Music folder (`~/Music` or `C:\Users\<User>\Music`) by default, or any custom path passed via `-o / --output`.
- **🏷️ High-Fidelity ID3 Tagging:** Embeds high-resolution cover art (APIC), Artist (TPE1), Album (TALB), Title (TIT2), Year (TDRC), and Track Number (TRCK) using the ID3v2.3 standard.
- **📊 Real-time Terminal Progress:** Rich terminal UI with spinners, live speed (MB/s), ETA, and completed song counters.
- **🛡️ Clean Interrupt Handling:** Graceful `Ctrl+C` handling cleans up temporary download files safely.

---

## 🛠️ Prerequisites & Installation

### System Requirements
- **Operating System:** Windows 10/11 (PowerShell) or Linux (Ubuntu, Debian, Fedora, Arch, etc.)
- **Python:** Python 3.9 or higher
- **FFmpeg:** Required for audio conversion and tagging.

---

### Windows / PowerShell Installation

1. **Open PowerShell and clone the repository:**
   ```powershell
   git clone https://github.com/kullaniciadi/mp3fy.git
   cd mp3fy
   ```

2. **Run the PowerShell Installer:**
   ```powershell
   # If script execution is restricted, temporarily permit execution:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

   # Run the installer:
   .\install.ps1
   ```

3. **Install FFmpeg (if not already installed):**
   ```powershell
   winget install Gyan.FFmpeg
   # Or via Scoop:
   scoop install ffmpeg
   # Or via Chocolatey:
   choco install ffmpeg
   ```

The installer builds the virtual environment, installs dependencies, creates `mp3fy.cmd` and `mp3fy.ps1` in `$HOME\bin`, adds this directory to your persistent user PATH, and defines an `mp3fy` shortcut function in your `$PROFILE`.

---

### Linux Installation

```bash
chmod +x install.sh
./install.sh
```

---

## 🚀 Running via the `mp3fy` Command

From any PowerShell or terminal directory:
```powershell
mp3fy
```

### 1. Interactive Wizard
When run without parameters, MP3fy guides you interactively:
1. **Spotify URL:** Paste your track, album, or playlist URL (or enter `q` to quit).
2. **Batch Selection:** If a playlist has more than 100 tracks, choose a specific chunk (e.g. `1`, `2`) or download all (`T`).
3. **Destination Folder:** Press Enter for your default Music folder or specify a custom path.
4. **Bitrate:** Choose between 320, 256, 192, or 128 kbps (Default: 320).
5. **Workers:** Set concurrent download workers (Default: 2).

### 2. Direct CLI Command & Flags
Execute automated or scripted downloads in a single line:
```powershell
# Download a single track
mp3fy "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4"

# Download a playlist to a custom directory with 320kbps and 3 workers
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" -o "$HOME\Music\Favs" -b 320 -w 3

# Download an entire album
mp3fy "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa"
```

### 3. 100-Track Batching
For a 250-track playlist:
- Batch 1: 1 - 100
- Batch 2: 101 - 200
- Batch 3: 201 - 250

Download only Batch 2:
```powershell
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --batch 2
```

---

## ⚙️ Complete CLI Flags Reference

| Flag | Description | Default |
| :--- | :--- | :--- |
| `url` | Spotify track, album, or playlist URL | `None` (Interactive Mode) |
| `-i`, `--interactive` | Force the interactive wizard mode | `False` |
| `-o`, `--output` | Destination directory for downloaded MP3s | User's Music folder |
| `-b`, `--bitrate` | Audio bitrate quality (`128`, `192`, `256`, `320`) | `320` |
| `-w`, `--workers` | Number of concurrent download workers (1-8) | `2` |
| `--batch` | Specific 100-song batch to download (e.g. `1`, `2`) | `All` |
| `-v`, `--version` | Display MP3fy version number | - |
| `-h`, `--help` | Show command line options and help | - |

---

## 💡 PowerShell & Windows Tips

1. **Quick Runner Script:**
   Inside the project repository, you can also run `.\run.ps1` or double-click `run.bat`.
2. **UTF-8 Console Encoding:**
   MP3fy automatically configures UTF-8 encoding and ANSI Virtual Terminal Processing on Windows consoles, preventing character corruption in song titles.
3. **ExecutionPolicy Issue:**
   If running `.ps1` files is blocked by PowerShell policy, run:
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```

---

## ❓ FAQ & Troubleshooting

**1. "The term 'mp3fy' is not recognized":**  
Open a new PowerShell window so the updated User PATH takes effect. In an existing window, run:
```powershell
$env:Path = "$HOME\bin;$env:Path"
```

**2. "ffmpeg not found" warning:**  
Install FFmpeg using:
```powershell
winget install Gyan.FFmpeg
```
Then restart PowerShell.

**3. Where are downloaded songs stored?**  
In your default Windows Music directory (`C:\Users\<User>\Music`) or whichever path was specified via `-o`.
