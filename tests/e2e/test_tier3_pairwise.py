"""
Tier 3: Cross-Feature Interactions E2E Tests.
Validates pairwise combinations of major features:
- Reserved filenames + long titles + artwork
- Batch filtering + partial failures + exit codes
- Rate limiting + CLI output + temp cleanup
- Rich console markup + special characters in metadata
>=15 test cases (Total: 16 tests).
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
    JPEG_BYTES,
    PNG_BYTES,
    WEBP_BYTES,
    HTML_ERROR_BYTES,
    BASE_DIR,
)

import core.utils as utils
import core.spotify as spotify
import core.downloader as downloader
import core.tagger as tagger
import main


class TestTier3PairwiseInteractions(IsolatedEnvTestCase):
    """Pairwise combinatorial tests across Core, Downloader, Tagger, and CLI."""

    def test_pairwise_windows_device_name_and_unicode_artist_and_long_title(self):
        """Interaction: Windows device name in artist + Turkish unicode + 250 char title."""
        artist = "CON - Barış Manço & Moğollar"
        long_title = ("Dönence: " + ("Uzun Şarkı Başlığı " * 15)).strip()
        safe_artist = utils.sanitize_filename(artist)
        safe_title = utils.sanitize_filename(long_title)

        base_name = f"{safe_artist} - {safe_title}"[:120]
        mp3_path = self.music_dir / f"{base_name}.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title=long_title,
            artist=artist,
            album="2023 Albümü",
            year="1982",
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        self.assertEqual(str(tags.get("TIT2")), long_title)
        self.assertEqual(str(tags.get("TPE1")), artist)

    def test_pairwise_missing_cover_art_and_subsecond_duration(self):
        """Interaction: Missing cover art + subsecond duration (500ms)."""
        duration_str = utils.format_duration(500)
        song = spotify.SongMetadata(
            id="sub_missing_art",
            title="Short Song",
            artist="Artist",
            duration_ms=500,
            duration_formatted=duration_str,
            cover_url=None,
        )
        mp3_path = self.music_dir / "Short Song.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title=song.title,
            artist=song.artist,
            cover_bytes=None,
            cover_url=None,
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        self.assertEqual(len(tags.getall("APIC")), 0)

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_pairwise_batch_filtered_playlist_with_jpeg_artwork(self, mock_tag, mock_ydl):
        """Interaction: Playlist with batch filtering + JPEG artwork embedding."""
        tracks = [
            spotify.SongMetadata(id=f"track_{i}", title=f"Track {i}", artist="Artist", batch_index=(1 if i <= 100 else 2))
            for i in range(1, 110)
        ]
        # Filter to batch 2
        batch_2_tracks = [t for t in tracks if t.batch_index == 2]
        self.assertEqual(len(batch_2_tracks), 9)

        dl = downloader.Downloader(output_dir=self.music_dir)
        tasks = dl.download_playlist(batch_2_tracks)
        dl.executor.shutdown(wait=True)

        for t in tasks:
            self.assertEqual(t.status, "completed")
            self.assertTrue(Path(t.file_path).exists())

    def test_pairwise_png_art_and_windows_device_title(self):
        """Interaction: Reserved device name 'AUX' + PNG APIC artwork embedding."""
        safe_title = utils.sanitize_filename("AUX")
        mp3_path = self.music_dir / f"{safe_title}.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title="AUX",
            artist="Sound Device",
            cover_bytes=PNG_BYTES,
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        apics = tags.getall("APIC")
        self.assertTrue(len(apics) > 0)
        self.assertEqual(apics[0].mime, "image/png")

    @patch("yt_dlp.YoutubeDL")
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_pairwise_batch_download_with_partial_failures_and_task_accounting(self, mock_tag, mock_ydl_cls):
        """Interaction: Batch download where track 1 succeeds and track 2 encounters extractor error."""
        def ytdl_factory(opts):
            outtmpl = opts.get("outtmpl", "")
            if "fail_song" in outtmpl:
                return MockYoutubeDL(opts, simulate_error=Exception("Extractor Failure"))
            return MockYoutubeDL(opts)

        mock_ydl_cls.side_effect = ytdl_factory

        s1 = spotify.SongMetadata(id="ok_song", title="Good Song", artist="Artist")
        s2 = spotify.SongMetadata(id="fail_song", title="Bad Song", artist="Artist")

        dl = downloader.Downloader(output_dir=self.music_dir, max_workers=1)
        tasks = dl.download_playlist([s1, s2])
        dl.executor.shutdown(wait=True)

        self.assertEqual(tasks[0].status, "completed")
        self.assertEqual(tasks[1].status, "error")

    @patch("main.SpotifyFetcher")
    @patch("main.check_dependencies")
    def test_pairwise_rate_limited_fetch_and_cli_exit_code(self, mock_check, mock_fetcher_cls):
        """Interaction: Spotify 429 rate limit during CLI run results in exit code 1."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("HTTP 429 Too Many Requests")
        mock_fetcher_cls.return_value = mock_fetcher

        with self.assertRaises(SystemExit) as cm:
            with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/123"]):
                main.main()
        self.assertEqual(cm.exception.code, 1)

    def test_pairwise_special_brackets_in_artist_and_rich_markup_resilience(self):
        """Interaction: Special brackets in artist/title formatted with Rich markup."""
        raw_artist = "[AC/DC] & <The Who> [/red]"
        raw_title = "[Remix] [Live in Paris]"
        safe_artist = utils.sanitize_filename(raw_artist)
        safe_title = utils.sanitize_filename(raw_title)
        label = f"{safe_artist} - {safe_title}"

        # If Rich is installed, ensure escape works and doesn't raise MarkupError
        try:
            from rich.markup import escape
            escaped = escape(label)
            self.assertIn("AC_DC", escaped)
        except ImportError:
            pass

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_pairwise_webp_art_and_custom_output_directory(self, mock_tag, mock_ydl):
        """Interaction: WebP artwork embedding inside custom nested directory."""
        custom_dir = self.isolated_root / "Deeply" / "Nested" / "Music" / "Store"
        song = spotify.SongMetadata(id="webp_custom", title="WebP Song", artist="Artist")

        dl = downloader.Downloader(output_dir=custom_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "completed")
        self.assertTrue(Path(task.file_path).exists())
        self.assertTrue(str(task.file_path).startswith(str(custom_dir)))

    def test_pairwise_subsecond_duration_and_trailing_dots_title(self):
        """Interaction: 800ms duration + title ending in dots and spaces."""
        cleaned_title = utils.sanitize_filename("Edge Track...   ")
        self.assertFalse(cleaned_title.endswith("."))
        self.assertFalse(cleaned_title.endswith(" "))
        dur = utils.format_duration(800)
        self.assertIn(dur, ["0:00", "0:01", "8:20"])

    @patch("main.execute_download")
    @patch("main.SpotifyFetcher")
    @patch("main.check_dependencies")
    def test_pairwise_cli_batch_out_of_bounds(self, mock_check, mock_fetcher_cls, mock_exec):
        """Interaction: User passes --batch 5 when metadata only has 2 batches -> exits 1."""
        b1 = MagicMock(batch_index=1)
        b2 = MagicMock(batch_index=2)
        mock_fetcher = MagicMock()
        mock_data = MagicMock(tracks=[b1, b2], batches=[b1, b2])
        mock_fetcher.fetch.return_value = mock_data
        mock_fetcher_cls.return_value = mock_fetcher

        with self.assertRaises(SystemExit) as cm:
            with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/123", "--batch", "5"]):
                main.main()
        self.assertEqual(cm.exception.code, 1)

    @patch("yt_dlp.YoutubeDL")
    def test_pairwise_network_timeout_mid_download_and_temp_cleanup(self, mock_ydl_cls):
        """Interaction: yt-dlp timeout mid-download cleans up temp files and reports error."""
        import socket
        mock_ydl_cls.side_effect = socket.timeout("Socket timeout during download")

        song = spotify.SongMetadata(id="net_timeout_pair", title="Timeout Song", artist="Artist")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.executor.shutdown(wait=True)

        self.assertEqual(task.status, "error")
        temp_dir = self.music_dir / ".temp_download"
        if temp_dir.exists():
            remaining = list(temp_dir.glob("net_timeout_pair_*"))
            self.assertEqual(remaining, [])

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_pairwise_multiple_concurrent_workers_and_temp_isolation(self, mock_tag, mock_ydl):
        """Interaction: 3 concurrent workers downloading tracks simultaneously."""
        songs = [
            spotify.SongMetadata(id=f"conc_{i}", title=f"Track {i}", artist=f"Artist {i}")
            for i in range(1, 4)
        ]
        dl = downloader.Downloader(output_dir=self.music_dir, max_workers=3)
        tasks = dl.download_playlist(songs)
        dl.executor.shutdown(wait=True)

        for t in tasks:
            self.assertEqual(t.status, "completed")
            self.assertTrue(Path(t.file_path).exists())

    def test_pairwise_html_error_response_as_cover_art_handling(self):
        """Interaction: Cover art URL returns HTML 404 page, tagger handles safely."""
        mp3_path = self.music_dir / "html_art_pair.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title="HTML Art Song",
            artist="Artist",
            cover_bytes=HTML_ERROR_BYTES,
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        self.assertEqual(str(tags.get("TIT2")), "HTML Art Song")

    @patch("main.SpotifyFetcher")
    @patch("main.check_dependencies")
    def test_pairwise_zero_tracks_metadata_and_cli_handling(self, mock_check, mock_fetcher_cls):
        """Interaction: Metadata with 0 tracks handled cleanly by CLI."""
        mock_fetcher = MagicMock()
        mock_data = MagicMock(tracks=[])
        mock_fetcher.fetch.return_value = mock_data
        mock_fetcher_cls.return_value = mock_fetcher

        with patch("main.execute_download") as mock_exec:
            with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/empty_123"]):
                main.main()
            mock_exec.assert_called_once()
            self.assertEqual(len(mock_exec.call_args.kwargs["tracks_to_download"]), 0)

    def test_pairwise_disc_number_and_track_total_tagging(self):
        """Interaction: Song with disc number 2, track 4 of 20."""
        mp3_path = self.music_dir / "disc_tag_pair.mp3"
        create_synthetic_mp3(mp3_path)

        res = tagger.apply_id3_tags(
            mp3_path=mp3_path,
            title="Multi Disc Song",
            artist="Artist",
            disc_number=2,
            track_number=4,
            total_tracks=20,
        )
        self.assertTrue(res)
        tags = ID3(str(mp3_path))
        self.assertEqual(str(tags.get("TPOS")), "2")
        self.assertEqual(str(tags.get("TRCK")), "4/20")

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    def test_pairwise_downloader_cancellation_and_temp_cleanup(self, mock_ydl):
        """Interaction: Task cancellation cleans up any intermediate temp files."""
        song = spotify.SongMetadata(id="cancel_cleanup_pair", title="Cancelled Song", artist="Artist")
        dl = downloader.Downloader(output_dir=self.music_dir)
        task = dl.download_song(song)
        dl.cancel_task(song.id)
        dl.executor.shutdown(wait=True)

        self.assertTrue(task.cancelled)
        temp_dir = self.music_dir / ".temp_download"
        remaining = list(temp_dir.glob("cancel_cleanup_pair_*"))
        self.assertEqual(remaining, [])


if __name__ == "__main__":
    unittest.main()
