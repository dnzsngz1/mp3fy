"""
Utility functions for MP3fy
"""

import os
import re
import sys
import math
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Dict, Union

WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(
    filename: str,
    replacement: str = "_",
    max_length: int = 200,
    default: str = "unnamed_track",
) -> str:
    """
    Remove or replace characters that are invalid in file names across Windows, Linux, and macOS.
    Guards against Windows reserved device names, truncates before stripping trailing dots/spaces,
    clamps to <= max_length chars / 250 bytes, and returns a safe fallback if empty.
    """
    fallback = default or "unnamed_track"
    if not filename:
        return fallback

    # Remove control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # If illegal characters have adjacent spaces or form repeated separators, replace with space
    cleaned = re.sub(r'\s+[<>:"/\\|?*]+|\s*[<>:"/\\|?*]+\s+', ' ', cleaned)

    # Replace remaining illegal filesystem characters: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', replacement, cleaned)

    # Normalize multiple spaces (preserving legitimate underscores)
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Strip leading/trailing dots and spaces
    cleaned = cleaned.strip('. ')

    # If empty after initial cleanup
    if not cleaned:
        return fallback

    # Check against Windows reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9, case-insensitive)
    stem = cleaned.split(".")[0].strip()
    if stem.upper() in WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"

    # Truncate to max_length AFTER any prefixing
    max_len = max_length if max_length is not None else 200
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]

    # Enforce safe byte clamp for Linux filesystems (max 250 bytes UTF-8)
    encoded = cleaned.encode("utf-8")
    if len(encoded) > 250:
        cleaned = encoded[:250].decode("utf-8", errors="ignore")

    # Remove trailing dots and spaces that may result from truncation
    cleaned = cleaned.rstrip('. ')

    # If empty after cleanup
    if not cleaned:
        return fallback

    return cleaned


def format_duration(
    duration_ms: Optional[Union[int, float]],
    in_seconds: Optional[bool] = None,
) -> str:
    """
    Format duration in milliseconds (or seconds if in_seconds=True) to MM:SS or HH:MM:SS string.
    Ensures 0 <= duration_ms < 1000 evaluates to "0:00" (or "0:01" if rounded),
    correctly formatting sub-second inputs and disambiguating milliseconds vs seconds.
    Guards against non-finite values (NaN, Inf) and negative durations.
    """
    if duration_ms is None:
        return "0:00"

    if not isinstance(duration_ms, (int, float)):
        return "0:00"

    if not math.isfinite(duration_ms) or duration_ms <= 0:
        return "0:00"

    if in_seconds is True:
        total_seconds = int(round(duration_ms))
    else:
        # Default behavior: input is in milliseconds.
        # Sub-second inputs (0 <= duration_ms < 1000) evaluate to 0 seconds ("0:00").
        total_seconds = int(duration_ms // 1000)

    if total_seconds <= 0:
        return "0:00"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"



def ensure_directory(path: str | Path) -> Path:
    """
    Ensure the target directory exists and return Path object.
    Supports expanding tilde (~) to user home directory.
    """
    expanded = os.path.expanduser(str(path))
    p = Path(expanded).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_default_music_dir() -> Path:
    """
    Get the default music directory in the user's home directory (e.g. ~/Music or ~/Müzik).
    """
    home = Path.home()
    for folder_name in ["Music", "Müzik", "music", "müzik"]:
        candidate = home / folder_name
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Fallback: create and return ~/Music
    default_dir = home / "Music"
    ensure_directory(default_dir)
    return default_dir


def open_folder_in_explorer(folder_path: str | Path) -> bool:
    """
    Open the given folder in the system's default file manager.
    Supports Windows, macOS, and Linux.
    """
    expanded = os.path.expanduser(str(folder_path))
    path_str = str(Path(expanded).resolve())
    try:
        current_os = platform.system()
        if current_os == "Windows":
            os.startfile(path_str)  # type: ignore
            return True
        elif current_os == "Darwin":  # macOS
            subprocess.run(["open", path_str], check=True)
            return True
        else:  # Linux / Unix
            # Try xdg-open first
            subprocess.Popen(["xdg-open", path_str])
            return True
    except Exception as e:
        print(f"Error opening folder {path_str}: {e}")
        return False


def open_native_folder_picker(initial_dir: Optional[str | Path] = None) -> Optional[str]:
    """
    Opens native OS directory chooser dialog and returns the selected folder path, or None.
    Supports Linux (zenity / kdialog / tkinter), macOS (osascript), Windows (PowerShell / Windows Forms).
    """
    sys_name = platform.system()
    init_path = str(Path(initial_dir or Path.home()).resolve())

    if sys_name == "Linux":
        # 1. Try zenity
        try:
            cmd = ["zenity", "--file-selection", "--directory", "--title=İndirme Klasörünü Seçin", f"--filename={init_path}/"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        # 2. Try kdialog
        try:
            cmd = ["kdialog", "--getexistingdirectory", init_path, "--title", "İndirme Klasörünü Seçin"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    elif sys_name == "Darwin":  # macOS
        try:
            script = 'POSIX path of (choose folder with prompt "İndirme Klasörünü Seçin:")'
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=60)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    elif sys_name == "Windows":
        try:
            safe_init_path = init_path.replace("'", "''")
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$dialog.Description = 'MP3fy İndirme Klasörünü Seçin'; "
                f"$dialog.SelectedPath = '{safe_init_path}'; "
                "$dialog.ShowNewFolderButton = $true; "
                "if($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){ Write-Output $dialog.SelectedPath }"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-STA", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    # Fallback: Tkinter if available
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(initialdir=init_path, title="İndirme Klasörünü Seçin")
        root.destroy()
        if selected:
            return selected
    except Exception:
        pass

    return None


def get_common_folder_presets() -> List[Dict[str, str]]:
    """Returns a list of common download folder presets for quick selection."""
    home = Path.home()
    presets = []

    # Music
    for m in ["Music", "Müzik"]:
        if (home / m).exists():
            presets.append({"name": "Müzik", "path": str(home / m), "icon": "music_note"})
            break
    else:
        presets.append({"name": "Müzik", "path": str(home / "Music"), "icon": "music_note"})

    # Downloads
    for d in ["Downloads", "İndirilenler"]:
        if (home / d).exists():
            presets.append({"name": "İndirilenler", "path": str(home / d), "icon": "download"})
            break

    # Desktop
    for d in ["Desktop", "Masaüstü"]:
        if (home / d).exists():
            presets.append({"name": "Masaüstü", "path": str(home / d), "icon": "desktop_windows"})
            break

    # Documents
    for d in ["Documents", "Belgeler"]:
        if (home / d).exists():
            presets.append({"name": "Belgeler", "path": str(home / d), "icon": "folder"})
            break

    return presets
