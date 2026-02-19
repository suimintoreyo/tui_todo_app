"""検索・フィルタ・ソートエンジン。"""

from __future__ import annotations

import datetime
from models.schedule import Schedule
from utils.datetime_util import date_to_key


def filter_by_date(schedules: list[Schedule], d: datetime.date) -> list[Schedule]:
    """指定日付のスケジュールを抽出し、時刻順でソートして返す。"""
    key = date_to_key(d)
    matched = [s for s in schedules if s.date_key == key]
    matched.sort(key=lambda s: s.parsed_datetime)
    return matched


def dates_with_schedules(schedules: list[Schedule]) -> set[str]:
    """スケジュールが存在する日付キー (YYMMDD) の集合を返す。"""
    return {s.date_key for s in schedules}


def search_schedules(schedules: list[Schedule], query: str) -> list[Schedule]:
    """タイトルまたはメモにクエリを含むスケジュールを検索する。"""
    q = query.lower()
    return [
        s for s in schedules
        if q in s.title.lower() or q in s.memo.lower()
    ]
