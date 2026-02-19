"""バックアップ管理ユーティリティ。"""

from __future__ import annotations

import shutil
from pathlib import Path


def create_backup(filepath: Path) -> Path | None:
    """ファイルの .bak コピーを作成する。"""
    if not filepath.exists():
        return None
    bak = filepath.with_suffix(filepath.suffix + ".bak")
    shutil.copy2(filepath, bak)
    return bak
