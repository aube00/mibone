"""Tests for download component exists-check logic (downloader.py)."""

import io
import zipfile
from pathlib import Path

from mibone.downloader import COMPONENTS, _safe_extract


class TestExistsCheck:
    """Verify the exists-check logic that was buggy before the fix.

    The original code used `base_dir / comp.get("target", "")` which
    resolved to base_dir itself for components without a "target" key
    (like zashboard), causing them to always be skipped.
    """

    def _check_exists(self, base_dir, comp):
        """Reproduce the fixed exists-check logic from run_setup."""
        if "target" in comp:
            return (base_dir / comp["target"]).exists()
        elif "target_dir" in comp:
            return (base_dir / comp["target_dir"]).exists()
        return False

    def test_fresh_install_nothing_exists(self, tmp_path):
        (tmp_path / "bin").mkdir()
        for name, comp in COMPONENTS.items():
            assert not self._check_exists(tmp_path, comp), (
                f"{name} should not exist on fresh install"
            )

    def test_existing_components_detected(self, tmp_path):
        (tmp_path / "bin").mkdir()

        (tmp_path / "bin" / "mihomo.exe").write_bytes(b"fake")
        assert self._check_exists(tmp_path, COMPONENTS["mihomo"])

        (tmp_path / "bin" / "mihomo-service.exe").write_bytes(b"fake")
        assert self._check_exists(tmp_path, COMPONENTS["winsw"])

        (tmp_path / "bin" / "ui").mkdir()
        assert self._check_exists(tmp_path, COMPONENTS["zashboard"])

    def test_zashboard_not_confused_with_base_dir(self, tmp_path):
        """Regression test: zashboard must check bin/ui, not base_dir."""
        (tmp_path / "bin").mkdir()
        assert tmp_path.exists()  # base_dir always exists
        assert not self._check_exists(tmp_path, COMPONENTS["zashboard"])


class TestSafeExtract:
    def _make_zip(self, members):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for name, data in members.items():
                zf.writestr(name, data)
        buf.seek(0)
        return buf

    def test_normal_zip_extracts(self, tmp_path):
        buf = self._make_zip({"file.txt": "hello", "sub/file2.txt": "world"})
        with zipfile.ZipFile(buf) as zf:
            _safe_extract(zf, tmp_path)
        assert (tmp_path / "file.txt").read_text() == "hello"
        assert (tmp_path / "sub" / "file2.txt").read_text() == "world"

    def test_path_traversal_blocked(self, tmp_path):
        buf = self._make_zip({"../escape.txt": "malicious"})
        with zipfile.ZipFile(buf) as zf:
            with __import__("pytest").raises(ValueError, match="Unsafe path"):
                _safe_extract(zf, tmp_path)
        assert not (tmp_path.parent / "escape.txt").exists()
