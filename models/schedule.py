"""Schedule データモデル。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from utils.datetime_util import parse_datetime, now_formatted, extract_date_key


@dataclass
class Schedule:
    """スケジュールレコード。"""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    date_time: str = ""          # YYMMDD_HHMM / ~YYMMDD_HHMM / YYMMDD_HHMM~
    date_time_type: str = "exact"  # exact | until | from
    title: str = ""
    memo: str = ""
    created_at: str = field(default_factory=now_formatted)

    # --- helpers ---

    @property
    def date_key(self) -> str:
        """YYMMDD 部分を返す（日付マッチ用）。"""
        return extract_date_key(self.date_time)

    @property
    def parsed_datetime(self):
        """datetime オブジェクトを返す。"""
        dt, _ = parse_datetime(self.date_time)
        return dt

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Schedule:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
