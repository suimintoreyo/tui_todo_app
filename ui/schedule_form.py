"""スケジュール追加・編集フォーム（モーダル）。"""

from __future__ import annotations

import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from models.schedule import Schedule
from utils.datetime_util import format_datetime, now_formatted


class ScheduleForm(ModalScreen[Optional[Schedule]]):
    """スケジュール追加・編集モーダルフォーム。"""

    CSS = """
    ScheduleForm {
        align: center middle;
    }

    #form-container {
        width: 60;
        height: auto;
        max-height: 28;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #form-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }

    .form-label {
        margin-top: 1;
    }

    #form-buttons {
        margin-top: 1;
        align: center middle;
    }

    #form-buttons Button {
        margin: 0 1;
    }

    #form-error {
        color: $error;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        date: datetime.date | None = None,
        schedule: Schedule | None = None,
    ) -> None:
        super().__init__()
        self.edit_schedule = schedule
        self.default_date = date or datetime.date.today()

    def compose(self) -> ComposeResult:
        is_edit = self.edit_schedule is not None
        title = "スケジュール編集" if is_edit else "スケジュール追加"

        if is_edit:
            s = self.edit_schedule
            dt = s.parsed_datetime
            default_date_str = dt.strftime("%y%m%d")
            default_time_str = dt.strftime("%H%M")
            default_type = s.date_time_type
            default_title = s.title
            default_memo = s.memo
        else:
            default_date_str = self.default_date.strftime("%y%m%d")
            default_time_str = ""
            default_type = "exact"
            default_title = ""
            default_memo = ""

        with Container(id="form-container"):
            yield Static(title, id="form-title")

            yield Label("日付 (YYMMDD):", classes="form-label")
            yield Input(
                value=default_date_str,
                placeholder="例: 250614",
                id="input-date",
                max_length=6,
            )

            yield Label("時刻 (HHMM):", classes="form-label")
            yield Input(
                value=default_time_str,
                placeholder="例: 1430",
                id="input-time",
                max_length=4,
            )

            yield Label("タイプ:", classes="form-label")
            yield Select(
                [
                    ("指定時刻", "exact"),
                    ("～まで", "until"),
                    ("～以降", "from"),
                ],
                value=default_type,
                id="input-type",
            )

            yield Label("タイトル:", classes="form-label")
            yield Input(
                value=default_title,
                placeholder="スケジュール名",
                id="input-title",
            )

            yield Label("メモ:", classes="form-label")
            yield Input(
                value=default_memo,
                placeholder="メモ（任意）",
                id="input-memo",
            )

            yield Static("", id="form-error")

            with Horizontal(id="form-buttons"):
                yield Button("保存", variant="primary", id="btn-save")
                yield Button("キャンセル", variant="default", id="btn-cancel")

    BINDINGS = [
        ("escape", "cancel", "キャンセル"),
    ]

    def on_mount(self) -> None:
        self.query_one("#input-date", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-save":
            self._save()

    def _save(self) -> None:
        error_widget = self.query_one("#form-error", Static)

        date_str = self.query_one("#input-date", Input).value.strip()
        time_str = self.query_one("#input-time", Input).value.strip()
        dt_type = self.query_one("#input-type", Select).value
        title = self.query_one("#input-title", Input).value.strip()
        memo = self.query_one("#input-memo", Input).value.strip()

        # Validation
        if not title:
            error_widget.update("エラー: タイトルは必須です")
            return

        if not date_str or len(date_str) != 6:
            error_widget.update("エラー: 日付は YYMMDD 形式で入力してください")
            return

        if not time_str or len(time_str) != 4:
            error_widget.update("エラー: 時刻は HHMM 形式で入力してください")
            return

        try:
            int(date_str)
            int(time_str)
        except ValueError:
            error_widget.update("エラー: 日付・時刻は数字で入力してください")
            return

        raw_dt = f"{date_str}_{time_str}"

        # Validate datetime
        from utils.datetime_util import parse_datetime
        try:
            parse_datetime(raw_dt)
        except ValueError:
            error_widget.update("エラー: 無効な日付・時刻です")
            return

        # Format with type prefix/suffix
        if dt_type == "until":
            formatted_dt = f"~{raw_dt}"
        elif dt_type == "from":
            formatted_dt = f"{raw_dt}~"
        else:
            formatted_dt = raw_dt

        if self.edit_schedule:
            schedule = Schedule(
                id=self.edit_schedule.id,
                date_time=formatted_dt,
                date_time_type=dt_type,
                title=title,
                memo=memo,
                created_at=self.edit_schedule.created_at,
            )
        else:
            schedule = Schedule(
                date_time=formatted_dt,
                date_time_type=dt_type,
                title=title,
                memo=memo,
            )

        self.dismiss(schedule)


class ConfirmDialog(ModalScreen[bool]):
    """確認ダイアログ。"""

    CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #confirm-container {
        width: 50;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #confirm-message {
        text-align: center;
        margin-bottom: 1;
    }

    #confirm-buttons {
        align: center middle;
    }

    #confirm-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, message: str = "本当に削除しますか？") -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="confirm-container"):
            yield Static(self._message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button("はい", variant="error", id="btn-yes")
                yield Button("いいえ", variant="default", id="btn-no")

    BINDINGS = [
        ("escape", "cancel", "キャンセル"),
    ]

    def on_mount(self) -> None:
        self.query_one("#btn-no", Button).focus()

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")


class SearchDialog(ModalScreen[Optional[str]]):
    """検索ダイアログ。"""

    CSS = """
    SearchDialog {
        align: center middle;
    }

    #search-container {
        width: 50;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #search-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #search-buttons {
        margin-top: 1;
        align: center middle;
    }

    #search-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="search-container"):
            yield Static("検索", id="search-title")
            yield Input(placeholder="検索キーワード", id="search-input")
            with Horizontal(id="search-buttons"):
                yield Button("検索", variant="primary", id="btn-search")
                yield Button("キャンセル", variant="default", id="btn-search-cancel")

    BINDINGS = [
        ("escape", "cancel", "キャンセル"),
    ]

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-search-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-search":
            q = self.query_one("#search-input", Input).value.strip()
            self.dismiss(q if q else None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        q = event.value.strip()
        self.dismiss(q if q else None)
