"""月カレンダー Widget。"""

from __future__ import annotations

import calendar
import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Grid
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, Static


class DayCell(Static):
    """カレンダーの1日分のセル。"""

    class Selected(Message):
        """日付が選択された。"""
        def __init__(self, date: datetime.date) -> None:
            super().__init__()
            self.date = date

    can_focus = True

    def __init__(
        self,
        day: int,
        date: datetime.date,
        is_today: bool = False,
        has_schedule: bool = False,
        is_selected: bool = False,
        is_other_month: bool = False,
    ) -> None:
        super().__init__()
        self.day = day
        self.date = date
        self.is_today = is_today
        self.has_schedule = has_schedule
        self.is_selected = is_selected
        self.is_other_month = is_other_month

    def render(self) -> str:
        if self.day == 0:
            return "    "
        marker = " ●" if self.has_schedule else "  "
        return f"{self.day:>2}{marker}"

    def on_mount(self) -> None:
        self._apply_styles()

    def _apply_styles(self) -> None:
        self.remove_class("today", "selected", "has-schedule", "other-month")
        if self.is_other_month:
            self.add_class("other-month")
        if self.is_today:
            self.add_class("today")
        if self.has_schedule:
            self.add_class("has-schedule")
        if self.is_selected:
            self.add_class("selected")

    def on_click(self) -> None:
        if self.day > 0 and not self.is_other_month:
            self.post_message(self.Selected(self.date))

    def on_key(self, event) -> None:
        if event.key == "enter" and self.day > 0 and not self.is_other_month:
            self.post_message(self.Selected(self.date))


class CalendarView(Widget):
    """月カレンダーの表示 Widget。"""

    class DateSelected(Message):
        """カレンダーの日付が選択された。"""
        def __init__(self, date: datetime.date) -> None:
            super().__init__()
            self.date = date

    class MonthChanged(Message):
        """月が変更された。"""
        def __init__(self, year: int, month: int) -> None:
            super().__init__()
            self.year = year
            self.month = month

    current_year: reactive[int] = reactive(datetime.date.today().year)
    current_month: reactive[int] = reactive(datetime.date.today().month)
    selected_date: reactive[datetime.date] = reactive(datetime.date.today)

    def __init__(
        self,
        schedule_dates: set[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.schedule_dates: set[str] = schedule_dates or set()

    def compose(self) -> ComposeResult:
        with Container(id="calendar-container"):
            with Horizontal(id="calendar-nav"):
                yield Button("◀", id="prev-month", variant="default")
                yield Label(self._month_label(), id="month-label")
                yield Button("▶", id="next-month", variant="default")
            with Container(id="weekday-header"):
                yield Static(" Mon Tue Wed Thu Fri Sat Sun", id="weekday-row")
            yield Grid(id="calendar-grid")

    def on_mount(self) -> None:
        self._rebuild_calendar()

    def _month_label(self) -> str:
        return f" {self.current_year}年{self.current_month:02d}月 "

    def watch_current_year(self) -> None:
        self._update_month_label()
        self._rebuild_calendar()

    def watch_current_month(self) -> None:
        self._update_month_label()
        self._rebuild_calendar()

    def _update_month_label(self) -> None:
        try:
            lbl = self.query_one("#month-label", Label)
            lbl.update(self._month_label())
        except Exception:
            pass

    def _rebuild_calendar(self) -> None:
        try:
            grid = self.query_one("#calendar-grid", Grid)
        except Exception:
            return

        grid.remove_children()

        today = datetime.date.today()
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        from utils.datetime_util import date_to_key

        cells: list[DayCell] = []
        for week in cal:
            for day in week:
                if day == 0:
                    cell = DayCell(
                        day=0,
                        date=today,
                        is_other_month=True,
                    )
                else:
                    d = datetime.date(self.current_year, self.current_month, day)
                    dk = date_to_key(d)
                    cell = DayCell(
                        day=day,
                        date=d,
                        is_today=(d == today),
                        has_schedule=(dk in self.schedule_dates),
                        is_selected=(d == self.selected_date),
                    )
                cells.append(cell)
        grid.mount_all(cells)

    def on_day_cell_selected(self, event: DayCell.Selected) -> None:
        self.selected_date = event.date
        self._rebuild_calendar()
        self.post_message(self.DateSelected(event.date))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "prev-month":
            self.go_prev_month()
        elif event.button.id == "next-month":
            self.go_next_month()

    def go_prev_month(self) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.post_message(self.MonthChanged(self.current_year, self.current_month))

    def go_next_month(self) -> None:
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.post_message(self.MonthChanged(self.current_year, self.current_month))

    def go_today(self) -> None:
        today = datetime.date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = today
        self._rebuild_calendar()
        self.post_message(self.DateSelected(today))

    def update_schedule_dates(self, dates: set[str]) -> None:
        self.schedule_dates = dates
        self._rebuild_calendar()

    def select_date(self, d: datetime.date) -> None:
        self.current_year = d.year
        self.current_month = d.month
        self.selected_date = d
        self._rebuild_calendar()
        self.post_message(self.DateSelected(d))
