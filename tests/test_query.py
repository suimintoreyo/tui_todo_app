"""query モジュールのテスト。"""

import datetime
import pytest

from models.schedule import Schedule
from db.query import filter_by_date, dates_with_schedules, search_schedules


def _make_schedule(date_time: str, title: str = "テスト", memo: str = "") -> Schedule:
    return Schedule(
        date_time=date_time,
        title=title,
        memo=memo,
    )


class TestFilterByDate:
    """filter_by_date のテスト。"""

    def test_filters_matching_date(self):
        schedules = [
            _make_schedule("260219_0900", title="朝会"),
            _make_schedule("260219_1400", title="午後会議"),
            _make_schedule("260220_1000", title="別の日"),
        ]
        result = filter_by_date(schedules, datetime.date(2026, 2, 19))
        assert len(result) == 2
        assert result[0].title == "朝会"
        assert result[1].title == "午後会議"

    def test_sorted_by_time(self):
        schedules = [
            _make_schedule("260219_1400", title="午後"),
            _make_schedule("260219_0900", title="朝"),
            _make_schedule("260219_1200", title="昼"),
        ]
        result = filter_by_date(schedules, datetime.date(2026, 2, 19))
        assert [s.title for s in result] == ["朝", "昼", "午後"]

    def test_no_match(self):
        schedules = [
            _make_schedule("260219_0900"),
        ]
        result = filter_by_date(schedules, datetime.date(2026, 2, 20))
        assert result == []

    def test_empty_list(self):
        result = filter_by_date([], datetime.date(2026, 2, 19))
        assert result == []

    def test_with_until_type(self):
        schedules = [
            _make_schedule("~260219_1430", title="まで"),
        ]
        result = filter_by_date(schedules, datetime.date(2026, 2, 19))
        assert len(result) == 1
        assert result[0].title == "まで"

    def test_with_from_type(self):
        schedules = [
            _make_schedule("260219_1430~", title="から"),
        ]
        result = filter_by_date(schedules, datetime.date(2026, 2, 19))
        assert len(result) == 1
        assert result[0].title == "から"


class TestDatesWithSchedules:
    """dates_with_schedules のテスト。"""

    def test_returns_unique_date_keys(self):
        schedules = [
            _make_schedule("260219_0900"),
            _make_schedule("260219_1400"),
            _make_schedule("260220_1000"),
        ]
        result = dates_with_schedules(schedules)
        assert result == {"260219", "260220"}

    def test_empty_list(self):
        assert dates_with_schedules([]) == set()

    def test_single_schedule(self):
        schedules = [_make_schedule("260301_1200")]
        result = dates_with_schedules(schedules)
        assert result == {"260301"}


class TestSearchSchedules:
    """search_schedules のテスト。"""

    def test_search_by_title(self):
        schedules = [
            _make_schedule("260219_0900", title="チーム会議"),
            _make_schedule("260219_1400", title="ランチ"),
        ]
        result = search_schedules(schedules, "会議")
        assert len(result) == 1
        assert result[0].title == "チーム会議"

    def test_search_by_memo(self):
        schedules = [
            _make_schedule("260219_0900", title="会議", memo="Q1計画について"),
            _make_schedule("260219_1400", title="ランチ", memo=""),
        ]
        result = search_schedules(schedules, "計画")
        assert len(result) == 1
        assert result[0].title == "会議"

    def test_case_insensitive(self):
        schedules = [
            _make_schedule("260219_0900", title="Team Meeting"),
        ]
        result = search_schedules(schedules, "team")
        assert len(result) == 1

        result2 = search_schedules(schedules, "MEETING")
        assert len(result2) == 1

    def test_no_match(self):
        schedules = [
            _make_schedule("260219_0900", title="会議"),
        ]
        result = search_schedules(schedules, "ランチ")
        assert result == []

    def test_empty_query(self):
        schedules = [
            _make_schedule("260219_0900", title="会議"),
            _make_schedule("260219_1400", title="ランチ"),
        ]
        result = search_schedules(schedules, "")
        assert len(result) == 2

    def test_empty_list(self):
        result = search_schedules([], "会議")
        assert result == []

    def test_partial_match(self):
        schedules = [
            _make_schedule("260219_0900", title="プロジェクト会議"),
        ]
        result = search_schedules(schedules, "プロジェクト")
        assert len(result) == 1
