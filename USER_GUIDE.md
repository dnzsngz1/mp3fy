# 🎵 MP3fy - Linux CLI User Guide (English)

**MP3fy** is a modern, fast, command-line Spotify to MP3 converter and downloader designed specifically for the Linux terminal. It converts Spotify playlists, albums, and tracks into high-fidelity (320 kbps) MP3 files with original high-resolution album cover art and complete ID3 tags embedded, saving directly to your chosen destination folder.

---

## 📑 Table of Contents
1. [Key Features](#-key-features)
2. [Prerequisites & Installation](#-prerequisites--installation)
3. [Running via the `mp3fy` Command](#-running-via-the-mp3fy-command)
4. [Usage Workflows](#-usage-workflows)
   - [1. Interactive Wizard](#1-interactive-wizard)
   - [2. Direct CLI Command & Flags](#2-direct-cli-command--flags)
   - [3. 100-Track Batching](#3-100-track-batching)
   - [4. Bitrate & Concurrency](#4-bitrate--concurrency)
5. [Complete CLI Flags Reference](#-complete-cli-flags-reference)
6. [FAQ & Troubleshooting](#-faq--troubleshooting)

---

## 🌟 Key Features

- **⚡ Global Shell Command:** Simply type `mp3fy` in any terminal directory to launch the tool.
- **🔒 Zero-Configuration Spotify Resolver:** Fetch any playlist, album, or track without needing Spotify developer API keys.
- **📦 100-Track Batching (Pagination):** Large playlists (100, 200, 500+ tracks) are automatically organized into 100-track sections; download batch-by-batch (`--batch 1`) or all at once.
- **📁 Smart Folder Management:** Saves music to `~/Music` by default or any custom path passed via `-o / --output`.
- **🏷️ High-Fidelity ID3 Tagging:** Embeds high-resolution cover art (APIC), Artist (TPE1), Album (TALB), Title (TIT2), Year (TDRC), and Track Number (TRCK) using the ID3v2.3 standard.
- **📊 Real-time Terminal Progress:** Rich terminal UI with spinners, live speed (MB/s), ETA, and completed song counters.
- **🛡️ Clean Interrupt Handling:** Graceful `Ctrl+C` handling cleans up temporary download files safely.

---

## 🛠️ Prerequisites & Installation

### System Requirements
- **Operating System:** Linux (Ubuntu, Debian, Linux Mint, Fedora, Arch Linux, etc.)
- **Python:** Python 3.9 or higher
- **FFmpeg:** Required for audio processing and MP3 conversion.

### One-Click Installation:
```bash
git clone https://github.com/kullaniciadi/mp3fy.git
cd mp3fy
chmod +x install.sh
./install.sh
```

This sets up the virtual environment, installs dependencies, and creates the executable launcher at `~/.local/bin/mp3fy`.

---

## 🚀 Running via the `mp3fy` Command

From any terminal window:
```bash
mp3fy
```

### 1. Interactive Wizard
When run without parameters, MP3fy guides you interactively:
1. **Spotify URL:** Paste your track, album, or playlist URL (or enter `q` to quit).
2. **Batch Selection:** If a playlist has more than 100 tracks, choose a specific chunk (e.g. `1`, `2`) or download all (`T`).
3. **Destination Folder:** Press Enter for `~/Music` or specify a custom path.
4. **Bitrate:** Choose between 320, 256, 192, or 128 kbps (Default: 320).
5. **Workers:** Set concurrent download workers (Default: 2).

### 2. Direct CLI Command & Flags
Execute automated or scripted downloads in a single line:
```bash
# Download a single track
mp3fy "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4"

# Download a playlist to ~/Music with 320kbps bitrate using 3 parallel workers
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" -o ~/Music -b 320 -w 3

# Download an album
mp3fy "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa"
```

### 3. 100-Track Batching
For massive playlists (e.g., 300 tracks):
- Batch 1: 1 - 100
- Batch 2: 101 - 200
- Batch 3: 201 - 300

Download just Batch 2:
```bash
mp3fy "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --batch 2
```

---

## ⚙️ Complete CLI Flags Reference

| Flag | Description |
| :--- | :--- |
| `url` | Spotify track, album, or playlist link (omitting launches interactive mode) |
| `-i`, `--interactive` | Force interactive wizard mode |
| `-o`, `--output` | Destination directory for downloaded MP3s (Default: `~/Music`) |
| `-b`, `--bitrate` | MP3 audio bitrate (`128`, `192`, `256`, `320`) |
| `-w`, `--workers` | Number of concurrent download workers (Default: `2`) |
| `--batch` | For 100+ track playlists, download only specified batch (e.g. `1`, `2`) |
| `-v`, `--version` | Display MP3fy version |
| `-h`, `--help` | Display usage and help message |

---

## ❓ FAQ & Troubleshooting

**1. `mp3fy: command not found`:**  
Ensure `~/.local/bin` is in your shell's `PATH`:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**2. `ffmpeg` missing warning:**  
Install ffmpeg on your Linux distribution:
```bash
sudo apt update && sudo apt install ffmpeg
```

**3. Where are downloaded songs saved?**  
By default in your user music directory (`~/Music`). You can specify any target folder using `-o /path/to/folder`.
