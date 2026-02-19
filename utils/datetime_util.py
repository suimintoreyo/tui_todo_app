"""YYMMDD_HHMM 形式の日時パーサー・フォーマッター。

仕様書のフォーマット YYMM_HHSS を日(DD)を含む YYMMDD_HHMM に拡張。
例: 250614_1430 → 2025年6月14日 14:30

タイプ表記:
  - exact:  250614_1430   (その時刻)
  - until:  ~250614_1430  (その時刻まで)
  - from:   250614_1430~  (その時刻以降)
"""

from __future__ import annotations

import datetime


def parse_datetime(raw: str) -> tuple[datetime.datetime, str]:
    """日時文字列をパースし (datetime, type) を返す。

    Args:
        raw: "YYMMDD_HHMM" / "~YYMMDD_HHMM" / "YYMMDD_HHMM~"

    Returns:
        (datetime, date_time_type) のタプル

    Raises:
        ValueError: フォーマット不正
    """
    dt_type = "exact"
    s = raw.strip()

    if s.startswith("~"):
        dt_type = "until"
        s = s[1:]
    elif s.endswith("~"):
        dt_type = "from"
        s = s[:-1]

    if len(s) != 11 or s[6] != "_":
        raise ValueError(f"Invalid datetime format: {raw!r}  (expected YYMMDD_HHMM)")

    yy = int(s[0:2])
    mm = int(s[2:4])
    dd = int(s[4:6])
    hh = int(s[7:9])
    mi = int(s[9:11])

    year = 2000 + yy
    dt = datetime.datetime(year, mm, dd, hh, mi)
    return dt, dt_type


def format_datetime(dt: datetime.datetime, dt_type: str = "exact") -> str:
    """datetime を YYMMDD_HHMM 形式に変換する。"""
    s = dt.strftime("%y%m%d_%H%M")
    if dt_type == "until":
        return f"~{s}"
    elif dt_type == "from":
        return f"{s}~"
    return s


def format_time_display(dt: datetime.datetime, dt_type: str = "exact") -> str:
    """詳細ビュー用の時刻表示を生成する。"""
    t = dt.strftime("%H:%M")
    if dt_type == "until":
        return f"~{t}"
    elif dt_type == "from":
        return f"{t}~"
    return t


def now_formatted() -> str:
    """現在日時を YYMMDD_HHMM 形式で返す。"""
    return format_datetime(datetime.datetime.now())


def date_to_key(d: datetime.date) -> str:
    """date オブジェクトを YYMMDD 文字列に変換する（検索用キー）。"""
    return d.strftime("%y%m%d")


def extract_date_key(raw: str) -> str:
    """日時文字列から YYMMDD 部分を抽出する。"""
    s = raw.strip().lstrip("~")
    if s.endswith("~"):
        s = s[:-1]
    return s[:6]
