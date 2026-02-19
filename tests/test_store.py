"""store モジュールのテスト。"""

import json
import pytest
from pathlib import Path

from models.schedule import Schedule
from db.store import load_schedules, save_schedules, load_config, save_config


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """テスト用の一時データディレクトリを用意する。"""
    import db.store as store_mod

    test_data_dir = tmp_path / "data"
    test_data_dir.mkdir()
    test_schedule_file = test_data_dir / "schedules.json"
    test_config_file = test_data_dir / "config.json"

    monkeypatch.setattr(store_mod, "DATA_DIR", test_data_dir)
    monkeypatch.setattr(store_mod, "SCHEDULE_FILE", test_schedule_file)
    monkeypatch.setattr(store_mod, "CONFIG_FILE", test_config_file)

    return test_data_dir, test_schedule_file, test_config_file


class TestLoadSchedules:
    """load_schedules のテスト。"""

    def test_empty_when_no_file(self, tmp_data_dir):
        result = load_schedules()
        assert result == []

    def test_load_existing_schedules(self, tmp_data_dir):
        _, schedule_file, _ = tmp_data_dir
        payload = {
            "schedules": [
                {
                    "id": "abc12345",
                    "date_time": "260219_1430",
                    "date_time_type": "exact",
                    "title": "会議",
                    "memo": "",
                    "created_at": "260218_0900",
                }
            ]
        }
        schedule_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        result = load_schedules()
        assert len(result) == 1
        assert result[0].id == "abc12345"
        assert result[0].title == "会議"

    def test_load_multiple_schedules(self, tmp_data_dir):
        _, schedule_file, _ = tmp_data_dir
        payload = {
            "schedules": [
                {
                    "id": "aaa11111",
                    "date_time": "260219_0900",
                    "date_time_type": "exact",
                    "title": "朝会",
                    "memo": "",
                    "created_at": "260218_0900",
                },
                {
                    "id": "bbb22222",
                    "date_time": "260219_1400",
                    "date_time_type": "from",
                    "title": "午後作業",
                    "memo": "コーディング",
                    "created_at": "260218_1000",
                },
            ]
        }
        schedule_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        result = load_schedules()
        assert len(result) == 2


class TestSaveSchedules:
    """save_schedules のテスト。"""

    def test_save_creates_file(self, tmp_data_dir):
        _, schedule_file, _ = tmp_data_dir
        schedules = [
            Schedule(
                id="abc12345",
                date_time="260219_1430",
                date_time_type="exact",
                title="テスト",
                memo="",
                created_at="260218_0900",
            )
        ]
        save_schedules(schedules)

        assert schedule_file.exists()
        data = json.loads(schedule_file.read_text(encoding="utf-8"))
        assert len(data["schedules"]) == 1
        assert data["schedules"][0]["title"] == "テスト"

    def test_save_creates_backup(self, tmp_data_dir):
        _, schedule_file, _ = tmp_data_dir
        save_schedules([
            Schedule(id="first111", date_time="260219_0900", title="最初"),
        ])
        save_schedules([
            Schedule(id="second22", date_time="260219_1400", title="次"),
        ])

        bak_file = schedule_file.with_suffix(".json.bak")
        assert bak_file.exists()
        bak_data = json.loads(bak_file.read_text(encoding="utf-8"))
        assert bak_data["schedules"][0]["id"] == "first111"

    def test_save_and_load_roundtrip(self, tmp_data_dir):
        original = [
            Schedule(
                id="abc12345",
                date_time="260219_1430",
                date_time_type="until",
                title="ラウンドトリップ",
                memo="テストメモ",
                created_at="260218_0900",
            )
        ]
        save_schedules(original)
        loaded = load_schedules()

        assert len(loaded) == 1
        assert loaded[0].id == original[0].id
        assert loaded[0].title == original[0].title
        assert loaded[0].date_time_type == original[0].date_time_type


class TestConfig:
    """config 読み書きのテスト。"""

    def test_empty_when_no_file(self, tmp_data_dir):
        result = load_config()
        assert result == {}

    def test_save_and_load(self, tmp_data_dir):
        config = {"theme": "dark", "language": "ja"}
        save_config(config)
        loaded = load_config()
        assert loaded == config

    def test_overwrite(self, tmp_data_dir):
        save_config({"key": "value1"})
        save_config({"key": "value2"})
        loaded = load_config()
        assert loaded["key"] == "value2"
