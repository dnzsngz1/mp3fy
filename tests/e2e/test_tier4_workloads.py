"""
Tier 4: Realistic Workload Scenarios E2E Tests.
Simulates real-world album, playlist, batch, and interactive CLI download flows
with mocked network and pure-Python deterministic audio generation.
>=5 test cases (Total: 6 tests).
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
    create_mock_album_embed_html,
    create_mock_playlist_embed_html,
    MockHTTPResponse,
    MockYoutubeDL,
    JPEG_BYTES,
    PNG_BYTES,
    BASE_DIR,
)

import core.utils as utils
import core.spotify as spotify
import core.downloader as downloader
import core.tagger as tagger
import main


class TestTier4RealisticWorkloads(IsolatedEnvTestCase):
    """Realistic end-to-end application workloads."""

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("requests.get")
    @patch("main.check_dependencies")
    def test_workload_single_track_full_cli_to_mp3(self, mock_check, mock_get, mock_ydl):
        """Workload 1: User downloads a single track via CLI command with full tagging."""
        track_url = "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4"
        mock_html = create_mock_track_embed_html(
            track_id="4LfCY65LvojKjWEnU7fNN4",
            title="Bohemian Rhapsody",
            artist="Queen",
            duration_ms=354000,
            release_year="1975",
        )

        def mock_requests(url, **kwargs):
            if "embed" in url:
                return MockHTTPResponse(status_code=200, text=mock_html)
            elif "image" in url or "scdn" in url:
                return MockHTTPResponse(status_code=200, content=JPEG_BYTES)
            return MockHTTPResponse(status_code=200, text="")

        mock_get.side_effect = mock_requests

        target_dir = self.music_dir / "SingleTrackWorkload"
        cli_args = [
            "mp3fy",
            track_url,
            "-o", str(target_dir),
            "-b", "320",
            "-w", "1",
        ]

        with patch.object(sys, "argv", cli_args):
            main.main()

        # Verify output file
        expected_file = target_dir / "Queen - Bohemian Rhapsody.mp3"
        self.assertTrue(expected_file.exists(), f"Expected {expected_file} to exist")
        self.assertGreater(expected_file.stat().st_size, 0)

        # Verify ID3 metadata with mutagen
        tags = ID3(str(expected_file))
        self.assertEqual(str(tags.get("TIT2")), "Bohemian Rhapsody")
        self.assertEqual(str(tags.get("TPE1")), "Queen")
        self.assertEqual(str(tags.get("TYER") or tags.get("TDRC")), "1975")
        self.assertEqual(str(tags.get("TRCK")), "1/1")

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("requests.get")
    @patch("main.check_dependencies")
    def test_workload_album_complete_download(self, mock_check, mock_get, mock_ydl):
        """Workload 2: User downloads a complete album with 4 tracks."""
        album_url = "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa"
        mock_html = create_mock_album_embed_html(
            album_id="4m2880jivSbbyEGAKfITCa",
            title="A Night at the Opera",
            artist="Queen",
            track_count=4,
            release_year="1975",
        )

        def mock_requests(url, **kwargs):
            if "embed" in url:
                return MockHTTPResponse(status_code=200, text=mock_html)
            elif "image" in url or "scdn" in url:
                return MockHTTPResponse(status_code=200, content=JPEG_BYTES)
            return MockHTTPResponse(status_code=200, text="")

        mock_get.side_effect = mock_requests

        target_dir = self.music_dir / "AlbumWorkload"
        cli_args = [
            "mp3fy",
            album_url,
            "-o", str(target_dir),
            "-b", "320",
            "-w", "2",
        ]

        with patch.object(sys, "argv", cli_args):
            main.main()

        # Verify all 4 album tracks were generated
        downloaded_files = sorted(list(target_dir.glob("*.mp3")))
        self.assertEqual(len(downloaded_files), 4)

        for idx, mp3_f in enumerate(downloaded_files, start=1):
            tags = ID3(str(mp3_f))
            self.assertEqual(str(tags.get("TALB")), "A Night at the Opera")
            self.assertEqual(str(tags.get("TPE1")), "Queen")
            self.assertEqual(str(tags.get("TRCK")), f"{idx}/4")

        # Verify temp directory is clean
        temp_dir = target_dir / ".temp_download"
        if temp_dir.exists():
            self.assertEqual(list(temp_dir.glob("*")), [])

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_workload_large_playlist_batch_filtered_flow(self, mock_tag, mock_ydl):
        """Workload 3: Large 125-track playlist filtered by --batch 2."""
        songs = []
        for i in range(1, 126):
            songs.append(spotify.SongMetadata(
                id=f"pl_song_{i}",
                title=f"Playlist Song {i}",
                artist="Various Artists",
                album="Top 125",
                batch_index=(1 if i <= 100 else 2),
            ))

        target_dir = self.music_dir / "BatchWorkload"

        # Execute only Batch 2 (tracks 101 to 125 = 25 tracks)
        batch_2_tracks = [s for s in songs if s.batch_index == 2]
        self.assertEqual(len(batch_2_tracks), 25)

        dl = downloader.Downloader(output_dir=target_dir, max_workers=2)
        tasks = dl.download_playlist(batch_2_tracks)
        dl.executor.shutdown(wait=True)

        self.assertEqual(len(tasks), 25)
        for t in tasks:
            self.assertEqual(t.status, "completed")
            self.assertTrue(Path(t.file_path).exists())

        # Verify exactly 25 MP3 files in output dir
        mp3_files = list(target_dir.glob("*.mp3"))
        self.assertEqual(len(mp3_files), 25)

    @patch("yt_dlp.YoutubeDL")
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_workload_mixed_success_and_failure_workload(self, mock_tag, mock_ydl_cls):
        """Workload 4: Playlist download where track 2 fails, tracks 1 & 3 succeed."""
        def ytdl_selective_error(opts):
            outtmpl = opts.get("outtmpl", "")
            if "track_2" in outtmpl:
                return MockYoutubeDL(opts, simulate_error=Exception("Geo-restricted audio"))
            return MockYoutubeDL(opts)

        mock_ydl_cls.side_effect = ytdl_selective_error

        songs = [
            spotify.SongMetadata(id=f"track_{i}", title=f"Track {i}", artist="Artist")
            for i in range(1, 4)
        ]

        target_dir = self.music_dir / "MixedWorkload"
        dl = downloader.Downloader(output_dir=target_dir, max_workers=1)
        tasks = dl.download_playlist(songs)
        dl.executor.shutdown(wait=True)

        self.assertEqual(tasks[0].status, "completed")
        self.assertEqual(tasks[1].status, "error")
        self.assertEqual(tasks[2].status, "completed")

        # Verify completed files exist
        self.assertTrue((target_dir / "Artist - Track 1.mp3").exists())
        self.assertFalse((target_dir / "Artist - Track 2.mp3").exists())
        self.assertTrue((target_dir / "Artist - Track 3.mp3").exists())

        # Verify no orphan temp files remain for any track
        temp_dir = target_dir / ".temp_download"
        if temp_dir.exists():
            self.assertEqual(list(temp_dir.glob("*")), [])

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("requests.get")
    @patch("main.check_dependencies")
    def test_workload_interactive_wizard_complete_flow(self, mock_check, mock_get, mock_ydl):
        """Workload 5: Interactive wizard prompts user, downloads track, and exits."""
        track_url = "https://open.spotify.com/track/wizard_track_123"
        mock_html = create_mock_track_embed_html(
            track_id="wizard_track_123",
            title="Wizard Song",
            artist="Wizard Artist",
            duration_ms=200000,
        )
        mock_get.return_value = MockHTTPResponse(status_code=200, text=mock_html)

        custom_wizard_dir = str(self.music_dir / "WizardPickedDir")

        # Sequence of user inputs: URL, custom output directory, bitrate 320, workers 2, then 'q' to quit
        user_inputs = [
            track_url,
            custom_wizard_dir,
            "320",
            "2",
            "q",
        ]

        with patch("main.HAS_RICH", False):
            with patch("main.show_banner"):
                with patch("builtins.input", side_effect=user_inputs):
                    with self.assertRaises(SystemExit) as cm:
                        main.interactive_mode()
                    self.assertEqual(cm.exception.code, 0)

        # Verify downloaded song exists in the custom folder
        saved_file = Path(custom_wizard_dir) / "Wizard Artist - Wizard Song.mp3"
        self.assertTrue(saved_file.exists())

    @patch("yt_dlp.YoutubeDL", side_effect=MockYoutubeDL)
    @patch("core.downloader.apply_id3_tags", return_value=True)
    def test_workload_idempotent_re_download(self, mock_tag, mock_ydl):
        """Workload 6: Repeated download of same track cleanly overwrites without error."""
        song = spotify.SongMetadata(id="idem_track", title="Repeat Track", artist="Repeat Artist")
        target_dir = self.music_dir / "IdempotentWorkload"

        dl = downloader.Downloader(output_dir=target_dir)

        # Download 1st time
        task1 = dl.download_song(song)
        dl.executor.shutdown(wait=True)
        self.assertEqual(task1.status, "completed")
        file_path = Path(task1.file_path)
        self.assertTrue(file_path.exists())

        # Modify content of existing file
        file_path.write_text("prior modified audio content")

        # Download 2nd time
        dl2 = downloader.Downloader(output_dir=target_dir)
        task2 = dl2.download_song(song)
        dl2.executor.shutdown(wait=True)

        self.assertEqual(task2.status, "completed")
        self.assertTrue(file_path.exists())
        # Content has been overwritten with fresh synthetic audio
        self.assertNotEqual(file_path.read_text(errors="ignore"), "prior modified audio content")


if __name__ == "__main__":
    unittest.main()
