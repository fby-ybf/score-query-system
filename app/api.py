"""FastAPI 路由。"""
from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from .db import connect
from .importer import import_csv
from .service import course_stats, overall_stats, scores_by_term, student_scores

BASE = Path(__file__).resolve().parents[1]
DB_PATH = BASE / "data" / "scores.db"
app = FastAPI(title="score-query-system", version="1.0.0")


def _conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    return connect(DB_PATH)


@app.get("/healthz")
def healthz() -> dict:
    conn = _conn()
    stats = overall_stats(conn)
    conn.close()
    return {"status": "ok", **stats}


@app.get("/students/{sid}")
def get_student(sid: str) -> dict:
    conn = _conn()
    data = student_scores(conn, sid)
    conn.close()
    if not data:
        raise HTTPException(status_code=404, detail="学号不存在")
    return data


@app.get("/courses/{cid}")
def get_course(cid: str) -> dict:
    conn = _conn()
    data = course_stats(conn, cid)
    conn.close()
    if not data:
        raise HTTPException(status_code=404, detail="课程号不存在")
    return data


@app.get("/scores")
def get_scores(term: str) -> list[dict]:
    conn = _conn()
    data = scores_by_term(conn, term)
    conn.close()
    return data


@app.get("/stats")
def stats() -> dict:
    conn = _conn()
    data = overall_stats(conn)
    conn.close()
    return data


@app.post("/import")
async def upload(file: UploadFile = File(...)) -> dict:
    content = (await file.read()).decode("utf-8-sig")
    tmp = BASE / "data" / "_upload.csv"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(content, encoding="utf-8")
    conn = _conn()
    try:
        result = import_csv(conn, str(tmp))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        conn.close()
        tmp.unlink(missing_ok=True)
    return {
        "inserted": result.inserted,
        "skipped": result.skipped,
        "errors": result.errors[:20],
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")
