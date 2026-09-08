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


    def test_interactive_mode_browse_folder(self):
        with patch("main.HAS_RICH", False):
            with patch("main.show_banner"):
                with patch("main.check_dependencies"):
                    with patch("main.parse_spotify_url", return_value=("track", "12345")):
                        with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                            with patch("main.open_native_folder_picker", return_value="/custom/picked/path") as mock_picker:
                                with patch("main.execute_download") as mock_exec:
                                    mock_fetcher = MagicMock()
                                    mock_data = MagicMock()
                                    mock_data.tracks = [MagicMock()]
                                    mock_data.batches = []
                                    mock_fetcher.fetch.return_value = mock_data
                                    mock_fetcher_cls.return_value = mock_fetcher

                                    # Sequence of inputs: URL, 'b' (browse folder), '320' (bitrate), '2' (workers), 'q' (exit)
                                    input_values = [
                                        "https://open.spotify.com/track/12345",
                                        "b",
                                        "320",
                                        "2",
                                        "q",
                                    ]
                                    with patch("builtins.input", side_effect=input_values):
                                        with self.assertRaises(SystemExit):
                                            main.interactive_mode()

                                        mock_picker.assert_called_once()
                                        mock_exec.assert_called_once()
                                        call_args = mock_exec.call_args.args
                                        from pathlib import Path
                                        self.assertEqual(call_args[2], Path("/custom/picked/path").resolve())

    def test_none_metadata_returns_exit_code_1(self):
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = None
                    mock_fetcher_cls.return_value = mock_fetcher
                    with self.assertRaises(SystemExit) as cm:
                        main.main()
                    self.assertEqual(cm.exception.code, 1)

    def test_batch_zero_rejection_returns_exit_code_1(self):
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M", "--batch", "0"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_data = MagicMock(tracks=[MagicMock(batch_index=1)], batches=[MagicMock()])
                    mock_fetcher.fetch.return_value = mock_data
                    mock_fetcher_cls.return_value = mock_fetcher
                    with self.assertRaises(SystemExit) as cm:
                        main.main()
                    self.assertEqual(cm.exception.code, 1)

    def test_download_failure_exit_code_1(self):
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/4LfCY65LvojKjWEnU7fNN4"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    with patch("main.execute_download", return_value=1) as mock_exec:
                        mock_fetcher = MagicMock()
                        mock_data = MagicMock(tracks=[MagicMock(batch_index=1)], batches=[])
                        mock_fetcher.fetch.return_value = mock_data
                        mock_fetcher_cls.return_value = mock_fetcher
                        with self.assertRaises(SystemExit) as cm:
                            main.main()
                        self.assertEqual(cm.exception.code, 1)
                        mock_exec.assert_called_once()

    def test_rich_markup_escaping_on_bracketed_titles(self):
        title = "Test Song [Official Remix] [feat. Artist] [/red]"
        artist = "Band [Rock] [blue]"
        label = f"{artist} - {title}"
        escaped_title = main.escape(title)
        escaped_label = main.escape(label)
        self.assertIn(r"\[/red]", escaped_title)
        self.assertIn(r"\[blue]", escaped_label)
        # Ensure that without escaping, it would crash
        if main.HAS_RICH and main.console:
            from rich.text import Text
            from rich.errors import MarkupError
            with self.assertRaises(MarkupError):
                Text.from_markup(f"[bold white]{label}[/bold white]")
            # With escaping, it renders safely
            rendered = Text.from_markup(f"[bold white]{escaped_label}[/bold white]")
            self.assertIn("Official Remix", rendered.plain)
            self.assertIn("[/red]", rendered.plain)
            self.assertIn("[blue]", rendered.plain)


if __name__ == "__main__":
    unittest.main()
