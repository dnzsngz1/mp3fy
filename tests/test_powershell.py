"""
Unit tests for MP3fy PowerShell & Windows scripts and integration.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class TestPowerShellScripts(unittest.TestCase):
    def setUp(self):
        self.project_dir = BASE_DIR
        self.install_ps1 = self.project_dir / "install.ps1"
        self.run_ps1 = self.project_dir / "run.ps1"
        self.mp3fy_ps1 = self.project_dir / "mp3fy.ps1"
        self.mp3fy_cmd = self.project_dir / "mp3fy.cmd"
        self.run_bat = self.project_dir / "run.bat"

    def test_install_ps1_content(self):
        self.assertTrue(self.install_ps1.exists(), "install.ps1 must exist")
        content = self.install_ps1.read_text(encoding="utf-8")
        
        # Verify UTF-8 console setup
        self.assertIn("[System.Text.Encoding]::UTF8", content)
        # Verify Python checks
        self.assertIn("Python 3.9", content)
        self.assertIn("winget install Python", content)
        # Verify FFmpeg checks & fallbacks
        self.assertIn("winget install Gyan.FFmpeg", content)
        self.assertIn("scoop install ffmpeg", content)
        # Verify Virtualenv setup
        self.assertIn(".venv", content)
        self.assertIn("uv", content)
        self.assertIn("pip install -e", content)
        # Verify launcher generation and PATH configuration
        self.assertIn("mp3fy.cmd", content)
        self.assertIn("mp3fy.ps1", content)
        self.assertIn("Set-Content -Path $UserCmd -Value $UserCmdContent -Encoding UTF8", content)
        self.assertIn("Set-Content -Path $UserPs1 -Value $UserPs1Content -Encoding UTF8", content)
        self.assertNotIn("-Encoding ASCII", content)
        self.assertIn("[Environment]::SetEnvironmentVariable", content)
        self.assertIn("PROFILE", content)

    def test_run_ps1_content(self):
        self.assertTrue(self.run_ps1.exists(), "run.ps1 must exist")
        content = self.run_ps1.read_text(encoding="utf-8")
        self.assertIn("[System.Text.Encoding]::UTF8", content)
        self.assertIn("install.ps1", content)
        self.assertIn(".venv", content)
        self.assertIn("@args", content)
        # Ensure install failure is checked and propagated
        self.assertIn("$LASTEXITCODE", content)
        self.assertIn("exit $LASTEXITCODE", content)
        # Ensure [CmdletBinding()] and param() are NOT present so arguments pass without ParameterBindingException
        self.assertNotIn("[CmdletBinding()]", content)
        self.assertNotIn("param()", content)

    def test_mp3fy_ps1_content(self):
        self.assertTrue(self.mp3fy_ps1.exists(), "mp3fy.ps1 must exist")
        content = self.mp3fy_ps1.read_text(encoding="utf-8")
        self.assertIn("[System.Text.Encoding]::UTF8", content)
        self.assertIn("@args", content)
        self.assertIn("main.py", content)
        # Ensure [CmdletBinding()] and param() are NOT present so arguments pass without ParameterBindingException
        self.assertNotIn("[CmdletBinding()]", content)
        self.assertNotIn("param()", content)
        # Verify portable dynamic path detection
        self.assertIn("$PSScriptRoot", content)

    def test_mp3fy_cmd_content(self):
        self.assertTrue(self.mp3fy_cmd.exists(), "mp3fy.cmd must exist")
        content = self.mp3fy_cmd.read_text(encoding="utf-8")
        self.assertIn("chcp 65001", content)
        self.assertIn("python.exe", content)
        self.assertIn("main.py", content)
        self.assertIn("%*", content)
        self.assertIn("%~dp0", content)
        self.assertIn("exit /b %ERRORLEVEL%", content)

    def test_run_bat_content(self):
        self.assertTrue(self.run_bat.exists(), "run.bat must exist")
        content = self.run_bat.read_text(encoding="utf-8")
        self.assertIn("chcp 65001", content)
        self.assertIn("install.ps1", content)
        self.assertIn("errorlevel 1 exit /b %ERRORLEVEL%", content)
        self.assertIn("main.py", content)
        self.assertIn("exit /b %ERRORLEVEL%", content)

    def test_install_ps1_profile_function_no_cmdletbinding(self):
        content = self.install_ps1.read_text(encoding="utf-8")
        # In the profile snippet, function mp3fy should NOT use [CmdletBinding()] or param()
        self.assertNotIn("[CmdletBinding()]\n    param()\n    & \"$VenvPython\"", content)
        # Verify WinGet Links check
        self.assertIn("WinGet\\Links\\ffmpeg.exe", content)

    def test_run_sh_content_and_syntax(self):
        run_sh = self.project_dir / "run.sh"
        self.assertTrue(run_sh.exists(), "run.sh must exist")
        content = run_sh.read_text(encoding="utf-8")
        self.assertIn("install.sh", content)
        self.assertIn('"$@"', content)
        self.assertIn("$?", content)
        self.assertIn("exit $EXIT_CODE", content)

        # Verify bash syntax
        import subprocess
        result = subprocess.run(["bash", "-n", str(run_sh)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"bash -n run.sh failed: {result.stderr}")

    def test_install_sh_content_and_syntax(self):
        install_sh = self.project_dir / "install.sh"
        self.assertTrue(install_sh.exists(), "install.sh must exist")
        content = install_sh.read_text(encoding="utf-8")
        self.assertIn("python3", content)
        self.assertIn("3.9", content)

        # Verify bash syntax
        import subprocess
        result = subprocess.run(["bash", "-n", str(install_sh)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"bash -n install.sh failed: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
