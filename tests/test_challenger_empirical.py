"""
Empirical stress-testing harness created by teamwork_preview_challenger_m1_2.
Validates Downloader and Tagger against 5 critical review criteria:
1. Downloader pre-flight (FFmpeg missing)
2. Temp file isolation (Concurrent downloads & race condition detection)
3. Zero-byte file handling & cleanup
4. Tagger magic byte validation (HTML 404, corrupt blobs, PNG, JPEG, WebP)
5. Tag formatting (4-digit TYER & idempotent track numbering)
"""

import os
import sys
import time
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core import downloader, tagger, spotify
from core.downloader import Downloader, find_ffmpeg
from core.spotify import SongMetadata
from mutagen.id3 import ID3
from tests.e2e.test_harness import MockYoutubeDL, create_synthetic_mp3


class TestDownloaderPreflight(unittest.TestCase):
    """1. Downloader pre-flight check when FFmpeg is not installed."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_preflight_when_ffmpeg_truly_missing(self):
        """When FFmpeg is not installed anywhere on the system, task fails cleanly upfront."""
        song = SongMetadata(id="pf_missing", title="Song", artist="Artist")

        with patch("core.downloader.find_ffmpeg", return_value=None):
            dl = Downloader(output_dir=self.temp_dir)
            self.assertIsNone(dl.ffmpeg_bin)
            task = dl.download_song(song)
            dl.executor.shutdown(wait=True)

            self.assertEqual(task.status, "error")
            self.assertIn("FFmpeg bulunamadı", task.error_message)

    def test_preflight_when_only_shutil_which_mocked(self):
        """
        Demonstrates that mocking only shutil.which falls back to candidate paths on disk.
        If host has /usr/bin/ffmpeg or ~/.local/bin/ffmpeg, find_ffmpeg still finds it.
        """
        with patch("shutil.which", return_value=None):
            found = find_ffmpeg()
            # If the host system has FFmpeg in candidates, it will be found despite shutil.which=None
            if found:
                self.assertTrue(Path(found).exists())
                self.assertTrue(Path(found).is_file())


class TestTempFileIsolation(unittest.TestCase):
    """2. Temp file isolation across concurrent download threads."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_distinct_songs_unique_templates(self):
        """Concurrent download threads for distinct songs use unique temp file paths."""
        dl = Downloader(output_dir=self.temp_dir, max_workers=4)
        captured_templates = []
        lock = threading.Lock()

        class TemplateTrackerMockYDL(MockYoutubeDL):
            def __init__(self, ydl_opts=None, simulate_error=None):
                super().__init__(ydl_opts, simulate_error)
                with lock:
                    captured_templates.append(self.ydl_opts.get("outtmpl"))

        with patch("yt_dlp.YoutubeDL", side_effect=TemplateTrackerMockYDL):
            songs = [
                SongMetadata(id=f"iso_track_{i}", title=f"Title {i}", artist="Artist")
                for i in range(8)
            ]
            tasks = dl.download_playlist(songs)
            dl.executor.shutdown(wait=True)

        self.assertEqual(len(captured_templates), 8)
        self.assertEqual(len(set(captured_templates)), 8)
        for t in tasks:
            self.assertEqual(t.status, "completed")

    def test_concurrent_same_song_id_race_condition(self):
        """
        Empirically tests the race condition in core/downloader.py:
        line 373: 'for temp_f in temp_dir.glob(f\"{song.id}_*\"): temp_f.unlink()'
        When two concurrent workers download the same song.id, the first worker to finish
        deletes the sibling worker's in-flight temp file!
        """
        dl = Downloader(output_dir=self.temp_dir, max_workers=2)
        barrier = threading.Barrier(2)

        class SynchronizedMockYDL(MockYoutubeDL):
            def extract_info(self, url, download=True):
                outtmpl = self.ydl_opts.get("outtmpl", "")
                rendered = outtmpl.replace("%(ext)s", "mp3").replace("%(id)s", "audio_mock")
                rendered_path = Path(rendered)
                create_synthetic_mp3(rendered_path)

                thread_name = threading.current_thread().name
                barrier.wait()  # Both files exist at this moment

                if "1" in thread_name:
                    time.sleep(0.01)  # Thread 1 proceeds and runs finally cleanup
                else:
                    time.sleep(0.4)   # Thread 2 is delayed while Thread 1 cleans up

                return {"id": "audio_mock", "title": "Mock Audio", "ext": "mp3"}

        with patch("yt_dlp.YoutubeDL", side_effect=SynchronizedMockYDL):
            song1 = SongMetadata(id="race_song", title="Race Title", artist="Race Artist")
            song2 = SongMetadata(id="race_song", title="Race Title", artist="Race Artist")

            task1 = dl.download_song(song1)
            task2 = dl.download_song(song2)
            dl.executor.shutdown(wait=True)

            # Check that neither task failed due to sibling collision and both completed cleanly
            statuses = [task1.status, task2.status]
            errors = [task1.error_message, task2.error_message]
            sibling_collision = "error" in statuses and any(
                "Dönüştürülen MP3 dosyası bulunamadı" in str(e) for e in errors if e
            )
            self.assertFalse(
                sibling_collision,
                f"Sibling race condition collision detected: statuses={statuses}, errors={errors}"
            )
            self.assertEqual(
                statuses,
                ["completed", "completed"],
                f"Expected both concurrent tasks to complete, got {statuses}"
            )


