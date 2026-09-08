"""
Test harness for MP3fy E2E test suite.
Provides pure-Python synthetic MP3 generators, mock images, Spotify responses,
yt-dlp mocks, and an isolated filesystem environment.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from typing import Optional, List, Dict, Any
from unittest.mock import MagicMock, patch

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Pure-Python valid MPEG 1 Layer III (128kbps, 44.1kHz) audio frame
# Sync word 0xFFFB, bitrate 1001 (128k), sample rate 00 (44.1k), padding 0, private 0
MPEG_AUDIO_FRAME = b"\xff\xfb\x90\x64" + b"\x00" * 413

# Valid minimal 1x1 image payloads
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82"
)

JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c"
    b"\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
    b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)

WEBP_BYTES = (
    b"RIFF\x1a\x00\x00\x00WEBPVP8 \x0e\x00\x00\x00"
    b"/ \x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00"
)

HTML_ERROR_BYTES = b"<!DOCTYPE html><html><head><title>404 Not Found</title></head><body>Not Found</body></html>"
CORRUPT_BYTES = b"NOT_A_VALID_IMAGE_OR_AUDIO_STREAM_CORRUPT_DATA_12345"


def create_synthetic_mp3(file_path: Path, num_frames: int = 15) -> Path:
    """Generates a valid pure-Python MP3 file with MPEG-1 Layer 3 frames without invoking FFmpeg."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(MPEG_AUDIO_FRAME * max(1, num_frames))
    return file_path


def create_mock_track_embed_html(
    track_id: str = "4LfCY65LvojKjWEnU7fNN4",
    title: str = "Test Track",
    artist: str = "Test Artist",
    duration_ms: int = 210000,
    cover_url: Optional[str] = "https://i.scdn.co/image/ab67616d0000b273test",
    release_year: Optional[str] = "2024",
) -> str:
    """Constructs Spotify Next.js embed HTML for a track."""
    data = {
        "props": {
            "pageProps": {
                "state": {
                    "data": {
                        "entity": {
                            "id": track_id,
                            "name": title,
                            "title": title,
                            "subtitle": artist,
                            "duration": duration_ms,
                            "artists": [{"name": artist}],
                            "releaseDate": {"isoString": f"{release_year}-01-01T00:00:00Z"} if release_year else None,
                            "coverArt": {"sources": [{"url": cover_url}]} if cover_url else {},
                            "visualIdentity": {"image": [{"url": cover_url}]} if cover_url else {},
                        }
                    }
                }
            }
        }
    }
    return f'<html><head></head><body><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></body></html>'


def create_mock_album_embed_html(
    album_id: str = "4m2880jivSbbyEGAKfITCa",
    title: str = "Test Album",
    artist: str = "Test Artist",
    track_count: int = 3,
    cover_url: Optional[str] = "https://i.scdn.co/image/ab67616d0000b273album",
    release_year: Optional[str] = "2024",
) -> str:
    """Constructs Spotify Next.js embed HTML for an album."""
    tracks = []
    for i in range(1, track_count + 1):
        tracks.append({
            "uri": f"spotify:track:track_id_{i}",
            "title": f"Album Track {i}",
            "subtitle": artist,
            "duration": 180000,
        })
    data = {
        "props": {
            "pageProps": {
                "state": {
                    "data": {
                        "entity": {
                            "id": album_id,
                            "title": title,
                            "name": title,
                            "subtitle": artist,
                            "artists": [{"name": artist}],
                            "releaseDate": {"isoString": f"{release_year}-05-01T00:00:00Z"} if release_year else None,
                            "coverArt": {"sources": [{"url": cover_url}]} if cover_url else {},
                            "trackList": tracks,
                        }
                    }
                }
            }
        }
    }
    return f'<html><head></head><body><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></body></html>'


def create_mock_playlist_embed_html(
    playlist_id: str = "37i9dQZF1DXcBWIGoYBM5M",
    title: str = "Test Playlist",
    owner: str = "Spotify",
    track_count: int = 5,
    cover_url: Optional[str] = "https://i.scdn.co/image/ab67616d0000b273playlist",
) -> str:
    """Constructs Spotify Next.js embed HTML for a playlist."""
    tracks = []
    for i in range(1, track_count + 1):
        tracks.append({
            "uri": f"spotify:track:pl_track_id_{i}",
            "title": f"Playlist Song {i}",
            "subtitle": f"Artist {i}",
            "duration": 200000,
        })
    data = {
        "props": {
            "pageProps": {
                "state": {
                    "data": {
                        "entity": {
                            "id": playlist_id,
                            "title": title,
                            "name": title,
                            "subtitle": owner,
                            "owner": {"name": owner},
                            "coverArt": {"sources": [{"url": cover_url}]} if cover_url else {},
                            "trackList": tracks,
                        }
                    }
                }
            }
        }
    }
    return f'<html><head></head><body><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></body></html>'


class MockHTTPResponse:
    """Mock requests.Response for deterministic HTTP test simulation."""
    def __init__(self, status_code: int = 200, text: str = "", content: bytes = b"", json_data: Any = None):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode("utf-8")
        self._json_data = json_data

    def json(self):
        if self._json_data is not None:
            return self._json_data
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            http_err = requests.exceptions.HTTPError(f"HTTP Error {self.status_code}")
            http_err.response = self
            raise http_err


class MockYoutubeDL:
    """
    Emulates yt_dlp.YoutubeDL without network activity or external subprocesses.
    Produces synthetic MP3 files in the requested temp template path and calls progress hooks.
    """
    def __init__(self, ydl_opts: Optional[Dict[str, Any]] = None, simulate_error: Optional[Exception] = None):
        self.ydl_opts = ydl_opts or {}
        self.simulate_error = simulate_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def extract_info(self, url: str, download: bool = True):
        if self.simulate_error:
            raise self.simulate_error

        # Trigger progress hooks if registered
        hooks = self.ydl_opts.get("progress_hooks", [])
        for hook in hooks:
            hook({
                "status": "downloading",
                "total_bytes": 1024 * 1024 * 3,
                "downloaded_bytes": 1024 * 1024 * 3,
                "speed": 1024 * 1024 * 2,
                "eta": 0,
            })
            hook({"status": "finished"})

        outtmpl = self.ydl_opts.get("outtmpl", "")
        if outtmpl:
            # Render outtmpl template, replacing %(ext)s with mp3 and %(id)s with audio_123
            rendered = outtmpl.replace("%(ext)s", "mp3").replace("%(id)s", "audio_mock")
            rendered_path = Path(rendered)
            create_synthetic_mp3(rendered_path)

        return {"id": "audio_mock", "title": "Mock Audio", "ext": "mp3"}


class IsolatedEnvTestCase(unittest.TestCase):
    """
    Base test case ensuring full isolation:
    - Dedicated temporary directory per test
    - ~/Music redirection to isolated temp directory
    - Safe cleanup on tearDown
    """
    def setUp(self):
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.isolated_root = Path(self.tmp_dir_obj.name).resolve()
        self.music_dir = self.isolated_root / "Music"
        self.music_dir.mkdir(parents=True, exist_ok=True)

        # Patch get_default_music_dir to avoid touching real ~/Music
        self.patcher_music_dir = patch("core.utils.get_default_music_dir", return_value=self.music_dir)
        self.patcher_music_dir.start()

    def tearDown(self):
        self.patcher_music_dir.stop()
        try:
            self.tmp_dir_obj.cleanup()
        except Exception:
            pass
