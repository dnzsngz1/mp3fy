"""
Unit tests for MP3fy CLI interface and arguments.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import main


class TestCLI(unittest.TestCase):
    def test_version(self):
        self.assertTrue(hasattr(main, "VERSION"))
        self.assertEqual(main.VERSION, "1.2.0")

    def test_argument_parser_help(self):
        with self.assertRaises(SystemExit) as cm:
            with patch.object(sys, "argv", ["mp3fy", "--help"]):
                main.main()
        self.assertEqual(cm.exception.code, 0)

    def test_argument_parser_version(self):
        with self.assertRaises(SystemExit) as cm:
            with patch.object(sys, "argv", ["mp3fy", "--version"]):
                main.main()
        self.assertEqual(cm.exception.code, 0)

    def test_argument_parser_options(self):
        test_args = [
            "mp3fy",
            "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4",
            "-o", "/tmp/test_music",
            "-b", "192",
            "-w", "4",
            "--batch", "2",
        ]
        with patch.object(sys, "argv", test_args):
            with patch("main.check_dependencies") as mock_check:
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    with patch("main.execute_download") as mock_exec:
                        mock_fetcher = MagicMock()
                        mock_data = MagicMock()
                        mock_track_1 = MagicMock(batch_index=1)
                        mock_track_2 = MagicMock(batch_index=2)
                        mock_data.tracks = [mock_track_1, mock_track_2]
                        mock_fetcher.fetch.return_value = mock_data
                        mock_fetcher_cls.return_value = mock_fetcher

                        main.main()

                        mock_check.assert_called_once()
                        mock_fetcher.fetch.assert_called_once_with("https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4")
                        mock_exec.assert_called_once()
                        call_kwargs = mock_exec.call_args.kwargs
                        self.assertEqual(call_kwargs["bitrate"], "192")
                        self.assertEqual(call_kwargs["max_workers"], 4)
                        self.assertEqual(call_kwargs["tracks_to_download"], [mock_track_2])

    def test_banner_display(self):
        with patch("main.HAS_RICH", False):
            with patch("builtins.print") as mock_print:
                main.show_banner()
                mock_print.assert_called()

    def test_check_dependencies_windows_hint(self):
        with patch("sys.platform", "win32"):
            with patch("shutil.which", return_value=None):
                with patch("main.HAS_RICH", False):
                    with patch("builtins.print") as mock_print:
                        main.check_dependencies()
                        printed_text = "".join(str(call[0][0]) for call in mock_print.call_args_list)
                        self.assertIn("winget install Gyan.FFmpeg", printed_text)

    def test_check_dependencies_linux_hint(self):
        with patch("sys.platform", "linux"):
            with patch("shutil.which", return_value=None):
                with patch("main.HAS_RICH", False):
                    with patch("builtins.print") as mock_print:
                        main.check_dependencies()
                        printed_text = "".join(str(call[0][0]) for call in mock_print.call_args_list)
                        self.assertIn("sudo apt install ffmpeg", printed_text)


if __name__ == "__main__":
    unittest.main()
