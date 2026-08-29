"""
Utility functions for MP3fy
"""

import os
import re
import sys
import subprocess
import platform
from pathlib import Path


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
    """
    p = Path(path).resolve()
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
    path_str = str(Path(folder_path).resolve())
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
