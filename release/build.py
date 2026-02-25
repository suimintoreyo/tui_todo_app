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
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = PROJECT_ROOT / "release"
DIST_DIR = RELEASE_DIR / "dist"
LOG_DIR = PROJECT_ROOT / "log"
APP_NAME = "schedule-tui"


# ---------------------------------------------------------------------------
# ログ用ユーティリティ
# ---------------------------------------------------------------------------

class TeeWriter:
    """ターミナルとログファイルに同時書き込みするヘルパー。"""

    def __init__(self, log_file):
        self._file = log_file

    def print(self, *args, **kwargs):
        """print() と同じインターフェースで、ターミナル＋ファイルに出力する。"""
        kwargs["flush"] = True
        print(*args, **kwargs)
        kwargs["file"] = self._file
        print(*args, **kwargs)

    def write_line(self, line: str):
        """1 行をターミナルとファイルに書き出す（末尾改行なし前提）。"""
        sys.stdout.write(line)
        sys.stdout.flush()
        self._file.write(line)
        self._file.flush()


def _read_proc_file(path: str) -> str | None:
    """Linux の /proc ファイルを安全に読む。"""
    try:
        return Path(path).read_text()
    except OSError:
        return None


def _get_cpu_info() -> str:
    """CPU モデル名とコア数を返す。"""
    cores = os.cpu_count() or "unknown"
    info = _read_proc_file("/proc/cpuinfo")
    if info:
        for line in info.splitlines():
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                return f"{model} ({cores} cores)"
    return f"{platform.processor() or platform.machine()} ({cores} cores)"


def _get_memory_info() -> str:
    """総メモリ量を返す。"""
    # Linux: /proc/meminfo
    info = _read_proc_file("/proc/meminfo")
    if info:
        for line in info.splitlines():
            if line.startswith("MemTotal"):
                kb = int(line.split()[1])
                mb = kb // 1024
                return f"{mb} MB ({mb / 1024:.1f} GB)"
    # Windows: kernel32.GlobalMemoryStatusEx
    if platform.system() == "Windows":
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            mb = stat.ullTotalPhys // (1024 * 1024)
            return f"{mb} MB ({mb / 1024:.1f} GB)"
        except Exception:
            pass
    return "unknown"


def _get_disk_info() -> str:
    """プロジェクトルートのディスク使用状況を返す。"""
    try:
        usage = shutil.disk_usage(PROJECT_ROOT)
        total_gb = usage.total / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        return f"{total_gb:.1f} GB total / {free_gb:.1f} GB free"
    except OSError:
        return "unknown"


def get_system_info(nuitka_version: str | None = None) -> str:
    """ハードウェア構成情報とシステムバージョン情報を文字列で返す。"""
    lines: list[str] = []

    lines.append("--- Hardware Configuration ---")
    lines.append(f"OS      : {platform.system()} {platform.release()}")
    lines.append(f"OS ver  : {platform.version()}")
    lines.append(f"Arch    : {platform.machine()}")
    lines.append(f"CPU     : {_get_cpu_info()}")
    lines.append(f"Memory  : {_get_memory_info()}")
    lines.append(f"Disk    : {_get_disk_info()}")
    lines.append("")
    lines.append("--- System Versions ---")
    lines.append(f"Python  : {sys.version}")
    if nuitka_version:
        lines.append(f"Nuitka  : {nuitka_version}")
    else:
        lines.append("Nuitka  : (not detected)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ビルド処理
# ---------------------------------------------------------------------------

def check_nuitka() -> str | None:
    """Nuitka がインストールされているか確認し、バージョン文字列を返す。

    1. ``nuitka --version`` を試す（stdin 無効・自動ダウンロード許可・10 秒制限）。
    2. 失敗した場合 ``pip show nuitka`` にフォールバック。
    """
    print("[INFO] Nuitka のバージョンを確認中...", flush=True)

    # --- Tier 1: nuitka --version ---
    version = _check_nuitka_version()
    if version is not None:
        return version

    # --- Tier 2: pip show nuitka (フォールバック) ---
    print(
        "[WARN] nuitka --version が応答しません。pip show で確認します...",
        flush=True,
    )
    return _check_nuitka_pip()


def _check_nuitka_version() -> str | None:
    """``python -m nuitka --version`` でバージョンを取得する。"""
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "nuitka",
                "--assume-yes-for-downloads",
                "--version",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0]
    except subprocess.TimeoutExpired:
        print(
            "[WARN] nuitka --version がタイムアウトしました（10秒）。",
            flush=True,
        )
    except FileNotFoundError:
        pass
    except OSError:
        pass
    return None


