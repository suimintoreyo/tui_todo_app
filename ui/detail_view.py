"""スケジュール詳細 Widget。"""

from __future__ import annotations

import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView, Static

from models.schedule import Schedule
from utils.datetime_util import format_time_display


class ScheduleItem(ListItem):
    """スケジュール一覧の1行。"""

    def __init__(self, schedule: Schedule) -> None:
        super().__init__()
        self.schedule = schedule

    def compose(self) -> ComposeResult:
        dt = self.schedule.parsed_datetime
        time_str = format_time_display(dt, self.schedule.date_time_type)
        yield Static(
            f"  {time_str}  {self.schedule.title}",
            classes="schedule-item-line",
        )
        if self.schedule.memo:
            yield Static(
                f"         memo: {self.schedule.memo}",
                classes="schedule-item-memo",
            )


class DetailView(Widget):
    """選択された日付のスケジュール詳細を表示する Widget。"""

    class ScheduleHighlighted(Message):
        """スケジュールがハイライトされた。"""
        def __init__(self, schedule: Optional[Schedule]) -> None:
            super().__init__()
            self.schedule = schedule

    selected_date: reactive[datetime.date | None] = reactive(None)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._schedules: list[Schedule] = []

    def compose(self) -> ComposeResult:
        yield Label("── スケジュールなし ──", id="detail-date-label")
        yield ListView(id="schedule-list")

    @property
    def highlighted_schedule(self) -> Schedule | None:
        """現在ハイライト中のスケジュールを返す。"""
        try:
            lv = self.query_one("#schedule-list", ListView)
            if lv.index is not None and 0 <= lv.index < len(self._schedules):
                return self._schedules[lv.index]
        except Exception:
            pass
        return None

    def update_schedules(self, date: datetime.date, schedules: list[Schedule]) -> None:
        """表示する日付とスケジュールを更新する。"""
        self.selected_date = date
        self._schedules = schedules

        try:
            lbl = self.query_one("#detail-date-label", Label)
            lbl.update(f"── {date.strftime('%Y/%m/%d')} ──")
        except Exception:
            pass

        try:
            lv = self.query_one("#schedule-list", ListView)
            lv.clear()
            if schedules:
                for s in schedules:
                    lv.append(ScheduleItem(s))
            else:
                lv.append(ListItem(Static("  スケジュールなし")))
        except Exception:
            pass

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and isinstance(event.item, ScheduleItem):
            self.post_message(self.ScheduleHighlighted(event.item.schedule))
        else:
            self.post_message(self.ScheduleHighlighted(None))
