"""
Utility functions for MP3fy
"""

import os
import re
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Dict


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Remove or replace characters that are invalid in file names across Windows, Linux, and macOS.
    """
    if not filename:
        return "unnamed_track"
    
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    
    # Replace illegal filesystem characters: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', replacement, cleaned)
    
    # Normalize multiple spaces or replacements
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'[ _]+', ' ', cleaned)
    
    # Remove trailing/leading dots and spaces (problematic on Windows)
    cleaned = cleaned.strip('. ')
    
    # If empty after cleanup
    if not cleaned:
        return "unnamed_track"
        
    return cleaned[:200]  # Avoid MAX_PATH limits


def format_duration(duration_ms: int | float | None) -> str:
    """
    Format duration in milliseconds to MM:SS or HH:MM:SS string.
    """
    if not duration_ms or duration_ms < 0:
        return "0:00"
    
    total_seconds = int(duration_ms // 1000) if duration_ms > 1000 else int(duration_ms)
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
            ps_cmd = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.windows.forms') | Out-Null;"
                "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog;"
                "$dialog.Description = 'MP3fy İndirme Klasörünü Seçin';"
                f"$dialog.SelectedPath = '{init_path}';"
                "if($dialog.ShowDialog() -eq 'OK'){ Write-Output $dialog.SelectedPath }"
            )
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=60)
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
