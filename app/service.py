"""查询与统计。"""
from __future__ import annotations

import sqlite3


def student_scores(conn: sqlite3.Connection, sid: str) -> dict | None:
    row = conn.execute("SELECT * FROM students WHERE sid=?", (sid,)).fetchone()
    if not row:
        return None
    rows = conn.execute(
        """SELECT c.name AS course, s.term, s.score, c.credit
           FROM scores s JOIN courses c ON c.cid = s.cid
           WHERE s.sid=? ORDER BY s.term, s.cid""",
        (sid,),
    ).fetchall()
    scores = [r["score"] for r in rows]
    rank = conn.execute(
        """SELECT COUNT(DISTINCT sid) + 1 FROM scores
           WHERE cid IN (SELECT cid FROM scores WHERE sid=?)
           GROUP BY sid HAVING AVG(score) > (SELECT AVG(score) FROM scores WHERE sid=?)""",
        (sid, sid),
    ).fetchall()
    return {
        "student": dict(row),
        "records": [dict(r) for r in rows],
        "average": round(sum(scores) / len(scores), 2) if scores else None,
        "count": len(scores),
        "rank_estimate": len(rank) + 1,
    }


def course_stats(conn: sqlite3.Connection, cid: str) -> dict | None:
    row = conn.execute("SELECT * FROM courses WHERE cid=?", (cid,)).fetchone()
    if not row:
        return None
    r = conn.execute(
        """SELECT COUNT(*) n, AVG(score) avg, MAX(score) max, MIN(score) min,
                  SUM(CASE WHEN score>=60 THEN 1 ELSE 0 END) passed
           FROM scores WHERE cid=?""",
        (cid,),
    ).fetchone()
    dist = conn.execute(
        """SELECT CASE
             WHEN score<60 THEN '0-59'
             WHEN score<70 THEN '60-69'
             WHEN score<80 THEN '70-79'
             WHEN score<90 THEN '80-89'
             ELSE '90-100' END AS bucket,
           COUNT(*) n
           FROM scores WHERE cid=? GROUP BY bucket""",
        (cid,),
    ).fetchall()
    return {
        "course": dict(row),
        "count": r["n"],
        "average": round(r["avg"], 2) if r["avg"] is not None else None,
        "max": r["max"],
        "min": r["min"],
        "pass_rate": round(r["passed"] / r["n"], 4) if r["n"] else 0.0,
        "distribution": {d["bucket"]: d["n"] for d in dist},
    }


def overall_stats(conn: sqlite3.Connection) -> dict:
    s = conn.execute(
        """SELECT COUNT(DISTINCT sid) students, COUNT(DISTINCT cid) courses,
                  COUNT(*) records, AVG(score) avg,
                  SUM(CASE WHEN score>=60 THEN 1 ELSE 0 END) passed
           FROM scores"""
    ).fetchone()
    return {
        "students": s["students"],
        "courses": s["courses"],
        "records": s["records"],
        "average": round(s["avg"], 2) if s["avg"] is not None else None,
        "pass_rate": round(s["passed"] / s["records"], 4) if s["records"] else 0.0,
    }


def scores_by_term(conn: sqlite3.Connection, term: str) -> list[dict]:
    rows = conn.execute(
        """SELECT s.sid, st.name AS student, c.name AS course, s.score
           FROM scores s
           JOIN students st ON st.sid = s.sid
           JOIN courses c ON c.cid = s.cid
           WHERE s.term=? ORDER BY s.sid""",
        (term,),
    ).fetchall()
    return [dict(r) for r in rows]
