"""
Adversarial white-box stress testing harness for MP3fy CLI and platform compatibility.
Created by teamwork_preview_challenger_final_2 (Tier 5 Hardening).

Validates:
1. CLI argument edge cases (None metadata, None tracks, fetch exception, batch 0/-1/999, invalid bitrate -b 999).
2. Exit code propagation (100% success -> 0, 100% failure -> 1, partial failure -> 1, cancellation -> 1, SIGINT -> 130).
3. Rich markup escaping (brackets, closing tags [/red], ANSI escape codes, unclosed tags, sliced brackets).
4. Platform launcher scripts (bash syntax, installer failure propagation, UTF-8 codepage, parameter binding & forwarding).
"""

import io
import os
import re
import sys
import time
import signal
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import main
from core.spotify import PlaylistMetadata, SongMetadata, BatchInfo


class TestCLIArgumentEdgeCases(unittest.TestCase):
    """Adversarial testing for CLI argument parsing and error handling."""

    def test_none_metadata_exits_1_without_traceback(self):
        """When SpotifyFetcher.fetch returns None, main() exits with code 1 and no traceback."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/none_track"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = None
                    mock_fetcher_cls.return_value = mock_fetcher

                    stdout_buf = io.StringIO()
                    stderr_buf = io.StringIO()
                    with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()

                    self.assertEqual(cm.exception.code, 1)
                    output = stdout_buf.getvalue() + stderr_buf.getvalue()
                    self.assertIn("Hata: Spotify bağlantısından parça listesi alınamadı", output)
                    self.assertNotIn("Traceback (most recent call last)", output)

    def test_none_tracks_exits_1_without_traceback(self):
        """When SpotifyFetcher returns an object with tracks=None, main() exits 1 cleanly."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/none_tracks_obj"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_data = MagicMock()
                    mock_data.tracks = None
                    mock_fetcher.fetch.return_value = mock_data
                    mock_fetcher_cls.return_value = mock_fetcher

                    stdout_buf = io.StringIO()
                    stderr_buf = io.StringIO()
                    with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()

                    self.assertEqual(cm.exception.code, 1)
                    output = stdout_buf.getvalue() + stderr_buf.getvalue()
                    self.assertIn("Hata: Spotify bağlantısından parça listesi alınamadı", output)
                    self.assertNotIn("Traceback", output)

    def test_fetch_exception_exits_1_without_traceback(self):
        """When fetcher.fetch raises a network/runtime exception, it is caught with code 1."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/exception_url"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.side_effect = ConnectionResetError("Connection dropped by peer")
                    mock_fetcher_cls.return_value = mock_fetcher

                    stdout_buf = io.StringIO()
                    stderr_buf = io.StringIO()
                    with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()

                    self.assertEqual(cm.exception.code, 1)
                    output = stdout_buf.getvalue() + stderr_buf.getvalue()
                    self.assertIn("Hata: Spotify bilgisi alınamadı", output)
                    self.assertIn("Connection dropped by peer", output)
                    self.assertNotIn("Traceback (most recent call last)", output)

    def test_batch_zero_exits_1(self):
        """Passing --batch 0 triggers validation failure and exits with code 1."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/test", "--batch", "0"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = PlaylistMetadata(
                        id="pl1", title="Test", tracks=[SongMetadata(id="s1", title="S", artist="A")]
                    )
                    mock_fetcher_cls.return_value = mock_fetcher

                    stdout_buf = io.StringIO()
                    stderr_buf = io.StringIO()
                    with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()

                    self.assertEqual(cm.exception.code, 1)
                    output = stdout_buf.getvalue() + stderr_buf.getvalue()
                    self.assertIn("Bölüm numarası 1 veya daha büyük olmalıdır", output)
                    self.assertIn("verilen: 0", output)

    def test_batch_negative_exits_1(self):
        """Passing --batch -1 triggers validation failure and exits with code 1."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/test", "--batch", "-1"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = PlaylistMetadata(
                        id="pl1", title="Test", tracks=[SongMetadata(id="s1", title="S", artist="A")]
                    )
                    mock_fetcher_cls.return_value = mock_fetcher

                    stdout_buf = io.StringIO()
                    stderr_buf = io.StringIO()
                    with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()

                    self.assertEqual(cm.exception.code, 1)
                    output = stdout_buf.getvalue() + stderr_buf.getvalue()
                    self.assertIn("Bölüm numarası 1 veya daha büyük olmalıdır", output)
                    self.assertIn("verilen: -1", output)

    def test_batch_out_of_range_exits_1(self):
        """Passing --batch 999 when playlist has fewer batches exits with code 1."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/test", "--batch", "999"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    batch = BatchInfo(batch_index=1, start_index=1, end_index=10, count=10, name="Bölüm 1")
                    mock_fetcher.fetch.return_value = PlaylistMetadata(
                        id="pl1",
                        title="Test",
                        tracks=[SongMetadata(id="s1", title="S", artist="A", batch_index=1)],
                        batches=[batch]
                    )
                    mock_fetcher_cls.return_value = mock_fetcher

                    stdout_buf = io.StringIO()
                    stderr_buf = io.StringIO()
                    with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()

                    self.assertEqual(cm.exception.code, 1)
                    output = stdout_buf.getvalue() + stderr_buf.getvalue()
                    self.assertIn("Belirtilen bölüm (999) bulunamadı", output)
                    self.assertIn("Toplam bölüm sayısı: 1", output)

    def test_invalid_bitrate_exits_2_without_traceback(self):
        """Passing invalid bitrate (-b 999) is rejected by argparse with exit code 2."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/123", "-b", "999"]):
            stderr_buf = io.StringIO()
            with patch("sys.stderr", stderr_buf):
                with self.assertRaises(SystemExit) as cm:
                    main.main()
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("invalid choice: '999'", stderr_buf.getvalue())
            self.assertNotIn("Traceback", stderr_buf.getvalue())

    def test_workers_clamping_to_safe_bounds(self):
        """Workers count is clamped to [1, 8] safely."""
        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/123", "-w", "50"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    with patch("main.execute_download", return_value=0) as mock_exec:
                        mock_fetcher = MagicMock()
                        mock_fetcher.fetch.return_value = PlaylistMetadata(
                            id="pl1", title="T", tracks=[SongMetadata(id="s1", title="S", artist="A")]
                        )
                        mock_fetcher_cls.return_value = mock_fetcher

                        main.main()
                        self.assertEqual(mock_exec.call_args.kwargs["max_workers"], 8)

        with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/track/123", "-w", "-10"]):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    with patch("main.execute_download", return_value=0) as mock_exec:
                        mock_fetcher = MagicMock()
                        mock_fetcher.fetch.return_value = PlaylistMetadata(
                            id="pl1", title="T", tracks=[SongMetadata(id="s1", title="S", artist="A")]
                        )
                        mock_fetcher_cls.return_value = mock_fetcher

                        main.main()
                        self.assertEqual(mock_exec.call_args.kwargs["max_workers"], 1)


class TestExitCodePropagation(unittest.TestCase):
    """Adversarial validation of exit code propagation in main.py and execute_download."""

    def _create_mock_downloader(self, statuses):
        class MockDownloader:
            def __init__(self, *args, **kwargs):
                self.on_progress = kwargs.get("on_progress")

            def download_playlist(self, tracks):
                tasks = []
                for tr, st in zip(tracks, statuses):
                    t = MagicMock(
                        song=tr,
                        status=st,
                        file_size_mb=3.0,
                        error_message="Downloader error" if st == "error" else None,
                    )
                    tasks.append(t)
                    if self.on_progress:
                        self.on_progress(t)
                return tasks

        return MockDownloader

    def test_exit_code_0_on_100_percent_success(self):
        """When 100% of tracks complete successfully, exit code 0 is returned."""
        tracks = [
            SongMetadata(id=f"t_{i}", title=f"Track {i}", artist="Artist")
            for i in range(3)
        ]
        data = PlaylistMetadata(id="pl_ok", title="Success Playlist", tracks=tracks)

        with patch("main.Downloader", self._create_mock_downloader(["completed", "completed", "completed"])):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = data
                    mock_fetcher_cls.return_value = mock_fetcher

                    with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/ok"]):
                        res = main.main()
                        self.assertEqual(res, 0)

    def test_exit_code_1_on_100_percent_failure(self):
        """When 100% of tracks fail to download, sys.exit(1) is called."""
        tracks = [
            SongMetadata(id=f"t_{i}", title=f"Track {i}", artist="Artist")
            for i in range(3)
        ]
        data = PlaylistMetadata(id="pl_fail", title="Fail Playlist", tracks=tracks)

        with patch("main.Downloader", self._create_mock_downloader(["error", "error", "error"])):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = data
                    mock_fetcher_cls.return_value = mock_fetcher

                    with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/fail"]):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()
                        self.assertEqual(cm.exception.code, 1)

    def test_exit_code_1_on_partial_failure(self):
        """When 2 tracks succeed and 1 track fails (partial failure), sys.exit(1) is called."""
        tracks = [
            SongMetadata(id=f"t_{i}", title=f"Track {i}", artist="Artist")
            for i in range(3)
        ]
        data = PlaylistMetadata(id="pl_part", title="Partial Playlist", tracks=tracks)

        with patch("main.Downloader", self._create_mock_downloader(["completed", "completed", "error"])):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = data
                    mock_fetcher_cls.return_value = mock_fetcher

                    with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/part"]):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()
                        self.assertEqual(cm.exception.code, 1)

    def test_exit_code_1_on_cancelled_tasks(self):
        """Cancelled tasks are counted as non-successful and propagate exit code 1."""
        tracks = [SongMetadata(id="t_c", title="Cancelled", artist="Artist")]
        data = PlaylistMetadata(id="pl_c", title="Cancelled Playlist", tracks=tracks)

        with patch("main.Downloader", self._create_mock_downloader(["cancelled"])):
            with patch("main.check_dependencies"):
                with patch("main.SpotifyFetcher") as mock_fetcher_cls:
                    mock_fetcher = MagicMock()
                    mock_fetcher.fetch.return_value = data
                    mock_fetcher_cls.return_value = mock_fetcher

                    with patch.object(sys, "argv", ["mp3fy", "https://open.spotify.com/playlist/canc"]):
                        with self.assertRaises(SystemExit) as cm:
                            main.main()
                        self.assertEqual(cm.exception.code, 1)


class TestRichMarkupEscaping(unittest.TestCase):
    """Stress testing Rich markup escaping on adversarial track titles, artists, and errors."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_adversarial_markup_in_titles_and_artists(self):
        """
        Tests tracks containing:
        - Opening/closing style tags: [red], [/red], [bold], [/bold], [/]
        - Malformed/unmatched tags: [bold][italic], [
        - Brackets inside text: [Remix], [1999], [feat. Artist]
        - Double/triple brackets: [[nested]], [[[triple]]]
        - ANSI escape sequences: \x1b[31;1mRedText\x1b[0m
        - Invalid tag names: [not_a_style], [xyz123]
        All must render cleanly without MarkupError.
        """
        adversarial_titles = [
            "Track [Official Video] [Remix]",
            "Track with [/red] closing tag",
            "Track with [/bold][/italic][/] closing tags",
            "Track with [bold][red] unclosed tags",
            "Track with \x1b[31;1mANSI escape code\x1b[0m embedded",
            "Track with [[double brackets]]",
            "Track with [nonexistent_rich_tag] test",
            "Track ending in unclosed single bracket [",
            "Track with tag sliced at boundary [A" * 5,
        ]

        tracks = [
            SongMetadata(id=f"adv_{i}", title=title, artist=f"Artist [Band] {i} [/blue]")
            for i, title in enumerate(adversarial_titles)
        ]
        data = PlaylistMetadata(
            id="pl_adv",
            title="Adversarial [Collection] [/green]",
            owner="DJ [Master] [/cyan]",
            tracks=tracks
        )

        class MockDownloader:
            def __init__(self, *args, **kwargs):
                self.on_progress = kwargs.get("on_progress")

            def download_playlist(self, trs):
                tasks = []
                for i, tr in enumerate(trs):
                    # Half succeed, half fail with markup in error message
                    if i % 2 == 0:
                        t = MagicMock(song=tr, status="completed", file_size_mb=4.0, error_message=None)
                    else:
                        t = MagicMock(
                            song=tr,
                            status="error",
                            file_size_mb=0,
                            error_message="Error: [red]Failed[/red] with code [404] \x1b[31mFAIL\x1b[0m"
                        )
                    tasks.append(t)
                    if self.on_progress:
                        self.on_progress(t)
                return tasks

        with patch("main.Downloader", MockDownloader):
            # Must complete without throwing rich.errors.MarkupError
            exit_code = main.execute_download(
                data=data,
                tracks_to_download=tracks,
                output_dir=self.temp_dir / "out_[music]_[2024]",
                bitrate="320",
                max_workers=2
            )
            # Partial failure must produce exit code 1
            self.assertEqual(exit_code, 1)

    def test_markup_escaping_with_rich_disabled(self):
        """Verifies plain-text fallback gracefully handles all bracketed and ANSI titles."""
        tracks = [
            SongMetadata(id="pt_1", title="Title [Remix] [/red]", artist="Artist [Live]"),
            SongMetadata(id="pt_2", title="ANSI \x1b[32mGreen\x1b[0m", artist="Artist 2"),
        ]
        data = PlaylistMetadata(id="pl_pt", title="Plain [Test]", tracks=tracks)

        class MockDownloader:
            def __init__(self, *args, **kwargs):
                self.on_progress = kwargs.get("on_progress")

            def download_playlist(self, trs):
                tasks = []
                for tr in trs:
                    t = MagicMock(song=tr, status="completed", file_size_mb=3.5, error_message=None)
                    tasks.append(t)
                    if self.on_progress:
                        self.on_progress(t)
                return tasks

        with patch("main.HAS_RICH", False):
            with patch("main.Downloader", MockDownloader):
                exit_code = main.execute_download(
                    data=data,
                    tracks_to_download=tracks,
                    output_dir=self.temp_dir,
                    bitrate="320",
                    max_workers=1
                )
                self.assertEqual(exit_code, 0)

    def test_bracket_slice_boundary_behavior(self):
        """
        When title[:35] cuts right through a bracket (e.g. at position 35),
        escape() and Text.from_markup() ensure no crash or unbalanced syntax error.
        """
        # Case 1: Bracket cut off mid-tag (e.g. "[b" without closing bracket)
        sliced_cut = "A" * 33 + "[bold]Something"
        # Sliced at 35 gives "A"*33 + "[b"
        slice_35 = sliced_cut[:35]
        escaped_cut = main.escape(slice_35)
        self.assertEqual(escaped_cut, "A" * 33 + "[b")

        # Case 2: Full tag inside slice
        sliced_full = "A" * 20 + "[bold]Tag[/bold]"
        slice_full = sliced_full[:35]
        escaped_full = main.escape(slice_full)
        self.assertIn(r"\[bold]", escaped_full)

        if main.HAS_RICH:
            from rich.text import Text
            # Both escaped slices render cleanly without MarkupError
            rendered_cut = Text.from_markup(f"[white]{escaped_cut}[/white]")
            self.assertEqual(rendered_cut.plain, "A" * 33 + "[b")

            rendered_full = Text.from_markup(f"[white]{escaped_full}[/white]")
            self.assertIn("[bold]Tag", rendered_full.plain)


