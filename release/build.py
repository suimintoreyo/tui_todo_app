#!/usr/bin/env python3
"""Nuitka ビルドスクリプト — JSON スケジュール管理 TUI。

使い方:
    python release/build.py [--onefile] [--clean]

オプション:
    --onefile   1ファイル実行形式でビルド（デフォルト: standalone）
    --clean     ビルド前に以前の成果物を削除
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = PROJECT_ROOT / "release"
DIST_DIR = RELEASE_DIR / "dist"
APP_NAME = "schedule-tui"


def check_nuitka() -> bool:
    """Nuitka がインストールされているか確認する。"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            version = result.stdout.strip().splitlines()[0]
            print(f"[INFO] Nuitka: {version}")
            return True
    except FileNotFoundError:
        pass
    print("[ERROR] Nuitka がインストールされていません。")
    print("  pip install -r release/requirements-build.txt")
    return False


def clean() -> None:
    """以前のビルド成果物を削除する。"""
    for pattern in ["dist", "*.build"]:
        for p in RELEASE_DIR.glob(pattern):
            if p.is_dir():
                shutil.rmtree(p)
                print(f"[CLEAN] {p}")
            else:
                p.unlink()
                print(f"[CLEAN] {p}")


def build(*, onefile: bool = False) -> None:
    """Nuitka でビルドを実行する。"""
    if not check_nuitka():
        sys.exit(1)

    main_script = PROJECT_ROOT / "main.py"
    data_dir = PROJECT_ROOT / "data"

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    mode = "--onefile" if onefile else "--standalone"
    mode_label = "onefile" if onefile else "standalone"

    cmd: list[str] = [
        sys.executable,
        "-m",
        "nuitka",
        mode,
        f"--output-dir={DIST_DIR}",
        # ---- インポート制御 ----
        "--follow-imports",
        # プロジェクト内パッケージ
        "--include-package=db",
        "--include-package=models",
        "--include-package=ui",
        "--include-package=utils",
        # Textual と依存パッケージ
        "--include-package=textual",
        "--include-package-data=textual",
        # ---- データファイル同梱 ----
        f"--include-data-dir={data_dir}=data",
        # ---- その他 ----
        "--assume-yes-for-downloads",
        str(main_script),
    ]

    print(f"[BUILD] モード: {mode_label}")
    print(f"[BUILD] 出力先: {DIST_DIR}")
    print(f"[BUILD] コマンド:")
    print(f"  {' '.join(cmd)}")
    print()

    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)

    # standalone モードの場合: data/ が dist 内に無ければコピー
    if not onefile:
        standalone_dir = DIST_DIR / "main.dist"
        if standalone_dir.exists():
            data_dest = standalone_dir / "data"
            if not data_dest.exists():
                shutil.copytree(data_dir, data_dest)
                print(f"[POST] data/ を {data_dest} にコピーしました")
            # 実行権限を付与
            exe = standalone_dir / "main"
            if exe.exists() and sys.platform != "win32":
                exe.chmod(0o755)

    print()
    print("=" * 50)
    print(" ビルド完了!")
    print("=" * 50)
    if onefile:
        print(f"  実行ファイル: {DIST_DIR / 'main.bin'}")
        print()
        print("  [注意] onefile モードでは data/ がバイナリに内包されます。")
        print("  スケジュールの永続化には実行ファイルと同階層に")
        print("  data/ ディレクトリを配置してください。")
    else:
        print(f"  配布ディレクトリ: {DIST_DIR / 'main.dist'}")
        print(f"  実行: {DIST_DIR / 'main.dist' / 'main'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="JSON スケジュール管理 TUI — Nuitka ビルドスクリプト"
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="1ファイル実行形式でビルド（デフォルト: standalone）",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="ビルド前に以前の成果物を削除",
    )
    args = parser.parse_args()

    if args.clean:
        clean()

    build(onefile=args.onefile)


if __name__ == "__main__":
    main()
