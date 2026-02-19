"""ヘッダー・フッター Widget。"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Footer, Header, Static


class AppHeader(Static):
    """アプリケーションヘッダー。"""

    def render(self) -> str:
        return "JSON スケジュール管理"


class AppFooter(Static):
    """キーバインド表示用フッター。"""

    def render(self) -> str:
        return " a:追加  e:編集  d:削除  /:検索  t:今日  </>:月切替  Tab:切替  q:終了"
