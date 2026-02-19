"""schema バリデーションのテスト。"""

import pytest

from db.schema import validate_schedule


class TestValidateSchedule:
    """validate_schedule のテスト。"""

    def test_valid_data(self):
        data = {
            "title": "会議",
            "date_time": "260219_1430",
            "date_time_type": "exact",
        }
        errors = validate_schedule(data)
        assert errors == []

    def test_valid_until(self):
        data = {
            "title": "締め切り",
            "date_time": "~260219_1430",
            "date_time_type": "until",
        }
        errors = validate_schedule(data)
        assert errors == []

    def test_valid_from(self):
        data = {
            "title": "開始",
            "date_time": "260219_1430~",
            "date_time_type": "from",
        }
        errors = validate_schedule(data)
        assert errors == []

    def test_missing_title(self):
        data = {
            "title": "",
            "date_time": "260219_1430",
        }
        errors = validate_schedule(data)
        assert len(errors) == 1
        assert "タイトル" in errors[0]

    def test_whitespace_only_title(self):
        data = {
            "title": "   ",
            "date_time": "260219_1430",
        }
        errors = validate_schedule(data)
        assert len(errors) == 1
        assert "タイトル" in errors[0]

    def test_no_title_key(self):
        data = {
            "date_time": "260219_1430",
        }
        errors = validate_schedule(data)
        assert any("タイトル" in e for e in errors)

    def test_missing_date_time(self):
        data = {
            "title": "会議",
            "date_time": "",
        }
        errors = validate_schedule(data)
        assert len(errors) == 1
        assert "日時" in errors[0]

    def test_no_date_time_key(self):
        data = {
            "title": "会議",
        }
        errors = validate_schedule(data)
        assert any("日時" in e for e in errors)

    def test_invalid_date_time_format(self):
        data = {
            "title": "会議",
            "date_time": "invalid",
        }
        errors = validate_schedule(data)
        assert len(errors) == 1
        assert "フォーマット" in errors[0]

    def test_invalid_date_time_type(self):
        data = {
            "title": "会議",
            "date_time": "260219_1430",
            "date_time_type": "invalid_type",
        }
        errors = validate_schedule(data)
        assert len(errors) == 1
        assert "date_time_type" in errors[0]

    def test_default_date_time_type_is_exact(self):
        """date_time_type が省略された場合は exact としてバリデーション成功。"""
        data = {
            "title": "会議",
            "date_time": "260219_1430",
        }
        errors = validate_schedule(data)
        assert errors == []

    def test_multiple_errors(self):
        data = {
            "title": "",
            "date_time": "",
            "date_time_type": "bad",
        }
        errors = validate_schedule(data)
        assert len(errors) == 3
