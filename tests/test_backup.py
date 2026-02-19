"""backup モジュールのテスト。"""

import pytest
from pathlib import Path

from utils.backup import create_backup


class TestCreateBackup:
    """create_backup のテスト。"""

    def test_creates_bak_file(self, tmp_path):
        original = tmp_path / "test.json"
        original.write_text('{"data": "original"}', encoding="utf-8")

        bak = create_backup(original)

        assert bak is not None
        assert bak.exists()
        assert bak.name == "test.json.bak"
        assert bak.read_text(encoding="utf-8") == '{"data": "original"}'

    def test_overwrites_existing_backup(self, tmp_path):
        original = tmp_path / "test.json"
        original.write_text("version1", encoding="utf-8")
        create_backup(original)

        original.write_text("version2", encoding="utf-8")
        bak = create_backup(original)

        assert bak.read_text(encoding="utf-8") == "version2"

    def test_returns_none_for_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        result = create_backup(missing)
        assert result is None

    def test_preserves_original(self, tmp_path):
        original = tmp_path / "test.json"
        original.write_text("original content", encoding="utf-8")

        create_backup(original)

        assert original.read_text(encoding="utf-8") == "original content"
