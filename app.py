"""Textual App クラス — JSON スケジュール管理 TUI。"""

from __future__ import annotations

import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header, Static, ListView

from db.query import dates_with_schedules, filter_by_date, search_schedules
from db.store import load_schedules, save_schedules
from models.schedule import Schedule
from ui.calendar_view import CalendarView
from ui.detail_view import DetailView
from ui.header_footer import AppFooter
from ui.schedule_form import ConfirmDialog, ScheduleForm, SearchDialog


class ScheduleApp(App):
    """JSON スケジュール管理アプリケーション。"""

    TITLE = "JSON スケジュール管理"

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-rows: 3 1fr 3;
    }

    #app-header {
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $accent;
        color: $text;
        padding: 1;
    }

    #main-area {
        layout: horizontal;
        height: 1fr;
    }

    CalendarView {
        width: 1fr;
        min-width: 32;
        height: 1fr;
        border-right: solid $accent;
    }

    #calendar-container {
        height: auto;
        padding: 0 1;
    }

    #calendar-nav {
        height: 3;
        align: center middle;
    }

    #calendar-nav Button {
        min-width: 4;
        margin: 0 1;
    }

    #month-label {
        text-style: bold;
        width: auto;
    }

    #weekday-header {
        height: 1;
    }

    #weekday-row {
        text-style: bold;
        color: $accent;
    }

    #calendar-grid {
        grid-size: 7;
        grid-gutter: 0;
        height: 1fr;
        padding: 0;
    }

    DayCell {
        width: 4;
        height: 1;
        content-align: right middle;
        color: $text;
    }

    DayCell.today {
        text-style: bold;
        color: $warning;
    }

    DayCell.selected {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    DayCell.has-schedule {
        color: $success;
    }

    DayCell.selected.has-schedule {
        background: $accent;
        color: $text;
    }

    DayCell.other-month {
        color: $text-muted;
    }

    DetailView {
        width: 1fr;
        padding: 0 1;
    }

    #detail-date-label {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin: 1 0;
    }

    #schedule-list {
        height: 1fr;
    }

    .schedule-item-line {
        text-style: bold;
    }

    .schedule-item-memo {
        color: $text-muted;
    }

    #app-footer {
        height: 3;
        content-align: center middle;
        background: $accent;
        color: $text;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("a", "add_schedule", "追加", show=True),
        Binding("e", "edit_schedule", "編集", show=True),
        Binding("d", "delete_schedule", "削除", show=True),
        Binding("slash", "search", "検索", show=True),
        Binding("t", "go_today", "今日", show=True),
        Binding("less_than_sign", "prev_month", "前月", show=True),
        Binding("greater_than_sign", "next_month", "翌月", show=True),
        Binding("tab", "toggle_focus", "切替", show=False),
        Binding("q", "quit_app", "終了", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._schedules: list[Schedule] = []
        self._selected_date: datetime.date = datetime.date.today()

    def compose(self) -> ComposeResult:
        yield Static("JSON スケジュール管理", id="app-header")
        with Horizontal(id="main-area"):
            yield CalendarView(id="calendar-view")
            yield DetailView(id="detail-view")
        yield AppFooter(id="app-footer")

    def on_mount(self) -> None:
        self._load_data()
        self._refresh_views()

    # ---- data ----

    def _load_data(self) -> None:
        self._schedules = load_schedules()

    def _save_data(self) -> None:
        save_schedules(self._schedules)

    def _schedule_date_keys(self) -> set[str]:
        return dates_with_schedules(self._schedules)

    def _schedules_for_date(self, d: datetime.date) -> list[Schedule]:
        return filter_by_date(self._schedules, d)

    # ---- view refresh ----

    def _refresh_views(self) -> None:
        cal = self.query_one("#calendar-view", CalendarView)
        cal.update_schedule_dates(self._schedule_date_keys())

        detail = self.query_one("#detail-view", DetailView)
        detail.update_schedules(
            self._selected_date,
            self._schedules_for_date(self._selected_date),
        )

    # ---- events ----

    def on_calendar_view_date_selected(self, event: CalendarView.DateSelected) -> None:
        self._selected_date = event.date
        detail = self.query_one("#detail-view", DetailView)
        detail.update_schedules(
            event.date,
            self._schedules_for_date(event.date),
        )

    # ---- actions ----

    def action_add_schedule(self) -> None:
        self.push_screen(
            ScheduleForm(date=self._selected_date),
            callback=self._on_schedule_form_result,
        )

    def _on_schedule_form_result(self, result: Optional[Schedule]) -> None:
        if result is None:
            return
        self._schedules.append(result)
        self._save_data()
        # Navigate to the date of the new schedule
        dt = result.parsed_datetime
        new_date = dt.date()
        self._selected_date = new_date
        cal = self.query_one("#calendar-view", CalendarView)
        cal.select_date(new_date)
        self._refresh_views()

    def action_edit_schedule(self) -> None:
        detail = self.query_one("#detail-view", DetailView)
        schedule = detail.highlighted_schedule
        if schedule is None:
            self.notify("編集するスケジュールを選択してください", severity="warning")
            return
        self.push_screen(
            ScheduleForm(schedule=schedule),
            callback=self._on_edit_form_result,
        )

    def _on_edit_form_result(self, result: Optional[Schedule]) -> None:
        if result is None:
            return
        # Replace schedule with same id
        self._schedules = [
            result if s.id == result.id else s for s in self._schedules
        ]
        self._save_data()
        dt = result.parsed_datetime
        new_date = dt.date()
        self._selected_date = new_date
        cal = self.query_one("#calendar-view", CalendarView)
        cal.select_date(new_date)
        self._refresh_views()

    def action_delete_schedule(self) -> None:
        detail = self.query_one("#detail-view", DetailView)
        schedule = detail.highlighted_schedule
        if schedule is None:
            self.notify("削除するスケジュールを選択してください", severity="warning")
            return
        self.push_screen(
            ConfirmDialog(f"「{schedule.title}」を削除しますか？"),
            callback=self._on_delete_confirm,
        )

    def _on_delete_confirm(self, confirmed: bool) -> None:
        if not confirmed:
            return
        detail = self.query_one("#detail-view", DetailView)
        schedule = detail.highlighted_schedule
        if schedule:
            self._schedules = [s for s in self._schedules if s.id != schedule.id]
            self._save_data()
            self._refresh_views()
            self.notify("削除しました", severity="information")

    def action_search(self) -> None:
        self.push_screen(SearchDialog(), callback=self._on_search_result)

    def _on_search_result(self, query: Optional[str]) -> None:
        if not query:
            self._refresh_views()
            return
        results = search_schedules(self._schedules, query)
        if not results:
            self.notify("見つかりませんでした", severity="warning")
            return
        # Navigate to the first result's date
        first = results[0]
        dt = first.parsed_datetime
        d = dt.date()
        self._selected_date = d
        cal = self.query_one("#calendar-view", CalendarView)
        cal.select_date(d)
        self._refresh_views()
        self.notify(f"{len(results)}件見つかりました", severity="information")

    def action_go_today(self) -> None:
        cal = self.query_one("#calendar-view", CalendarView)
        cal.go_today()

    def action_prev_month(self) -> None:
        cal = self.query_one("#calendar-view", CalendarView)
        cal.go_prev_month()

    def action_next_month(self) -> None:
        cal = self.query_one("#calendar-view", CalendarView)
        cal.go_next_month()

    def action_toggle_focus(self) -> None:
        """カレンダー ↔ 詳細ビューのフォーカスを切り替える。"""
        detail = self.query_one("#detail-view", DetailView)
        cal = self.query_one("#calendar-view", CalendarView)

        try:
            lv = detail.query_one("#schedule-list", ListView)
            if lv.has_focus:
                cal.focus()
            else:
                lv.focus()
        except Exception:
            cal.focus()

    def action_quit_app(self) -> None:
        self.exit()

