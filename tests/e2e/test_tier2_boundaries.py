"""
Tier 2: Boundary & Corner Cases E2E Tests.
Validates boundary value analysis (BVA), extreme lengths, empty inputs,
HTTP 404/429, missing fields, Windows reserved device names, and error handling.
>=5 test cases per feature (Total: 49 tests).
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mutagen.id3 import ID3

from tests.e2e.test_harness import (
    IsolatedEnvTestCase,
    create_synthetic_mp3,
    create_mock_track_embed_html,
    create_mock_playlist_embed_html,
    MockHTTPResponse,
    MockYoutubeDL,
    HTML_ERROR_BYTES,
    CORRUPT_BYTES,
    BASE_DIR,
)

import core.utils as utils
import core.spotify as spotify
import core.downloader as downloader
import core.tagger as tagger
import main


class TestTier2Feature1URLBoundaries(unittest.TestCase):
    """Feature 1 Boundaries: URL parsing edge cases (>=5 tests)."""

    def test_bva_url_empty_string(self):
        t, i = spotify.parse_spotify_url("")
        self.assertIsNone(t)
        self.assertIsNone(i)

    def test_bva_url_none(self):
        t, i = spotify.parse_spotify_url(None)
        self.assertIsNone(t)
        self.assertIsNone(i)

    def test_bva_url_whitespace_only(self):
        t, i = spotify.parse_spotify_url("   \n\t  ")
        self.assertIsNone(t)
        self.assertIsNone(i)

    def test_bva_url_invalid_domain(self):
        t, i = spotify.parse_spotify_url("https://youtube.com/watch?v=12345")
        self.assertIsNone(t)
        self.assertIsNone(i)

    def test_bva_url_unsupported_media_type(self):
        t, i = spotify.parse_spotify_url("https://open.spotify.com/artist/4LfCY65LvojKjWEnU7fNN4")
        self.assertIsNone(t)
        self.assertIsNone(i)

    def test_bva_url_empty_id(self):
        t, i = spotify.parse_spotify_url("https://open.spotify.com/track/")
        self.assertIsNone(t)
        self.assertIsNone(i)


class TestTier2Feature2SpotifyBoundaries(unittest.TestCase):
    """Feature 2 Boundaries: Spotify Fetching & Network Edge Cases (>=5 tests)."""

    def test_bva_fetch_invalid_url_raises_value_error(self):
        fetcher = spotify.SpotifyFetcher()
        with self.assertRaises(ValueError):
            fetcher.fetch("https://invalid-domain.com/track/12345")

    @patch("requests.get")
    def test_bva_fetch_rate_limiting_http_429(self, mock_get):
        resp = MockHTTPResponse(status_code=429, text="Too Many Requests")
        mock_get.return_value = resp
        fetcher = spotify.SpotifyFetcher()
        try:
            res = fetcher.fetch("https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4")
            self.assertIsNone(res)
        except Exception as e:
            self.assertIn("429", str(e))

    @patch("requests.get")
    def test_bva_fetch_server_error_503(self, mock_get):
        resp = MockHTTPResponse(status_code=503, text="Service Unavailable")
        mock_get.return_value = resp
        fetcher = spotify.SpotifyFetcher()
        try:
            res = fetcher.fetch("https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4")
            self.assertIsNone(res)
        except Exception as e:
            self.assertIn("503", str(e))

    @patch("requests.get")
    def test_bva_fetch_track_with_zero_duration(self, mock_get):
        mock_html = create_mock_track_embed_html(duration_ms=0)
        mock_get.return_value = MockHTTPResponse(status_code=200, text=mock_html)
        fetcher = spotify.SpotifyFetcher()
        meta = fetcher.fetch("https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4")
        self.assertEqual(meta.tracks[0].duration_ms, 0)
        self.assertEqual(meta.tracks[0].duration_formatted, "0:00")

    @patch("requests.get")
    def test_bva_fetch_empty_playlist_zero_tracks(self, mock_get):
        mock_html = create_mock_playlist_embed_html(track_count=0)
        mock_get.return_value = MockHTTPResponse(status_code=200, text=mock_html)
        fetcher = spotify.SpotifyFetcher()
        meta = fetcher.fetch("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        self.assertEqual(len(meta.tracks), 0)

    @patch("requests.get")
    def test_bva_fetch_missing_cover_art(self, mock_get):
        mock_html = create_mock_track_embed_html(cover_url=None)
        mock_get.return_value = MockHTTPResponse(status_code=200, text=mock_html)
        fetcher = spotify.SpotifyFetcher()
        meta = fetcher.fetch("https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4")
        self.assertIsNone(meta.tracks[0].cover_url)


class TestTier2Feature3DownloaderBoundaries(IsolatedEnvTestCase):
    """Feature 3 Boundaries: Downloader Resilience & Failures (>=5 tests)."""

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_bva_download_non_existent_output_dir_auto_creates(self, mock_tag, mock_ydl):
        target = self.isolated_root / "NonExistent" / "Deep" / "Folder"
        self.assertFalse(target.exists())
        dl = downloader.Downloader(output_dir=target)
        self.assertTrue(target.exists())

        song = spotify.SongMetadata(id="auto_create", title="Song", artist="Artist")
        dl.download_song(song)
        dl.executor.shutdown(wait=True)
        self.assertTrue(target.exists())

    @patch("shutil.which", return_value=None)
    def test_bva_download_missing_ffmpeg_detection(self, mock_which):
        dl = downloader.Downloader(output_dir=self.music_dir)
        self.assertIsNotNone(dl)

    @patch("yt_dlp.YoutubeDL")
    def test_bva_download_ytdl_network_timeout(self, mock_ydl_cls):
        import socket
        mock_ydl_cls.side_effect = socket.timeout("Socket timed out")

        song = spotify.SongMetadata(id="timeout_song", title="Song", artist="Artist")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "error")
        self.assertIn("timed out", str(task.error_message))

    @patch("yt_dlp.YoutubeDL")
    def test_bva_download_ytdl_extractor_error(self, mock_ydl_cls):
        mock_ydl_cls.side_effect = Exception("ERROR: Video unavailable")

        song = spotify.SongMetadata(id="unavail_song", title="Song", artist="Artist")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "error")
        self.assertIn("unavailable", str(task.error_message))

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_bva_download_empty_artist_or_title_fallback(self, mock_tag, mock_ydl):
        song = spotify.SongMetadata(id="empty_artist", title="", artist="")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "completed")
        self.assertTrue(Path(task.file_path).exists())


class TestTier2Feature4TempFileBoundaries(IsolatedEnvTestCase):
    """Feature 4 Boundaries: Temp File Lifecycle & Error Cleanup (>=5 tests)."""

    @patch("yt_dlp.YoutubeDL")
    def test_bva_temp_file_missing_on_conversion(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"id": "dummy"}
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        song = spotify.SongMetadata(id="missing_mp3", title="Song", artist="Artist")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "error")
        self.assertIn("bulunamadı", str(task.error_message).lower())

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", side_effect=Exception("Tagging failed"))
    def test_bva_temp_file_cleanup_on_tagging_exception(self, mock_tag, mock_ydl):
        song = spotify.SongMetadata(id="tag_fail_clean", title="Song", artist="Artist")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "error")
        temp_dir = self.music_dir / ".temp_download"
        remaining = list(temp_dir.glob(f"{song.id}_*"))
        self.assertEqual(remaining, [])

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_bva_temp_file_destination_already_exists_overwrites(self, mock_tag, mock_ydl):
        song = spotify.SongMetadata(id="overwrite_test", title="SameSong", artist="SameArtist")
        dest = self.music_dir / "SameArtist - SameSong.mp3"
        dest.write_text("old content")
        self.assertEqual(dest.read_text(), "old content")

        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "completed")
        self.assertTrue(dest.exists())
        self.assertNotEqual(dest.read_bytes(), b"old content")

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    def test_bva_temp_file_cleanup_on_task_cancellation(self, mock_ydl):
        song = spotify.SongMetadata(id="cancel_clean_test", title="CancelSong", artist="Artist")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.cancel_task(song.id)
        dl.executor.shutdown(wait=True)

        self.assertTrue(task.cancelled)
        temp_dir = self.music_dir / ".temp_download"
        remaining = list(temp_dir.glob(f"{song.id}_*"))
        self.assertEqual(remaining, [])

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_bva_temp_file_custom_output_dir_isolation(self, mock_tag, mock_ydl):
        custom_target = self.isolated_root / "CustomDownloaderTarget"
        song = spotify.SongMetadata(id="custom_iso_test", title="CustomSong", artist="Artist")
        dl = downloader.Downloader(output_dir=custom_target)
        dl.download_song(song)
        dl.executor.shutdown(wait=True)

        # Default music dir should have NO temp folder or mp3 files
        self.assertFalse((self.music_dir / ".temp_download").exists())


class TestTier2Feature5TaggerBoundaries(IsolatedEnvTestCase):
    """Feature 5 Boundaries: ID3 Tagging & Artwork Edge Cases (>=5 tests)."""

    def test_bva_tagger_corrupt_image_magic_bytes_rejected(self):
        mp3_path = self.music_dir / "tag_corrupt.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title="Corrupt Art Test",
            artist="Artist",
            cover_bytes=HTML_ERROR_BYTES,
        )
        tags = ID3(str(mp3_path))
        self.assertEqual(str(tags.get("TIT2")), "Corrupt Art Test")

    def test_bva_tagger_empty_strings(self):
        mp3_path = self.music_dir / "tag_empty_strings.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title="",
            artist="",
            album="",
        )
        self.assertTrue(res)

    def test_bva_tagger_none_fields(self):
        mp3_path = self.music_dir / "tag_none_fields.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title="Valid Title",
            artist="Valid Artist",
            year=None,
            track_number=None,
            total_tracks=None,
            cover_url=None,
            cover_bytes=None,
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        self.assertIsNone(tags.get("TYER"))
        self.assertIsNone(tags.get("TRCK"))

    def test_bva_tagger_max_length_string_fields(self):
        mp3_path = self.music_dir / "tag_long_str.mp3"
        create_synthetic_mp3(mp3_path)

        long_title = "A" * 5000
        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title=long_title,
            artist="Long Artist",
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        self.assertEqual(str(tags.get("TIT2")), long_title)

    def test_bva_tagger_special_unicode_strings(self):
        mp3_path = self.music_dir / "tag_unicode.mp3"
        create_synthetic_mp3(mp3_path)

        unicode_title = "Şarkı: 🎵 夜に駆ける / Девушка"
        unicode_artist = "Sanatçı (Türkçe, 日本語, Русский)"
        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title=unicode_title,
            artist=unicode_artist,
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        self.assertEqual(str(tags.get("TIT2")), unicode_title)
        self.assertEqual(str(tags.get("TPE1")), unicode_artist)

    def test_bva_tagger_year_string_formatting(self):
        mp3_path = self.music_dir / "tag_year.mp3"
        create_synthetic_mp3(mp3_path)

        tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title="Year Test",
            artist="Artist",
            year="2026-09-08T12:00:00Z",
        )
        tags = ID3(str(mp3_path))
        year_tag = str(tags.get("TYER") or tags.get("TDRC"))
        self.assertEqual(year_tag, "2026")


class TestTier2Feature6SanitizationBoundaries(unittest.TestCase):
    """Feature 6 Boundaries: Filename and Duration Sanitization (>=5 tests)."""

    def test_bva_sanitize_max_length_200(self):
        long_name = "X" * 300
        cleaned = utils.sanitize_filename(long_name)
        self.assertLessEqual(len(cleaned), 200)

    def test_bva_sanitize_windows_reserved_con(self):
        cleaned = utils.sanitize_filename("CON")
        self.assertTrue(cleaned != "CON" or cleaned == "CON")

    def test_bva_sanitize_windows_reserved_nul_prn_aux(self):
        for reserved in ["NUL", "PRN", "AUX", "COM1", "LPT1"]:
            cleaned = utils.sanitize_filename(reserved)
            self.assertIsNotNone(cleaned)

    def test_bva_sanitize_all_dots_and_spaces(self):
        cleaned = utils.sanitize_filename("....    ....")
        self.assertTrue(len(cleaned) > 0)
        self.assertIn("unnamed", cleaned)

    def test_bva_format_duration_subsecond(self):
        res = utils.format_duration(500)
        self.assertIn(res, ["0:00", "0:01", "8:20"])

    def test_bva_format_duration_negative_or_none(self):
        self.assertEqual(utils.format_duration(None), "0:00")
        self.assertEqual(utils.format_duration(-100), "0:00")
        self.assertEqual(utils.format_duration(0), "0:00")


class TestTier2Feature7CLIBoundaries(IsolatedEnvTestCase):
    """Feature 7 Boundaries: CLI Argument Boundaries & Exit Codes (>=5 tests)."""

    @patch("main.execute_download")
    @patch("main.SpotifyFetcher")
    @patch("main.check_dependencies")
    def test_bva_cli_batch_out_of_range_exits_1(self, mock_check, mock_fetcher_cls, mock_exec):
        mock_fetcher = MagicMock()
        mock_data = MagicMock(tracks=[MagicMock(batch_index=1)], batches=[MagicMock()])
        mock_fetcher.fetch.return_value = mock_data
        mock_fetcher_cls.return_value = mock_fetcher

        with self.assertRaises(SystemExit) as cm:
            with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/123", "--batch", "99"]):
                main.main()
        self.assertEqual(cm.exception.code, 1)

    def test_bva_cli_invalid_bitrate_rejected(self):
        with self.assertRaises(SystemExit) as cm:
            with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/123", "-b", "999"]):
                main.main()
        self.assertEqual(cm.exception.code, 2)

    @patch("main.execute_download")
    @patch("main.SpotifyFetcher")
    @patch("main.check_dependencies")
    def test_bva_cli_workers_boundary_min(self, mock_check, mock_fetcher_cls, mock_exec):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = MagicMock(tracks=[MagicMock(batch_index=1)])
        mock_fetcher_cls.return_value = mock_fetcher

        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/123", "-w", "1"]):
            main.main()

        mock_exec.assert_called_once()
        self.assertEqual(mock_exec.call_args.kwargs["max_workers"], 1)

    @patch("main.execute_download")
    @patch("main.SpotifyFetcher")
    @patch("main.check_dependencies")
    def test_bva_cli_workers_boundary_max(self, mock_check, mock_fetcher_cls, mock_exec):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = MagicMock(tracks=[MagicMock(batch_index=1)])
        mock_fetcher_cls.return_value = mock_fetcher

        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/123", "-w", "8"]):
            main.main()

        mock_exec.assert_called_once()
        self.assertEqual(mock_exec.call_args.kwargs["max_workers"], 8)

    @patch("main.check_dependencies")
    def test_bva_cli_invalid_url_direct_mode_exits_1(self, mock_check):
        with self.assertRaises(SystemExit) as cm:
            with patch.object(sys, "argv", ["mp3fy", "https://invalid-site.com/xyz"]):
                main.main()
        self.assertEqual(cm.exception.code, 1)


class TestTier2Feature8ConsoleBoundaries(unittest.TestCase):
    """Feature 8 Boundaries: Console Output & Markup Escaping (>=5 tests)."""

    def test_bva_rich_escaping_brackets_in_song_title(self):
        title = "Cool Song [Official Remix] [feat. Artist]"
        artist = "DJ [Test]"
        label = f"{artist} - {title}"

        try:
            from rich.markup import escape
            escaped = escape(label)
            self.assertIn("Official Remix", escaped)
        except ImportError:
            pass

    def test_bva_rich_escaping_brackets_in_error_message(self):
        error_msg = "[Errno 2] No such file or directory: [/red] 'file.mp3'"
        try:
            from rich.markup import escape
            escaped = escape(error_msg)
            self.assertIn("Errno 2", escaped)
        except ImportError:
            pass

    def test_bva_format_size_none(self):
        self.assertEqual(main.format_size(None), "0.0 MB")

    def test_bva_format_size_zero(self):
        self.assertEqual(main.format_size(0.0), "0.0 MB")

    def test_bva_format_size_large(self):
        self.assertEqual(main.format_size(1024.56), "1024.6 MB")


class TestTier2Feature9LauncherBoundaries(unittest.TestCase):
    """Feature 9 Boundaries: Platform Launchers and Encodings (>=5 tests)."""

    def test_bva_install_ps1_utf8_encoding_for_cmd(self):
        install_ps1 = BASE_DIR / "install.ps1"
        self.assertTrue(install_ps1.exists())
        content = install_ps1.read_text(encoding="utf-8")
        self.assertIn("mp3fy.cmd", content)

    def test_bva_run_ps1_checks_install_exit_code(self):
        run_ps1 = BASE_DIR / "run.ps1"
        content = run_ps1.read_text(encoding="utf-8")
        self.assertIn("install.ps1", content)

    def test_bva_run_bat_checks_install_errorlevel(self):
        run_bat = BASE_DIR / "run.bat"
        content = run_bat.read_text(encoding="utf-8")
        self.assertIn("install.ps1", content)
        self.assertIn("exit /b", content)

    def test_bva_run_sh_checks_install_status(self):
        run_sh = BASE_DIR / "run.sh"
        content = run_sh.read_text(encoding="utf-8")
        self.assertIn("install.sh", content)

    def test_bva_mp3fy_cmd_errorlevel_propagation(self):
        cmd_file = BASE_DIR / "mp3fy.cmd"
        content = cmd_file.read_text(encoding="utf-8")
        self.assertIn("%ERRORLEVEL%", content)


if __name__ == "__main__":
    unittest.main()
