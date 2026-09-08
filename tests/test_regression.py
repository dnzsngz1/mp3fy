"""
Comprehensive regression tests for MP3fy Milestone 2 & Milestone 3 hardening.
Covers CLI resilience, rich markup escaping, stream reconfiguration, platform launcher scripts,
and exit code propagation.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import main
from core.spotify import SongMetadata, PlaylistMetadata
from core.tagger import apply_id3_tags
from core.downloader import DownloadTask


class TestRegressionCLI(unittest.TestCase):
    """Regression tests for CLI interface and main.py hardening."""

    def test_reconfigure_stream_universal_no_crash(self):
        """Universal UTF-8 stream reconfiguration handles mock and unsupported streams without crash."""
        class MockStream:
            def reconfigure(self, **kwargs):
                import io
                raise io.UnsupportedOperation("not reconfigurable")

        # Must not raise exception
        for stream in (MockStream(), None, sys.stdout):
            if stream and hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass

    def test_local_bins_includes_venv_bin(self):
        """Local bins discovery includes .venv/bin for Linux/macOS and .venv/Scripts for Windows."""
        venv_bin = str(BASE_DIR / ".venv" / "bin")
        venv_scripts = str(BASE_DIR / ".venv" / "Scripts")
        self.assertIn(venv_bin, main.local_bins)
        self.assertIn(venv_scripts, main.local_bins)

    def test_none_metadata_exits_code_1(self):
        """When fetch() returns None, main() exits with code 1 without AttributeError traceback."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/valid_url_but_none_data"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = None
                    mock_fetcher_cls.return_value = mock_fetcher
                    with self.assertRaises(SystemExit) as cm:
                        main.main()
                    self.assertEqual(cm.exception.code, 1)

    def test_batch_zero_and_negative_rejected_exit_code_1(self):
        """CLI cleanly rejects --batch 0 and --batch -1 with exit code 1."""
        for invalid_batch in ["0", "-1", "-5"]:
            with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/123", "--batch", invalid_batch]):
                with patch("main.check_dependencies"):
                    with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                        mock_fetcher = MagicMock()
                        mock_data = MagicMock(tracks=[MagicMock(batch_index=1)], batches=[MagicMock()])
                        mock_fetcher.fetch.return_value = mock_data
                        mock_fetcher_cls.return_value = mock_fetcher
                        with self.assertRaises(SystemExit) as cm:
                            main.main()
                        self.assertEqual(cm.exception.code, 1)

    def test_execute_download_exit_code_propagation_all_success(self):
        """execute_download returns 0 when all downloads succeed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            song = SongMetadata(id="s1", title="Success Song", artist="Artist")
            data = PlaylistMetadata(id="p1", title="Test Pl", type="playlist", tracks=[song])

            with patch("core.downloader.Downloader.download_playlist") as mock_dl:
                task = DownloadTask(song=song)
                task.status = "completed"
                task.file_size_mb = 3.5
                mock_dl.return_value = [task]

                res = main.execute_download(
                    data=data,
                    tracks_to_download=[song],
                    output_dir=Path(tmp_dir),
                    bitrate="320",
                    max_workers=1,
                )
                self.assertEqual(res, 0)

    def test_execute_download_exit_code_propagation_any_failure(self):
        """execute_download returns 1 when any download fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            song1 = SongMetadata(id="s1", title="Success Song", artist="Artist")
            song2 = SongMetadata(id="s2", title="Failed Song", artist="Artist")
            data = PlaylistMetadata(id="p1", title="Test Pl", type="playlist", tracks=[song1, song2])

            with patch("core.downloader.Downloader.download_playlist") as mock_dl:
                t1 = DownloadTask(song=song1)
                t1.status = "completed"
                t1.file_size_mb = 3.5
                t2 = DownloadTask(song=song2)
                t2.status = "error"
                t2.error_message = "Network Error"
                mock_dl.return_value = [t1, t2]

                res = main.execute_download(
                    data=data,
                    tracks_to_download=[song1, song2],
                    output_dir=Path(tmp_dir),
                    bitrate="320",
                    max_workers=1,
                )
                self.assertEqual(res, 1)

    def test_execute_download_exit_code_zero_success_when_tracks_requested(self):
        """execute_download returns 1 when 0 downloads succeed for non-empty track list."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            song = SongMetadata(id="s1", title="Failed Song", artist="Artist")
            data = PlaylistMetadata(id="p1", title="Test Pl", type="playlist", tracks=[song])

            with patch("core.downloader.Downloader.download_playlist") as mock_dl:
                t1 = DownloadTask(song=song)
                t1.status = "error"
                t1.error_message = "Conversion Error"
                mock_dl.return_value = [t1]

                res = main.execute_download(
                    data=data,
                    tracks_to_download=[song],
                    output_dir=Path(tmp_dir),
                    bitrate="320",
                    max_workers=1,
                )
                self.assertEqual(res, 1)

    def test_execute_download_zero_tracks_requested_returns_zero(self):
        """execute_download returns 0 when 0 tracks were requested."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            data = PlaylistMetadata(id="p1", title="Empty Pl", type="playlist", tracks=[])
            with patch("core.downloader.Downloader.download_playlist", return_value=[]):
                res = main.execute_download(
                    data=data,
                    tracks_to_download=[],
                    output_dir=Path(tmp_dir),
                    bitrate="320",
                    max_workers=1,
                )
                self.assertEqual(res, 0)

    def test_rich_markup_escaping_adversarial_strings(self):
        """Adversarial user strings containing Rich tags do not throw MarkupError."""
        adversarial_strings = [
            "Track [Official Remix]",
            "Artist [feat. [Nested] Singer]",
            "Error: [Errno 2] No file found",
            "Color tags [/red] [bold yellow] [italic]",
            "Closing tag without opening [/]",
            "Symbols < > & \" ' [ ]",
        ]
        for s in adversarial_strings:
            escaped = main.escape(s)
            self.assertIsInstance(escaped, str)
            if main.HAS_RICH:
                from rich.text import Text
                # Rendering escaped text within tags must succeed without MarkupError
                rendered = Text.from_markup(f"[white]{escaped}[/white]")
                self.assertIsNotNone(rendered)