class TestLauncherScripts(unittest.TestCase):
    """Adversarial stress-testing of Linux, Windows, and PowerShell launcher scripts."""

    def test_bash_syntax_run_sh_and_install_sh(self):
        """Runs bash -n on run.sh and install.sh to ensure zero syntax errors."""
        for script_name in ["run.sh", "install.sh"]:
            script_path = PROJECT_DIR / script_name
            self.assertTrue(script_path.exists(), f"{script_name} must exist")
            res = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"bash -n {script_name} failed: {res.stderr}")

    def test_run_sh_installer_failure_propagation(self):
        """
        Empirically verifies that if run.sh triggers install.sh and install.sh fails,
        run.sh halts immediately and returns the non-zero installer exit code.
        """
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            test_run_sh = temp_path / "run.sh"
            shutil.copy(PROJECT_DIR / "run.sh", test_run_sh)
            test_run_sh.chmod(0o755)

            # Create a mock install.sh that exits with code 42
            test_install_sh = temp_path / "install.sh"
            test_install_sh.write_text("#!/usr/bin/env bash\necho 'Mock install failed' >&2\nexit 42\n")
            test_install_sh.chmod(0o755)

            res = subprocess.run(["bash", str(test_run_sh)], cwd=temp_path, capture_output=True, text=True)
            self.assertEqual(res.returncode, 42)
            self.assertIn("Kurulum başarısız oldu (Çıkış kodu: 42)", res.stderr)

    def test_run_sh_argument_preservation_and_forwarding(self):
        """
        Empirically verifies that run.sh passes complex arguments ($@) with spaces,
        special characters, and quotes without token splitting.
        """
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            test_run_sh = temp_path / "run.sh"
            shutil.copy(PROJECT_DIR / "run.sh", test_run_sh)
            test_run_sh.chmod(0o755)

            # Create dummy .venv/bin/python3
            venv_bin = temp_path / ".venv" / "bin"
            venv_bin.mkdir(parents=True)
            (venv_bin / "python3").symlink_to(sys.executable)

            # Create mock main.py recording sys.argv
            test_main_py = temp_path / "main.py"
            test_main_py.write_text(
                "import sys, json\n"
                "Path = __import__('pathlib').Path\n"
                "Path('argv_out.json').write_text(json.dumps(sys.argv[1:]))\n"
                "sys.exit(0)\n"
            )

            test_args = [
                "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=123",
                "-o", "/path with spaces/and [brackets]/dir",
                "-b", "256",
                "--batch", "2"
            ]

            res = subprocess.run(["bash", str(test_run_sh)] + test_args, cwd=temp_path, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"run.sh failed: {res.stderr}")

            recorded_argv = (temp_path / "argv_out.json").read_text()
            import json
            parsed_argv = json.loads(recorded_argv)
            self.assertEqual(parsed_argv, test_args)

    def test_run_sh_exit_code_propagation(self):
        """Verifies run.sh propagates Python exit codes (0, 1, 2, 130) transparently."""
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            test_run_sh = temp_path / "run.sh"
            shutil.copy(PROJECT_DIR / "run.sh", test_run_sh)
            test_run_sh.chmod(0o755)

            venv_bin = temp_path / ".venv" / "bin"
            venv_bin.mkdir(parents=True)
            (venv_bin / "python3").symlink_to(sys.executable)

            test_main_py = temp_path / "main.py"
            test_main_py.write_text("import sys\nsys.exit(int(sys.argv[1]))\n")

            for expected_code in [0, 1, 2, 130]:
                res = subprocess.run(["bash", str(test_run_sh), str(expected_code)], cwd=temp_path)
                self.assertEqual(res.returncode, expected_code)

    def test_windows_batch_script_integrity(self):
        """Validates run.bat and mp3fy.cmd UTF-8 code page and exit code propagation."""
        for bat_name in ["run.bat", "mp3fy.cmd"]:
            bat_path = PROJECT_DIR / bat_name
            self.assertTrue(bat_path.exists(), f"{bat_name} must exist")
            content = bat_path.read_text(encoding="utf-8")

            # Check UTF-8 code page
            self.assertIn("chcp 65001", content, f"{bat_name} must set UTF-8 code page 65001")
            # Check argument forwarding
            self.assertIn("%*", content, f"{bat_name} must forward all arguments using %*")
            # Check exit code propagation
            self.assertIn("exit /b %ERRORLEVEL%", content, f"{bat_name} must propagate %ERRORLEVEL%")

    def test_powershell_script_parameter_binding_and_exit_codes(self):
        """
        Validates run.ps1 and mp3fy.ps1:
        1. Must NOT contain [CmdletBinding()] or param() (which cause ParameterBindingException).
        2. Must use @args to splat parameters verbatim.
        3. Must propagate $LASTEXITCODE.
        4. Must handle installer failure and exit with $LASTEXITCODE.
        """
        for ps1_name in ["run.ps1", "mp3fy.ps1"]:
            ps1_path = PROJECT_DIR / ps1_name
            self.assertTrue(ps1_path.exists(), f"{ps1_name} must exist")
            content = ps1_path.read_text(encoding="utf-8")

            # Must not have CmdletBinding / param at root
            self.assertNotIn("[CmdletBinding()]", content, f"{ps1_name} must not use [CmdletBinding()]")
            self.assertNotIn("param(", content, f"{ps1_name} must not declare param()")

            # Must forward arguments via @args
            self.assertIn("@args", content, f"{ps1_name} must forward @args")

            # Must propagate exit code
            self.assertIn("exit $LASTEXITCODE", content, f"{ps1_name} must exit with $LASTEXITCODE")

        # Specific check for run.ps1 installer error handling
        run_ps1_content = (PROJECT_DIR / "run.ps1").read_text(encoding="utf-8")
        self.assertIn("install.ps1", run_ps1_content)
        self.assertIn("$LASTEXITCODE -ne 0", run_ps1_content)

    def test_powershell_installer_utf8_generation(self):
        """
        Validates install.ps1:
        1. Configures UTF-8 console streams.
        2. Generates launchers using UTF8 encoding (not ASCII).
        3. Profile function does not declare CmdletBinding or param.
        """
        install_ps1 = PROJECT_DIR / "install.ps1"
        self.assertTrue(install_ps1.exists(), "install.ps1 must exist")
        content = install_ps1.read_text(encoding="utf-8")

        self.assertIn("[System.Text.Encoding]::UTF8", content)
        self.assertIn("Set-Content -Path $UserCmd -Value $UserCmdContent -Encoding UTF8", content)
        self.assertIn("Set-Content -Path $UserPs1 -Value $UserPs1Content -Encoding UTF8", content)
        self.assertNotIn("-Encoding ASCII", content)


if __name__ == "__main__":
    unittest.main()
