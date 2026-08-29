"""
Audio Downloader & Converter Engine using yt-dlp, FFmpeg, and Mutagen ID3 Tagger.
"""

import os
import sys
import time
import shutil
import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, Future
import threading

import yt_dlp

from core.spotify import SongMetadata
from core.tagger import apply_id3_tags
from core.utils import sanitize_filename, ensure_directory, get_default_music_dir

logger = logging.getLogger(__name__)


class DownloadTask:
    def __init__(self, song: SongMetadata, output_dir: Optional[Path] = None, bitrate: str = "320"):
        self.song = song
        self.output_dir = output_dir or get_default_music_dir()
        self.bitrate = bitrate
        self.status = "queued"  # queued, searching, downloading, converting, tagging, completed, error, cancelled
        self.progress: float = 0.0
        self.speed: str = ""
        self.eta: str = ""
        self.error_message: Optional[str] = None
        self.file_path: Optional[str] = None
        self.file_size_mb: Optional[float] = None
        self.cancelled = False
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.song.id,
            "title": self.song.title,
            "artist": self.song.artist,
            "album": self.song.album,
            "duration_formatted": self.song.duration_formatted,
            "cover_url": self.song.cover_url,
            "status": self.status,
            "progress": round(self.progress, 1),
            "speed": self.speed,
            "eta": self.eta,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "file_size_mb": round(self.file_size_mb, 2) if self.file_size_mb else None,
        }


class Downloader:
    """
    Manages downloading Spotify songs via yt-dlp, converting to MP3, and applying ID3 metadata.
    """

    def __init__(
        self,
        output_dir: Optional[str | Path] = None,
        bitrate: str = "320",
        max_workers: int = 2,
        on_progress: Optional[Callable[[DownloadTask], None]] = None,
    ):
        self.output_dir = ensure_directory(output_dir or get_default_music_dir())
        self.bitrate = bitrate
        self.max_workers = max_workers
        self.on_progress = on_progress
        self.tasks: Dict[str, DownloadTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._lock = threading.Lock()
        self._futures: Dict[str, Future] = {}

    def set_output_dir(self, output_dir: str | Path):
        self.output_dir = ensure_directory(output_dir)

    def set_bitrate(self, bitrate: str):
        self.bitrate = bitrate

    def cancel_task(self, song_id: str):
        with self._lock:
            task = self.tasks.get(song_id)
            if task:
                task.cancelled = True
                task.status = "cancelled"
                self._notify(task)

    def cancel_all(self):
        with self._lock:
            for task in self.tasks.values():
                if task.status in ["queued", "searching", "downloading", "converting", "tagging"]:
                    task.cancelled = True
                    task.status = "cancelled"
                    self._notify(task)

    def download_song(
        self,
        song: SongMetadata,
        output_dir: Optional[Path] = None,
        bitrate: Optional[str] = None,
    ) -> DownloadTask:
        """
        Submits a single song to the download queue.
        """
        target_dir = output_dir or self.output_dir
        target_bitrate = bitrate or self.bitrate

        with self._lock:
            task = DownloadTask(song, target_dir, target_bitrate)
            self.tasks[song.id] = task
            self._notify(task)

        future = self.executor.submit(self._download_worker, task)
        self._futures[song.id] = future
        return task

    def download_playlist(
        self,
        songs: List[SongMetadata],
        output_dir: Optional[Path] = None,
        bitrate: Optional[str] = None,
    ) -> List[DownloadTask]:
        """
        Submits all songs from a playlist/album to the download queue.
        """
        task_list = []
        for song in songs:
            task = self.download_song(song, output_dir, bitrate)
            task_list.append(task)
        return task_list

    def _notify(self, task: DownloadTask):
        task.updated_at = time.time()
        if self.on_progress:
            try:
                self.on_progress(task)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def _download_worker(self, task: DownloadTask):
        if task.cancelled:
            return

        song = task.song
        task.status = "searching"
        task.progress = 5.0
        self._notify(task)

        # Build clean filename: "Artist - Title.mp3"
        safe_artist = sanitize_filename(song.artist)
        safe_title = sanitize_filename(song.title)
        base_name = f"{safe_artist} - {safe_title}"
        final_mp3_path = task.output_dir / f"{base_name}.mp3"
        temp_dir = task.output_dir / ".temp_download"
        ensure_directory(temp_dir)
        temp_out_tmpl = str(temp_dir / f"{song.id}_%(id)s.%(ext)s")

        # Custom progress hook for yt-dlp
        def ytdl_progress_hook(d):
            if task.cancelled:
                raise Exception("Download cancelled by user.")

            if d["status"] == "downloading":
                task.status = "downloading"
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_bytes = d.get("downloaded_bytes") or 0

                if total_bytes > 0:
                    # Map yt-dlp 0-100% to task 10-85%
                    percent = (downloaded_bytes / total_bytes) * 75.0
                    task.progress = 10.0 + percent

                speed = d.get("speed")
                if speed:
                    task.speed = f"{speed / (1024 * 1024):.1f} MB/s" if speed > 1024 * 1024 else f"{speed / 1024:.0f} KB/s"

                eta = d.get("eta")
                if eta:
                    task.eta = f"{eta}s"

                self._notify(task)

            elif d["status"] == "finished":
                task.status = "converting"
                task.progress = 88.0
                task.speed = ""
                task.eta = ""
                self._notify(task)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": temp_out_tmpl,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": task.bitrate,
                }
            ],
            "progress_hooks": [ytdl_progress_hook],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "default_search": "ytsearch",
        }

        search_query = f"ytsearch1:{song.artist} - {song.title} audio"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                if not info or not info.get("entries") and not info.get("id"):
                    # Fallback search without "audio" suffix
                    search_query_fallback = f"ytsearch1:{song.artist} - {song.title}"
                    info = ydl.extract_info(search_query_fallback, download=True)

            if task.cancelled:
                task.status = "cancelled"
                self._notify(task)
                return

            # Find generated temp mp3 file
            temp_mp3_files = list(temp_dir.glob(f"{song.id}_*.mp3"))
            if not temp_mp3_files:
                raise FileNotFoundError("Dönüştürülen MP3 dosyası bulunamadı.")

            temp_mp3 = temp_mp3_files[0]

            # Tagging phase
            task.status = "tagging"
            task.progress = 92.0
            self._notify(task)

            # Move temp file to final destination
            if final_mp3_path.exists():
                final_mp3_path.unlink()
            shutil.move(str(temp_mp3), str(final_mp3_path))

            # Apply ID3 tags and embed album cover
            apply_id3_tags(
                mp3_path=final_mp3_path,
                title=song.title,
                artist=song.artist,
                album=song.album or song.title,
                year=song.year,
                track_number=song.track_number,
                total_tracks=song.total_tracks,
                cover_url=song.cover_url,
                comment="Downloaded with MP3fy",
            )

            # Finished successfully!
            task.status = "completed"
            task.progress = 100.0
            task.file_path = str(final_mp3_path)
            task.file_size_mb = final_mp3_path.stat().st_size / (1024 * 1024)
            task.speed = ""
            task.eta = ""
            logger.info(f"Successfully downloaded & tagged: {final_mp3_path.name}")
            self._notify(task)

        except Exception as e:
            if task.cancelled:
                task.status = "cancelled"
            else:
                logger.error(f"Error downloading {song.title}: {e}", exc_info=True)
                task.status = "error"
                task.error_message = str(e)
            self._notify(task)
        finally:
            # Clean any residual temp files for this song
            for temp_f in temp_dir.glob(f"{song.id}_*"):
                try:
                    temp_f.unlink()
                except Exception:
                    pass
