"""Tests for scanner module."""
import os
from pathlib import Path
import pytest
from pyscan.scanner import Scanner


class TestScanner:
    """Test Scanner class."""

    def test_scan_directory(self, tmp_path):
        """测试扫描目录下的 Python 文件。"""
        # 创建测试文件
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.py").write_text("print('world')")
        (tmp_path / "readme.md").write_text("# README")

        scanner = Scanner()
        files = scanner.scan(str(tmp_path))

        assert len(files) == 2
        assert any("file1.py" in f for f in files)
        assert any("file2.py" in f for f in files)
        assert not any("readme.md" in f for f in files)

    def test_scan_nested_directories(self, tmp_path):
        """测试扫描嵌套目录。"""
        # 创建嵌套目录结构
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        (tmp_path / "root.py").write_text("# root")
        (sub_dir / "nested.py").write_text("# nested")

        scanner = Scanner()
        files = scanner.scan(str(tmp_path))

        assert len(files) == 2
        assert any("root.py" in f for f in files)
        assert any("nested.py" in f for f in files)

    def test_exclude_patterns(self, tmp_path):
        """测试排除模式。"""
        (tmp_path / "main.py").write_text("# main")
        (tmp_path / "test_main.py").write_text("# test")
        (tmp_path / "config.py").write_text("# config")

        scanner = Scanner(exclude_patterns=["test_*.py", "config.py"])
        files = scanner.scan(str(tmp_path))

        assert len(files) == 1
        assert any("main.py" in f for f in files)
        assert not any("test_main.py" in f for f in files)
        assert not any("config.py" in f for f in files)

    def test_exclude_venv_directories(self, tmp_path):
        """测试排除虚拟环境目录。"""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (tmp_path / "app.py").write_text("# app")
        (venv_dir / "lib.py").write_text("# lib")

        scanner = Scanner(exclude_patterns=["*/venv/*"])
        files = scanner.scan(str(tmp_path))

        assert len(files) == 1
        assert any("app.py" in f for f in files)
        assert not any("lib.py" in f for f in files)

    def test_exclude_site_packages(self, tmp_path):
        """测试排除 site-packages 目录。"""
        site_packages = tmp_path / "site-packages"
        site_packages.mkdir()
        (tmp_path / "mycode.py").write_text("# mycode")
        (site_packages / "library.py").write_text("# library")

        scanner = Scanner(exclude_patterns=["*/site-packages/*"])
        files = scanner.scan(str(tmp_path))

        assert len(files) == 1
        assert any("mycode.py" in f for f in files)
        assert not any("library.py" in f for f in files)

    def test_empty_directory(self, tmp_path):
        """测试空目录。"""
        scanner = Scanner()
        files = scanner.scan(str(tmp_path))

        assert len(files) == 0

    def test_directory_not_found(self):
        """测试目录不存在。"""
        scanner = Scanner()
        with pytest.raises(FileNotFoundError):
            scanner.scan("non_existent_directory")

    def test_scan_returns_absolute_paths(self, tmp_path):
        """测试返回绝对路径。"""
        (tmp_path / "test.py").write_text("# test")

        scanner = Scanner()
        files = scanner.scan(str(tmp_path))

        assert len(files) == 1
        assert Path(files[0]).is_absolute()
