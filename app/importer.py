"""CSV 批量导入与校验。

CSV 表头：sid,name,class_name,cid,course_name,credit,term,score
校验规则不满足的行记为错误并跳过，不影响其他行入库。
"""
from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass, field

REQUIRED_COLUMNS = ["sid", "name", "class_name", "cid", "course_name", "credit", "term", "score"]


@dataclass
class ImportResult:
    inserted: int = 0
    skipped: int = 0
    errors: list[dict] = field(default_factory=list)


def _validate(row: dict, line_no: int) -> str | None:
    sid = (row.get("sid") or "").strip()
    if not (len(sid) == 10 and sid.isdigit()):
        return f"第 {line_no} 行：学号必须是 10 位数字（当前：{sid!r}）"
    for col in ("name", "class_name", "cid", "course_name", "term"):
        if not (row.get(col) or "").strip():
            return f"第 {line_no} 行：字段 {col} 不能为空"
    try:
        credit = float(row["credit"])
        if not (0 < credit <= 10):
            return f"第 {line_no} 行：学分必须在 0-10 之间（当前：{row['credit']}）"
    except ValueError:
        return f"第 {line_no} 行：学分不是数字（当前：{row['credit']!r}）"
    try:
        score = float(row["score"])
        if not (0 <= score <= 100):
            return f"第 {line_no} 行：分数必须在 0-100 之间（当前：{row['score']}）"
    except ValueError:
        return f"第 {line_no} 行：分数不是数字（当前：{row['score']!r}）"
    term = row["term"].strip()
    if not (len(term) == 5 and term[:4].isdigit() and term[4] in "123"):
        return f"第 {line_no} 行：学期格式应为 20241 / 20242 / 20243（当前：{term!r}）"
    return None


def import_csv(conn: sqlite3.Connection, csv_path: str) -> ImportResult:
    result = ImportResult()
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV 缺少必需列：{missing}")
        for line_no, row in enumerate(reader, start=2):
            error = _validate(row, line_no)
            if error:
                result.errors.append({"line": line_no, "reason": error})
                result.skipped += 1
                continue
            try:
                with conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO students(sid, name, class_name) VALUES (?,?,?)",
                        (row["sid"].strip(), row["name"].strip(), row["class_name"].strip()),
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO courses(cid, name, credit) VALUES (?,?,?)",
                        (row["cid"].strip(), row["course_name"].strip(), float(row["credit"])),
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO scores(sid, cid, term, score) VALUES (?,?,?,?)",
                        (row["sid"].strip(), row["cid"].strip(), row["term"].strip(), float(row["score"])),
                    )
                result.inserted += 1
            except sqlite3.Error as exc:
                result.errors.append({"line": line_no, "reason": f"数据库错误：{exc}"})
                result.skipped += 1
    return result
