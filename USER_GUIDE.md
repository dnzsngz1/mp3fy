# 🎵 MP3fy - User Guide (English)

**MP3fy** is a modern, fast, open-source Spotify to MP3 converter and downloader. It converts Spotify playlists, albums, and tracks into high-fidelity (320 kbps) MP3 files with original high-resolution album cover art and complete ID3 tags embedded, saving directly to your chosen destination folder.

---

## 📑 Table of Contents
1. [Key Features](#-key-features)
2. [Prerequisites & Installation](#-prerequisites--installation)
3. [Running the Application](#-running-the-application)
4. [Step-by-Step Usage](#-step-by-step-usage)
   - [1. Fetching Spotify Metadata](#1-fetching-spotify-metadata)
   - [2. 100-Track Batching & Pagination](#2-100-track-batching--pagination)
   - [3. Custom Download Folder Selection](#3-custom-download-folder-selection)
   - [4. Downloading & Audio Conversion](#4-downloading--audio-conversion)
   - [5. Dark / Light Theme & Language Switcher](#5-dark--light-theme--language-switcher)
5. [Settings & Audio Quality](#-settings--audio-quality)
6. [FAQ & Troubleshooting](#-faq--troubleshooting)

---

## 🌟 Key Features

- **🔒 Zero-Configuration Spotify Resolver:** Fetch any playlist, album, or track without needing Spotify developer API keys.
- **📦 100-Track Batching (Pagination):** Large playlists (100, 200, 500+ tracks) are automatically organized into 100-track sections; download batch-by-batch or all at once.
- **📁 Flexible Folder Selector:** Choose where your music goes via native OS directory picker dialog, fast presets (`Music`, `Downloads`, `Desktop`, `Documents`), or custom directory paths.
- **🏷️ High-Fidelity ID3 Tagging:** Embeds high-resolution cover art (APIC), Artist (TPE1), Album (TALB), Title (TIT2), Year (TDRC), and Track Number (TRCK) using ID3v2.3 standard.
- **🎧 Studio Audio Quality:** Converts audio to crystal-clear 320 kbps MP3 format via `yt-dlp` and `ffmpeg`.
- **🌓 Modern Glassmorphic Dark / Light Theme:** Atmospheric UI design with smooth theme toggle.
- **🌐 Bilingual Support (English / Turkish):** Instant language switching in one click.

---

## 🛠️ Prerequisites & Installation

### System Requirements
- **Operating System:** Linux (Ubuntu/Debian/Fedora/Arch), Windows 10/11, macOS
- **Python:** Python 3.10 or higher
- **FFmpeg:** Required for audio processing and MP3 conversion.

### Installing FFmpeg:
- **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt update && sudo apt install ffmpeg -y
  ```
- **Arch Linux:**
  ```bash
  sudo pacman -S ffmpeg
  ```
- **macOS (Homebrew):**
  ```bash
  brew install ffmpeg
  ```
- **Windows:**
  Download from [FFmpeg Official Website](https://ffmpeg.org/download.html) and add to system `PATH`, or run `winget install Gyan.FFmpeg`.

---

## 🚀 Running the Application

### Linux / macOS:
Run the launcher script in the project directory:
```bash
cd mp3fy
chmod +x run.sh
./run.sh
```

### Windows:
Double-click `run.bat` in the project root or execute via command prompt:
```cmd
cd mp3fy
run.bat
```

> **Note:** The launcher script automatically creates a Python virtual environment (`.venv`), installs required dependencies, and launches the web interface at `http://localhost:8888`.

---

## 📖 Step-by-Step Usage

### 1. Fetching Spotify Metadata
1. Copy any **Playlist**, **Album**, or **Track** link from Spotify.
2. Paste it into the MP3fy input bar (or click the **"Paste"** button).
3. Click **"Fetch Playlist"**. The tracklist and metadata will be loaded in seconds.

### 2. 100-Track Batching & Pagination
- For playlists with more than 100 tracks (e.g. 150, 300, 500+ items), MP3fy automatically organizes tracks into 100-track batches:
  - `[✨ All Tracks (150)]`
  - `[📦 Batch 1 (1 - 100)]`
  - `[📦 Batch 2 (101 - 150)]`
- Click any batch pill to filter the view and use **"Download Batch"** to download tracks section by section.

### 3. Custom Download Folder Selection
- Click the **"📁 Folder: [Path]"** button in the header or the edit button in the playlist card to open the Folder Selector:
  - **Browse Computer Folder...:** Opens your native operating system file chooser.
  - **Quick Locations:** `Music (~/Music)`, `Downloads (~/Downloads)`, `Desktop (~/Desktop)`, `Documents (~/Documents)`.
  - **Custom Path:** Type any destination path or external drive directory and click **"Apply"**.

### 4. Downloading & Audio Conversion
- **Download All:** Queues and downloads all selected tracks across the entire playlist.
- **Single Download:** Click the **"Download"** button on any track row.
- **Live Progress:** Track percentage, download speed (MB/s), and conversion status in real-time.
- **Audio Preview:** Click the play icon on any track row to preview the track in the floating web audio player before or after downloading.

### 5. Dark / Light Theme & Language Switcher
- **Theme:** Click `[🌙 Dark / ☀️ Light]` in the header to switch themes.
- **Language:** Click `[🌐 TR / EN]` in the header to toggle between English and Turkish.

---

## ⚙️ Settings & Audio Quality

Click the **⚙️ Settings** icon in the top right:
- **Audio Bitrate:** Choose between 320 kbps (Studio - Recommended), 256 kbps, 192 kbps, or 128 kbps.
- **Custom Spotify API:** Optionally provide your own Spotify Developer Client ID / Secret (not required for normal operation).

---

## ❓ FAQ & Troubleshooting

**Q: Where are downloaded MP3 files saved?**  
**A:** Files are saved to your selected download folder (default is `~/Music`). You can change this anytime from the top bar or click the folder icon to open the directory in your file manager.

**Q: Are album covers and tags embedded in the MP3?**  
**A:** Yes. High-resolution album artwork, artist, album, track title, and year are embedded using ID3v2.3 standard tags. They display correctly on car head units, smartphones, and all media players.

**Q: "FFmpeg not found" error?**  
**A:** Make sure FFmpeg is installed on your system and accessible via terminal (`ffmpeg -version`). Refer to the Prerequisites section above for installation commands.
