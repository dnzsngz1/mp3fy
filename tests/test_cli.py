"""
Unit tests for MP3fy CLI interface and arguments.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import main


class TestCLI(unittest.TestCase):
    def test_version(self):
        self.assertTrue(hasattr(main, "VERSION"))
        self.assertEqual(main.VERSION, "1.1.0")

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


if __name__ == "__main__":
    unittest.main()