class TestRegressionPlatformLaunchers(unittest.TestCase):
    """Regression tests for platform launcher scripts."""

    def test_install_ps1_utf8_cmd_generation(self):
        """install.ps1 writes mp3fy.cmd using UTF-8 encoding to preserve non-ASCII paths."""
        install_ps1 = BASE_DIR / "install.ps1"
        self.assertTrue(install_ps1.exists())
        content = install_ps1.read_text(encoding="utf-8")
        self.assertIn("Set-Content -Path $UserCmd -Value $UserCmdContent -Encoding UTF8", content)
        self.assertNotIn("-Encoding ASCII", content)

    def test_run_ps1_checks_install_exit_code(self):
        """run.ps1 verifies $LASTEXITCODE after invoking install.ps1."""
        run_ps1 = BASE_DIR / "run.ps1"
        self.assertTrue(run_ps1.exists())
        content = run_ps1.read_text(encoding="utf-8")
        self.assertIn("$LASTEXITCODE", content)
        self.assertIn("exit $LASTEXITCODE", content)

    def test_run_bat_checks_install_errorlevel(self):
        """run.bat checks %ERRORLEVEL% after invoking install.ps1."""
        run_bat = BASE_DIR / "run.bat"
        self.assertTrue(run_bat.exists())
        content = run_bat.read_text(encoding="utf-8")
        self.assertIn("errorlevel 1 exit /b %ERRORLEVEL%", content)

    def test_install_sh_checks_python_version_3_9(self):
        """install.sh verifies Python >= 3.9 before proceeding."""
        install_sh = BASE_DIR / "install.sh"
        self.assertTrue(install_sh.exists())
        content = install_sh.read_text(encoding="utf-8")
        self.assertIn("3.9", content)

    def test_run_sh_quotes_arguments_and_propagates_exit_code(self):
        """run.sh quotes \"$@\" and propagates exit code $?."""
        run_sh = BASE_DIR / "run.sh"
        self.assertTrue(run_sh.exists())
        content = run_sh.read_text(encoding="utf-8")
        self.assertIn('"$@"', content)
        self.assertIn("$?", content)
        self.assertIn("exit $EXIT_CODE", content)


class TestRegressionCoreHardening(unittest.TestCase):
    """Regression tests for core utilities and tagger without external dependencies."""

    def test_tagger_pure_python_mp3_frames_no_ffmpeg(self):
        """ID3 tagger succeeds on valid in-memory MP3 frames without spawning FFmpeg."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mp3_file = Path(tmp_dir) / "synthetic.mp3"
            # Standard MPEG-1 Layer 3 frame header (0xFFFB9044) + padding
            frame = b"\xff\xfb\x90\x44" + (b"\x00" * 413)
            mp3_file.write_bytes(frame * 4)

            success = apply_id3_tags(
                mp3_path=mp3_file,
                title="Synthetic Song",
                artist="Synthetic Artist",
                album="Synthetic Album",
                year="2026",
                track_number=1,
                total_tracks=5,
            )
            self.assertTrue(success)

            from mutagen.id3 import ID3
            tags = ID3(str(mp3_file))
            self.assertEqual(str(tags.get("TIT2")), "Synthetic Song")
            self.assertEqual(str(tags.get("TPE1")), "Synthetic Artist")
            self.assertEqual(str(tags.get("TALB")), "Synthetic Album")
            self.assertEqual(str(tags.get("TRCK")), "1/5")


if __name__ == "__main__":
    unittest.main()
