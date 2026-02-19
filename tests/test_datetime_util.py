"""datetime_util モジュールのテスト。"""

import datetime
import pytest

from utils.datetime_util import (
    parse_datetime,
    format_datetime,
    format_time_display,
    now_formatted,
    date_to_key,
    extract_date_key,
)


# ── parse_datetime ──────────────────────────────────────────


class TestParseDatetime:
    """parse_datetime のテスト。"""

    def test_exact(self):
        dt, dt_type = parse_datetime("260219_1430")
        assert dt == datetime.datetime(2026, 2, 19, 14, 30)
        assert dt_type == "exact"

    def test_until(self):
        dt, dt_type = parse_datetime("~260219_1430")
        assert dt == datetime.datetime(2026, 2, 19, 14, 30)
        assert dt_type == "until"

    def test_from(self):
        dt, dt_type = parse_datetime("260219_1430~")
        assert dt == datetime.datetime(2026, 2, 19, 14, 30)
        assert dt_type == "from"

    def test_midnight(self):
        dt, dt_type = parse_datetime("260101_0000")
        assert dt == datetime.datetime(2026, 1, 1, 0, 0)
        assert dt_type == "exact"

    def test_end_of_day(self):
        dt, dt_type = parse_datetime("261231_2359")
        assert dt == datetime.datetime(2026, 12, 31, 23, 59)
        assert dt_type == "exact"

    def test_with_whitespace(self):
        dt, dt_type = parse_datetime("  260219_1430  ")
        assert dt == datetime.datetime(2026, 2, 19, 14, 30)

    def test_invalid_format_short(self):
        with pytest.raises(ValueError):
            parse_datetime("2602_1430")

    def test_invalid_format_no_underscore(self):
        with pytest.raises(ValueError):
            parse_datetime("26021914300")

    def test_invalid_month(self):
        with pytest.raises(ValueError):
            parse_datetime("261319_1430")

    def test_invalid_day(self):
        with pytest.raises(ValueError):
            parse_datetime("260232_1430")

    def test_invalid_hour(self):
        with pytest.raises(ValueError):
            parse_datetime("260219_2530")


# ── format_datetime ─────────────────────────────────────────


class TestFormatDatetime:
    """format_datetime のテスト。"""

    def test_exact(self):
        dt = datetime.datetime(2026, 2, 19, 14, 30)
        assert format_datetime(dt, "exact") == "260219_1430"

    def test_until(self):
        dt = datetime.datetime(2026, 2, 19, 14, 30)
        assert format_datetime(dt, "until") == "~260219_1430"

    def test_from(self):
        dt = datetime.datetime(2026, 2, 19, 14, 30)
        assert format_datetime(dt, "from") == "260219_1430~"

    def test_default_type(self):
        dt = datetime.datetime(2026, 1, 1, 0, 0)
        assert format_datetime(dt) == "260101_0000"

    def test_roundtrip_exact(self):
        original = "260614_0900"
        dt, dt_type = parse_datetime(original)
        assert format_datetime(dt, dt_type) == original

    def test_roundtrip_until(self):
        original = "~260614_0900"
        dt, dt_type = parse_datetime(original)
        assert format_datetime(dt, dt_type) == original

    def test_roundtrip_from(self):
        original = "260614_0900~"
        dt, dt_type = parse_datetime(original)
        assert format_datetime(dt, dt_type) == original


# ── format_time_display ─────────────────────────────────────


class TestFormatTimeDisplay:
    """format_time_display のテスト。"""

    def test_exact(self):
        dt = datetime.datetime(2026, 2, 19, 14, 30)
        assert format_time_display(dt, "exact") == "14:30"

    def test_until(self):
        dt = datetime.datetime(2026, 2, 19, 14, 30)
        assert format_time_display(dt, "until") == "~14:30"

    def test_from(self):
        dt = datetime.datetime(2026, 2, 19, 14, 30)
        assert format_time_display(dt, "from") == "14:30~"

    def test_midnight(self):
        dt = datetime.datetime(2026, 1, 1, 0, 0)
        assert format_time_display(dt) == "00:00"


# ── now_formatted ───────────────────────────────────────────


class TestNowFormatted:
    """now_formatted のテスト。"""

    def test_returns_valid_format(self):
        result = now_formatted()
        assert len(result) == 11
        assert result[6] == "_"
        # パースできることを確認
        parse_datetime(result)


# ── date_to_key ─────────────────────────────────────────────


class TestDateToKey:
    """date_to_key のテスト。"""

    def test_basic(self):
        d = datetime.date(2026, 2, 19)
        assert date_to_key(d) == "260219"

    def test_single_digit_month(self):
        d = datetime.date(2026, 1, 5)
        assert date_to_key(d) == "260105"

    def test_year_2000(self):
        d = datetime.date(2000, 12, 31)
        assert date_to_key(d) == "001231"


# ── extract_date_key ────────────────────────────────────────


class TestExtractDateKey:
    """extract_date_key のテスト。"""

    def test_exact(self):
        assert extract_date_key("260219_1430") == "260219"

    def test_until(self):
        assert extract_date_key("~260219_1430") == "260219"

    def test_from(self):
        assert extract_date_key("260219_1430~") == "260219"

    def test_with_whitespace(self):
        assert extract_date_key("  ~260219_1430  ") == "260219"
