"""Tests for utility functions (utils.py)."""

from pathlib import Path

from mibone.utils import load_yaml, save_yaml, print_bi, print_ok, print_err, print_warn


class TestYamlIO:
    def test_save_load_roundtrip(self, tmp_path):
        data = {"key": "value", "nested": {"a": 1, "b": [2, 3]}}
        path = tmp_path / "test.yaml"
        save_yaml(data, path)
        loaded = load_yaml(path)
        assert loaded == data

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "file.yaml"
        save_yaml({"x": 1}, path)
        assert path.exists()

    def test_load_empty_file(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        result = load_yaml(path)
        assert result == {}

    def test_unicode_roundtrip(self, tmp_path):
        data = {"名称": "测试订阅", "proxies": ["🚀 节点选择"]}
        path = tmp_path / "unicode.yaml"
        save_yaml(data, path)
        loaded = load_yaml(path)
        assert loaded["名称"] == "测试订阅"
        assert loaded["proxies"] == ["🚀 节点选择"]


class TestPrintFunctions:
    def test_print_bi(self, capsys):
        print_bi("中文", "English")
        assert capsys.readouterr().out == "中文 (English)\n"

    def test_print_ok(self, capsys):
        print_ok("成功", "Success")
        assert "✓" in capsys.readouterr().out

    def test_print_err(self, capsys):
        print_err("失败", "Failed")
        assert "✗" in capsys.readouterr().err

    def test_print_warn(self, capsys):
        print_warn("警告", "Warning")
        assert "!" in capsys.readouterr().out
