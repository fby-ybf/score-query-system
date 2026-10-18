"""命令行入口：导入 CSV。"""
from __future__ import annotations

import sys
from pathlib import Path

from .db import connect
from .importer import import_csv

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "scores.db"


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] != "import":
        print("用法：python -m app.cli import <csv路径>")
        return 1
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = connect(DB_PATH)
    result = import_csv(conn, sys.argv[2])
    print(f"成功入库 {result.inserted} 条，跳过 {result.skipped} 条")
    for err in result.errors:
        print(" -", err["reason"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
