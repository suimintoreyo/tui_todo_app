#!/usr/bin/env python3
"""JSON スケジュール管理 TUI — エントリポイント。"""

from app import ScheduleApp


def main() -> None:
    app = ScheduleApp()
    app.run()


if __name__ == "__main__":
    main()
