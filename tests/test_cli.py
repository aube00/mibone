"""Tests for CLI argument parsing (cli.py)."""

import subprocess
import sys


class TestCLI:
    def test_version_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "mibone", "--version"],
            capture_output=True,
            text=True,
            cwd=str(__import__("pathlib").Path(__file__).parent.parent / "src"),
        )
        assert result.returncode == 0
        assert "mibone" in result.stdout
        assert "0.1.0" in result.stdout

    def test_no_args_shows_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "mibone"],
            capture_output=True,
            text=True,
            cwd=str(__import__("pathlib").Path(__file__).parent.parent / "src"),
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "mibone" in result.stdout
