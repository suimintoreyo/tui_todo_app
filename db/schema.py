"""スケジュールデータのバリデーション。"""

from __future__ import annotations

from utils.datetime_util import parse_datetime


def validate_schedule(data: dict) -> list[str]:
    """スケジュールレコードをバリデーションし、エラーメッセージのリストを返す。"""
    errors: list[str] = []

    if not data.get("title", "").strip():
        errors.append("タイトルは必須です")

    dt = data.get("date_time", "").strip()
    if not dt:
        errors.append("日時は必須です")
    else:
        try:
            parse_datetime(dt)
        except ValueError as e:
            errors.append(f"日時フォーマットエラー: {e}")

    dt_type = data.get("date_time_type", "exact")
    if dt_type not in ("exact", "until", "from"):
        errors.append(f"不正な date_time_type: {dt_type}")

    return errors
