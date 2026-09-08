"""
ID3 Metadata & Album Art Tagger for MP3fy using Mutagen
"""

import os
import logging
import re
from pathlib import Path
from typing import Optional, Union
import requests
from mutagen.id3 import (
    ID3,
    ID3NoHeaderError,
    TIT2,
    TPE1,
    TPE2,
    TALB,
    TDRC,
    TYER,
    TRCK,
    TPOS,
    TCON,
    COMM,
    APIC,
)

logger = logging.getLogger(__name__)


def apply_id3_tags(
    mp3_path: Union[str, Path],
    title: str,
    artist: str,
    album: Optional[str] = None,
    album_artist: Optional[str] = None,
    year: Optional[Union[str, int]] = None,
    track_number: Optional[Union[int, str]] = None,
    total_tracks: Optional[Union[int, str]] = None,
    disc_number: Optional[Union[int, str]] = None,
    genre: Optional[str] = None,
    cover_url: Optional[str] = None,
    cover_bytes: Optional[bytes] = None,
    comment: str = "Downloaded with MP3fy",
) -> bool:
    """
    Applies comprehensive ID3v2.3 tags and high-resolution album cover to the specified MP3 file.
    
    Args:
        mp3_path: Path to the MP3 file.
        title: Track title.
        artist: Main artist(s) name.
        album: Album name.
        album_artist: Album artist name (defaults to artist if None).
        year: Release year or date string.
        track_number: Track index/number.
        total_tracks: Total tracks in album/playlist.
        disc_number: Disc index (default 1).
        genre: Music genre if available.
        cover_url: URL to download album cover image.
        cover_bytes: Raw image bytes for cover art (if already downloaded).
        comment: User comment tag.
        
    Returns:
        bool: True if tagging succeeded, False otherwise.
    """
    file_path = Path(mp3_path).resolve()
    if not file_path.exists():
        logger.error(f"File not found for tagging: {file_path}")
        return False

    try:
        try:
            tags = ID3(str(file_path))
        except ID3NoHeaderError:
            tags = ID3()
        except Exception:
            tags = ID3()

        # Clean existing standard tags to avoid duplicates or corruption
        tags.delall("TIT2")
        tags.delall("TPE1")
        tags.delall("TPE2")
        tags.delall("TALB")
        tags.delall("TDRC")
        tags.delall("TYER")
        tags.delall("TRCK")
        tags.delall("TPOS")
        tags.delall("TCON")
        tags.delall("COMM")
        tags.delall("APIC")

        # UTF-8 / Unicode encoding (encoding=3 is UTF-8)
        # Title
        if title:
            tags.add(TIT2(encoding=3, text=str(title).strip()))

        # Artist
        if artist:
            tags.add(TPE1(encoding=3, text=str(artist).strip()))

        # Album Artist
        if album_artist or artist:
            tags.add(TPE2(encoding=3, text=str(album_artist or artist).strip()))

        # Album
        if album:
            tags.add(TALB(encoding=3, text=str(album).strip()))

        # Year / Date
        if year is not None:
            year_str = str(year).strip()
            if year_str:
                match = re.search(r"\b(\d{4})\b", year_str)
                year_clean = match.group(1) if match else year_str
                tags.add(TDRC(encoding=3, text=year_clean))
                tags.add(TYER(encoding=3, text=year_clean))

        # Track Number (format "current/total" or "current")
        if track_number is not None:
            track_str = str(track_number).strip()
            if "/" in track_str:
                trck_text = track_str
            elif total_tracks is not None and str(total_tracks).strip():
                trck_text = f"{track_str}/{str(total_tracks).strip()}"
            else:
                trck_text = track_str
            if trck_text:
                tags.add(TRCK(encoding=3, text=trck_text))

        # Disc Number
        if disc_number is not None:
            disc_str = str(disc_number).strip()
            if disc_str:
                tags.add(TPOS(encoding=3, text=disc_str))

        # Genre
        if genre:
            tags.add(TCON(encoding=3, text=str(genre).strip()))

        # Comment
        if comment:
            tags.add(COMM(encoding=3, lang="eng", desc="Description", text=comment))

        # Album Cover Art (APIC)
        image_data = cover_bytes
        if not image_data and cover_url:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                }
                resp = requests.get(cover_url, headers=headers, timeout=12)
                if resp.status_code == 200 and resp.content:
                    image_data = resp.content
            except Exception as img_err:
                logger.warning(f"Failed to fetch cover art from {cover_url}: {img_err}")

        if image_data:
            mime = None
            if image_data.startswith(b"\xff\xd8"):
                mime = "image/jpeg"
            elif image_data.startswith(b"\x89PNG\r\n\x1a\n"):
                mime = "image/png"
            elif image_data.startswith(b"RIFF") and b"WEBP" in image_data[:12]:
                mime = "image/webp"

            if mime:
                tags.add(
                    APIC(
                        encoding=3,
                        mime=mime,
                        type=3,  # 3 is front cover
                        desc="Cover",
                        data=image_data,
                    )
                )
            else:
                logger.warning("Cover art data is not a valid JPEG, PNG, or WebP image; omitting APIC frame.")

        # Save with ID3v2.3 for maximum compatibility across players
        tags.save(str(file_path), v2_version=3)
        return True

    except Exception as e:
        logger.error(f"Error applying ID3 tags to {file_path}: {e}", exc_info=True)
        return False