class TestZeroByteFileHandling(unittest.TestCase):
    """3. Zero-byte file detection and cleanup."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_zero_byte_file_caught_and_cleaned(self):
        """Verify 0-byte corrupt files are caught and cleaned up from the temp directory."""
        dl = Downloader(output_dir=self.temp_dir)

        class ZeroByteMockYDL(MockYoutubeDL):
            def extract_info(self, url, download=True):
                outtmpl = self.ydl_opts.get("outtmpl", "")
                rendered = outtmpl.replace("%(ext)s", "mp3").replace("%(id)s", "audio_mock")
                rendered_path = Path(rendered)
                rendered_path.touch()  # Creates a 0-byte file
                return {"id": "audio_mock", "title": "Mock Audio", "ext": "mp3"}

        with patch("yt_dlp.YoutubeDL", side_effect=ZeroByteMockYDL):
            song = SongMetadata(id="zero_byte_track", title="Empty Song", artist="Artist")
            task = dl.download_song(song)
            dl.executor.shutdown(wait=True)

            # Task must fail
            self.assertEqual(task.status, "error")

            # Temp directory must be clean (0-byte file removed in finally)
            temp_dir = self.temp_dir / ".temp_download"
            leftovers = list(temp_dir.glob("*zero_byte_track*"))
            self.assertEqual(leftovers, [], f"Residual 0-byte files found: {leftovers}")


class TestTaggerMagicByteValidation(unittest.TestCase):
    """4. Tagger magic byte validation with HTML, corrupt blobs, PNG, JPEG, WebP."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mp3(self, name: str) -> Path:
        mp3 = self.temp_dir / f"{name}.mp3"
        create_synthetic_mp3(mp3)
        return mp3

    def test_html_404_rejected_and_mp3_valid(self):
        """HTML 404 response is rejected from APIC; MP3 remains valid with text tags."""
        mp3 = self._create_mp3("test_html404")
        html_bytes = b"<!DOCTYPE html><html><head><title>404 Not Found</title></head><body>Error 404</body></html>"

        ok = tagger.apply_id3_tags(
            mp3_path=mp3,
            title="Valid Title",
            artist="Valid Artist",
            cover_bytes=html_bytes,
        )
        self.assertTrue(ok)

        tags = ID3(str(mp3))
        self.assertEqual(tags.get("TIT2").text[0], "Valid Title")
        self.assertEqual(tags.get("TPE1").text[0], "Valid Artist")
        # APIC frame must NOT exist
        apic = tags.get("APIC:Cover") or tags.get("APIC:")
        self.assertIsNone(apic, "APIC frame should not be created for HTML content")

    def test_corrupt_binary_blob_rejected_and_mp3_valid(self):
        """Corrupt binary garbage is rejected from APIC; MP3 remains valid with text tags."""
        mp3 = self._create_mp3("test_corrupt_blob")
        garbage = bytes([i % 256 for i in range(500)])

        ok = tagger.apply_id3_tags(
            mp3_path=mp3,
            title="Valid Title",
            artist="Valid Artist",
            cover_bytes=garbage,
        )
        self.assertTrue(ok)

        tags = ID3(str(mp3))
        apic = tags.get("APIC:Cover") or tags.get("APIC:")
        self.assertIsNone(apic, "APIC frame should not be created for random binary junk")

    def test_png_accepted_with_apic(self):
        """Valid PNG magic bytes create image/png APIC frame."""
        mp3 = self._create_mp3("test_png")
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00"
            b"\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        ok = tagger.apply_id3_tags(
            mp3_path=mp3,
            title="PNG Track",
            artist="PNG Artist",
            cover_bytes=png_bytes,
        )
        self.assertTrue(ok)

        tags = ID3(str(mp3))
        apic = tags.get("APIC:Cover")
        self.assertIsNotNone(apic)
        self.assertEqual(apic.mime, "image/png")
        self.assertEqual(apic.data, png_bytes)

    def test_jpeg_accepted_with_apic(self):
        """Valid JPEG magic bytes create image/jpeg APIC frame."""
        mp3 = self._create_mp3("test_jpeg")
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\xff\xd9"

        ok = tagger.apply_id3_tags(
            mp3_path=mp3,
            title="JPEG Track",
            artist="JPEG Artist",
            cover_bytes=jpeg_bytes,
        )
        self.assertTrue(ok)

        tags = ID3(str(mp3))
        apic = tags.get("APIC:Cover")
        self.assertIsNotNone(apic)
        self.assertEqual(apic.mime, "image/jpeg")
        self.assertEqual(apic.data, jpeg_bytes)

    def test_webp_accepted_with_apic(self):
        """Valid WebP magic bytes create image/webp APIC frame."""
        mp3 = self._create_mp3("test_webp")
        webp_bytes = b"RIFF\x24\x00\x00\x00WEBPVP8 \x18\x00\x00\x000\x01\x00\x9d\x01*\x01\x00\x01\x00\x02\x004%\xa4%0\x00\xfe\xff\xfd\x00\x00\x00"

        ok = tagger.apply_id3_tags(
            mp3_path=mp3,
            title="WebP Track",
            artist="WebP Artist",
            cover_bytes=webp_bytes,
        )
        self.assertTrue(ok)

        tags = ID3(str(mp3))
        apic = tags.get("APIC:Cover")
        self.assertIsNotNone(apic)
        self.assertEqual(apic.mime, "image/webp")
        self.assertEqual(apic.data, webp_bytes)


