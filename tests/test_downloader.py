"""Tests for download component exists-check logic (downloader.py)."""

from pathlib import Path

from mibone.downloader import COMPONENTS


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