def _check_nuitka_pip() -> str | None:
    """``pip show nuitka`` でインストール有無とバージョンを取得する。"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "nuitka"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    return f"{version} (pip)"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def clean(tee: TeeWriter | None = None) -> None:
    """以前のビルド成果物を削除する。"""
    out = tee.print if tee else print
    for pattern in ["dist", "*.build"]:
        for p in RELEASE_DIR.glob(pattern):
            if p.is_dir():
                shutil.rmtree(p)
                out(f"[CLEAN] {p}")
            else:
                p.unlink()
                out(f"[CLEAN] {p}")


def build(*, onefile: bool = False, do_clean: bool = False) -> None:
    """Nuitka でビルドを実行し、ログを保存する。"""
    print("[INFO] ビルドスクリプトを開始します...", flush=True)

    # --- Nuitka チェック ---
    nuitka_version = check_nuitka()
    if nuitka_version is None:
        print("[ERROR] Nuitka が見つからないか、応答がありません。", flush=True)
        print("  以下を確認してください:", flush=True)
        print("  1. Nuitka がインストールされているか:", flush=True)
        print("     pip install -r release/requirements-build.txt", flush=True)
        print("  2. 'python -m nuitka --version' が正常に動作するか", flush=True)
        print("  3. C コンパイラ (MinGW64 等) がダウンロード可能か", flush=True)
        print("  4. ネットワーク/プロキシ環境に問題がないか", flush=True)
        sys.exit(1)
    print(f"[INFO] Nuitka: {nuitka_version}", flush=True)

    # --- ログ準備 ---
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"build_{timestamp}.log"
    log_path = LOG_DIR / log_filename

    mode_label = "onefile" if onefile else "standalone"

    with open(log_path, "w", encoding="utf-8") as log_file:
        tee = TeeWriter(log_file)

        # --- ヘッダー ---
        tee.print("=" * 60)
        tee.print(f" Build Log — {APP_NAME}")
        tee.print(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        tee.print(f" Mode: {mode_label}")
        tee.print("=" * 60)
        tee.print()
        tee.print(get_system_info(nuitka_version))
        tee.print()

        # --- Clean（オプション） ---
        if do_clean:
            tee.print("-" * 60)
            tee.print(" Clean")
            tee.print("-" * 60)
            clean(tee)
            tee.print()

        # --- ビルド ---
        main_script = PROJECT_ROOT / "main.py"
        data_dir = PROJECT_ROOT / "data"

        DIST_DIR.mkdir(parents=True, exist_ok=True)

        mode = "--onefile" if onefile else "--standalone"

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

        tee.print("=" * 60)
        tee.print(" Build Start")
        tee.print("=" * 60)
        tee.print(f"[BUILD] モード: {mode_label}")
        tee.print(f"[BUILD] 出力先: {DIST_DIR}")
        tee.print(f"[BUILD] コマンド:")
        tee.print(f"  {' '.join(cmd)}")
        tee.print()

        # --- Nuitka 実行（tee 方式でストリーム出力） ---
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=PROJECT_ROOT,
            env=env,
        )
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                tee.write_line(line)
        exit_code = process.wait()

        tee.print()

        if exit_code != 0:
            tee.print("=" * 60)
            tee.print(f" Build FAILED — exit code: {exit_code}")
            tee.print("=" * 60)
            tee.print(f"\n[LOG] ログファイル: {log_path}")
            sys.exit(exit_code)

        # --- ポストビルド ---
        if not onefile:
            standalone_dir = DIST_DIR / "main.dist"
            if standalone_dir.exists():
                data_dest = standalone_dir / "data"
                if not data_dest.exists():
                    shutil.copytree(data_dir, data_dest)
                    tee.print(f"[POST] data/ を {data_dest} にコピーしました")
                # 実行権限を付与
                exe = standalone_dir / "main"
                if exe.exists() and sys.platform != "win32":
                    exe.chmod(0o755)

        tee.print()
        tee.print("=" * 60)
        tee.print(f" ビルド完了! (exit code: {exit_code})")
        tee.print("=" * 60)
        if onefile:
            tee.print(f"  実行ファイル: {DIST_DIR / 'main.bin'}")
            tee.print()
            tee.print("  [注意] onefile モードでは data/ がバイナリに内包されます。")
            tee.print("  スケジュールの永続化には実行ファイルと同階層に")
            tee.print("  data/ ディレクトリを配置してください。")
        else:
            tee.print(f"  配布ディレクトリ: {DIST_DIR / 'main.dist'}")
            tee.print(f"  実行: {DIST_DIR / 'main.dist' / 'main'}")

        tee.print()
        tee.print(f"[LOG] ログファイル: {log_path}")


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

    build(onefile=args.onefile, do_clean=args.clean)


if __name__ == "__main__":
    main()