class TestTagFormatting(unittest.TestCase):
    """5. Tag formatting: 4-digit release years (TYER) and idempotent track numbering."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mp3(self, name: str) -> Path:
        mp3 = self.temp_dir / f"{name}.mp3"
        create_synthetic_mp3(mp3)
        return mp3

    def test_four_digit_year_extraction(self):
        """Verify release dates in various formats are extracted to 4-digit TYER."""
        test_cases = [
            ("2023-11-04", "2023"),
            ("1982-01-01T00:00:00Z", "1982"),
            ("1995", "1995"),
            (2018, "2018"),
            ("Released 2005", "2005"),
        ]
        for idx, (input_year, expected_year) in enumerate(test_cases):
            mp3 = self._create_mp3(f"year_test_{idx}")
            ok = tagger.apply_id3_tags(
                mp3_path=mp3,
                title="Year Track",
                artist="Artist",
                year=input_year,
            )
            self.assertTrue(ok)
            tags = ID3(str(mp3))
            year_tag = tags.get("TYER") or tags.get("TDRC")
            self.assertIsNotNone(year_tag, f"Year tag missing for input: {input_year}")
            self.assertEqual(str(year_tag), expected_year)
            # Verify raw bytes on disk contain TYER frame for ID3v2.3 compliance
            raw_bytes = mp3.read_bytes()
            self.assertIn(b"TYER", raw_bytes)

    def test_idempotent_track_numbering(self):
        """Verify track numbers already formatted as current/total are not duplicated."""
        mp3 = self._create_mp3("idempotent_track")

        # Initial tagging: track 4 of 12
        ok1 = tagger.apply_id3_tags(
            mp3_path=mp3,
            title="Track 4",
            artist="Artist",
            track_number=4,
            total_tracks=12,
        )
        self.assertTrue(ok1)
        tags1 = ID3(str(mp3))
        self.assertEqual(tags1.get("TRCK").text[0], "4/12")

        # Second tagging with pre-formatted track string "4/12" and total_tracks=12
        ok2 = tagger.apply_id3_tags(
            mp3_path=mp3,
            title="Track 4",
            artist="Artist",
            track_number="4/12",
            total_tracks=12,
        )
        self.assertTrue(ok2)
        tags2 = ID3(str(mp3))
        # Must still be "4/12", NOT "4/12/12"
        self.assertEqual(tags2.get("TRCK").text[0], "4/12")

    def test_repeated_tagging_frame_clearing(self):
        """Verify repeated calls to apply_id3_tags cleanly replace frames without duplicating."""
        mp3 = self._create_mp3("repeated_tagging")

        tagger.apply_id3_tags(mp3, title="Title 1", artist="Artist 1", year="2020", track_number=1)
        tagger.apply_id3_tags(mp3, title="Title 2", artist="Artist 2", year="2021", track_number=2)

        tags = ID3(str(mp3))
        self.assertEqual(tags.get("TIT2").text[0], "Title 2")
        self.assertEqual(tags.get("TPE1").text[0], "Artist 2")
        year_tag = tags.get("TYER") or tags.get("TDRC")
        self.assertEqual(str(year_tag), "2021")
        self.assertEqual(tags.get("TRCK").text[0], "2")
        self.assertEqual(len(tags.getall("TIT2")), 1)
        self.assertEqual(len(tags.getall("TPE1")), 1)


if __name__ == "__main__":
    unittest.main()
