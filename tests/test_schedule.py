"""Schedule モデルのテスト。"""

import datetime
import pytest

from models.schedule import Schedule


class TestScheduleCreation:
    """Schedule の生成テスト。"""

    def test_default_id_generated(self):
        s = Schedule()
        assert len(s.id) == 8
        assert s.id.isalnum()

    def test_unique_ids(self):
        s1 = Schedule()
        s2 = Schedule()
        assert s1.id != s2.id

    def test_default_values(self):
        s = Schedule()
        assert s.date_time == ""
        assert s.date_time_type == "exact"
        assert s.title == ""
        assert s.memo == ""
        assert s.created_at != ""

    def test_custom_values(self):
        s = Schedule(
            id="abcd1234",
            date_time="260219_1430",
            date_time_type="from",
            title="会議",
            memo="Q1計画",
        )
        assert s.id == "abcd1234"
        assert s.date_time == "260219_1430"
        assert s.date_time_type == "from"
        assert s.title == "会議"
        assert s.memo == "Q1計画"


class TestScheduleDateKey:
    """date_key プロパティのテスト。"""

    def test_exact(self):
        s = Schedule(date_time="260219_1430")
        assert s.date_key == "260219"

    def test_until(self):
        s = Schedule(date_time="~260219_1430")
        assert s.date_key == "260219"

    def test_from(self):
        s = Schedule(date_time="260219_1430~")
        assert s.date_key == "260219"


class TestScheduleParsedDatetime:
    """parsed_datetime プロパティのテスト。"""

    def test_parsed(self):
        s = Schedule(date_time="260219_1430")
        assert s.parsed_datetime == datetime.datetime(2026, 2, 19, 14, 30)

    def test_parsed_until(self):
        s = Schedule(date_time="~260219_0900")
        assert s.parsed_datetime == datetime.datetime(2026, 2, 19, 9, 0)


class TestScheduleSerialization:
    """to_dict / from_dict のテスト。"""

    def test_to_dict(self):
        s = Schedule(
            id="abc12345",
            date_time="260219_1430",
            date_time_type="exact",
            title="テスト",
            memo="メモ",
            created_at="260218_0900",
        )
        d = s.to_dict()
        assert d == {
            "id": "abc12345",
            "date_time": "260219_1430",
            "date_time_type": "exact",
            "title": "テスト",
            "memo": "メモ",
            "created_at": "260218_0900",
        }

    def test_from_dict(self):
        d = {
            "id": "abc12345",
            "date_time": "260219_1430",
            "date_time_type": "until",
            "title": "テスト",
            "memo": "メモ",
            "created_at": "260218_0900",
        }
        s = Schedule.from_dict(d)
        assert s.id == "abc12345"
        assert s.title == "テスト"
        assert s.date_time_type == "until"

    def test_from_dict_ignores_extra_keys(self):
        d = {
            "id": "abc12345",
            "date_time": "260219_1430",
            "date_time_type": "exact",
            "title": "テスト",
            "memo": "",
            "created_at": "260218_0900",
            "unknown_field": "ignored",
        }
        s = Schedule.from_dict(d)
        assert s.id == "abc12345"
        assert not hasattr(s, "unknown_field")

    def test_roundtrip(self):
        s = Schedule(
            id="abc12345",
            date_time="260219_1430",
            date_time_type="from",
            title="ラウンドトリップ",
            memo="テストメモ",
            created_at="260218_0900",
        )
        s2 = Schedule.from_dict(s.to_dict())
        assert s.id == s2.id
        assert s.date_time == s2.date_time
        assert s.date_time_type == s2.date_time_type
        assert s.title == s2.title
        assert s.memo == s2.memo
        assert s.created_at == s2.created_at
