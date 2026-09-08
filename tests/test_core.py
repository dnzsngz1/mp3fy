"""
Unit tests for MP3fy core modules.
"""

import os
import tempfile
import unittest
from pathlib import Path

from mutagen.id3 import ID3
from core.utils import sanitize_filename, format_duration, ensure_directory
from core.spotify import parse_spotify_url, SpotifyFetcher
from core.tagger import apply_id3_tags
from core.downloader import DownloadTask, SongMetadata


class TestUtils(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Valid Name"), "Valid Name")
        self.assertEqual(sanitize_filename("Illegal: / \\ ? * < > | Name"), "Illegal Name")
        self.assertEqual(sanitize_filename("   leading and trailing spaces...   "), "leading and trailing spaces")
        self.assertEqual(sanitize_filename(""), "unnamed_track")

    def test_format_duration(self):
        self.assertEqual(format_duration(185000), "3:05")
        self.assertEqual(format_duration(3665000), "1:01:05")
        self.assertEqual(format_duration(0), "0:00")
        self.assertEqual(format_duration(None), "0:00")

    def test_ensure_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sub = Path(tmp_dir) / "test_sub" / "inner"
            res = ensure_directory(sub)
            self.assertTrue(res.exists())
            self.assertTrue(res.is_dir())

    def test_get_default_music_dir(self):
        from core.utils import get_default_music_dir
        music_dir = get_default_music_dir()
        self.assertTrue(music_dir.exists())
        self.assertTrue(music_dir.is_dir())


class TestSpotifyParser(unittest.TestCase):
    def test_parse_urls(self):
        pl_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=123"
        t, i = parse_spotify_url(pl_url)
        self.assertEqual(t, "playlist")
        self.assertEqual(i, "37i9dQZF1DXcBWIGoYBM5M")

        alb_url = "https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa"
        t, i = parse_spotify_url(alb_url)
        self.assertEqual(t, "album")
        self.assertEqual(i, "4m2880jivSbbyEGAKfITCa")

        tr_url = "https://open.spotify.com/intl-tr/track/4LfCY65LvojKjWEnU7fNN4"
        t, i = parse_spotify_url(tr_url)
        self.assertEqual(t, "track")
        self.assertEqual(i, "4LfCY65LvojKjWEnU7fNN4")

        uri = "spotify:track:4LfCY65LvojKjWEnU7fNN4"
        t, i = parse_spotify_url(uri)
        self.assertEqual(t, "track")
        self.assertEqual(i, "4LfCY65LvojKjWEnU7fNN4")


class TestID3Tagger(unittest.TestCase):
    def test_tagger_with_sample_mp3(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_mp3 = Path(tmp_dir) / "test_track.mp3"
            # Generate a 0.5-second silent MP3 using ffmpeg
            ret = os.system(f'ffmpeg -f lavfi -i "sine=frequency=440:duration=0.5" -b:a 128k "{sample_mp3}" -y -loglevel quiet')
            if ret != 0:
                self.skipTest("ffmpeg not available or failed to generate test audio")

            success = apply_id3_tags(
                mp3_path=sample_mp3,
                title="Test Song Title",
                artist="Test Artist Name",
                album="Test Album Name",
                year="2026",
                track_number=1,
                total_tracks=10,
                comment="Downloaded with MP3fy",
            )
            self.assertTrue(success)

            # Verify with mutagen
            tags = ID3(str(sample_mp3))
            self.assertEqual(str(tags.get("TIT2")), "Test Song Title")
            self.assertEqual(str(tags.get("TPE1")), "Test Artist Name")
            self.assertEqual(str(tags.get("TALB")), "Test Album Name")
            self.assertEqual(str(tags.get("TDRC")), "2026")
            self.assertEqual(str(tags.get("TRCK")), "1/10")


class TestWindowsPlatform(unittest.TestCase):
    def test_open_native_folder_picker_windows(self):
        from core.utils import open_native_folder_picker
        from unittest.mock import patch, MagicMock

        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as mock_run:
                mock_res = MagicMock()
                mock_res.returncode = 0
                mock_res.stdout = "C:\\Users\\TestUser\\Music\n"
                mock_run.return_value = mock_res

                res = open_native_folder_picker("C:\\Users\\O'Connor\\Music")
                self.assertEqual(res, "C:\\Users\\TestUser\\Music")
                mock_run.assert_called_once()
                args, kwargs = mock_run.call_args
                cmd = args[0]
                self.assertIn("powershell", cmd)
                self.assertIn("-STA", cmd)
                # Ensure single quotes are escaped as '' in PowerShell command
                self.assertIn("O''Connor", cmd[cmd.index("-Command") + 1])

    def test_downloader_ffmpeg_detection_windows(self):
        from core.downloader import Downloader, SongMetadata
        from unittest.mock import patch

        with patch("sys.platform", "win32"):
            with patch("shutil.which", return_value=None):
                with patch.dict("os.environ", {"LOCALAPPDATA": "C:\\fake\\appdata"}):
                    downloader = Downloader()
                    self.assertIsNotNone(downloader)


if __name__ == "__main__":
    unittest.main()
