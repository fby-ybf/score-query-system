"""导入校验 / 查询 / 统计 / API 测试。"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.db import connect
from app.importer import import_csv
from app.service import course_stats, overall_stats, scores_by_term, student_scores

VALID_CSV = """sid,name,class_name,cid,course_name,credit,term,score
2023100101,测试甲,智能23-1,CS101,数据结构,4,20241,92
2023100102,测试乙,智能23-1,CS101,数据结构,4,20241,58
2023100102,测试乙,智能23-1,CS102,Python,3,20242,77
"""

INVALID_CSV = """sid,name,class_name,cid,course_name,credit,term,score
2023100101,测试甲,智能23-1,CS101,数据结构,4,20241,92
202310010,学号位数不够,智能23-1,CS101,数据结构,4,20241,80
2023100103,分数越界,智能23-1,CS101,数据结构,4,20241,120
2023100104,学分非数字,智能23-1,CS101,数据结构,abc,20241,80
2023100105,学期格式错,智能23-1,CS101,数据结构,4,2024-1,80
"""


@pytest.fixture()
def conn():
    c = connect(":memory:")
    yield c
    c.close()


@pytest.fixture()
def loaded(conn, tmp_path):
    p = tmp_path / "scores.csv"
    p.write_text(VALID_CSV, encoding="utf-8")
    return conn, import_csv(conn, str(p))


def test_import_valid_rows(loaded):
    _, result = loaded
    assert result.inserted == 3
    assert result.skipped == 0
    assert result.errors == []


def test_import_reports_invalid_rows(conn, tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text(INVALID_CSV, encoding="utf-8")
    result = import_csv(conn, str(p))
    assert result.inserted == 1
    assert result.skipped == 4
    reasons = " ".join(e["reason"] for e in result.errors)
    assert "学号" in reasons and "分数" in reasons and "学分" in reasons and "学期" in reasons


def test_import_missing_column_raises(conn, tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("sid,name\n2023100101,甲\n", encoding="utf-8")
    with pytest.raises(ValueError):
        import_csv(conn, str(p))


def test_student_query(loaded):
    conn, _ = loaded
    data = student_scores(conn, "2023100102")
    assert data["student"]["name"] == "测试乙"
    assert data["count"] == 2
    assert data["average"] == pytest.approx(67.5)
    assert data["records"][0]["course"] == "数据结构"


def test_student_not_found(loaded):
    conn, _ = loaded
    assert student_scores(conn, "9999999999") is None


def test_course_stats(loaded):
    conn, _ = loaded
    data = course_stats(conn, "CS101")
    assert data["count"] == 2
    assert data["average"] == pytest.approx(75.0)
    assert data["pass_rate"] == 0.5
    assert data["distribution"]["90-100"] == 1


def test_overall_stats(loaded):
    conn, _ = loaded
    stats = overall_stats(conn)
    assert stats["students"] == 2
    assert stats["courses"] == 2
    assert stats["records"] == 3


def test_scores_by_term(loaded):
    conn, _ = loaded
    assert len(scores_by_term(conn, "20241")) == 2
    assert len(scores_by_term(conn, "20242")) == 1


def test_api_end_to_end(tmp_path, monkeypatch):
    from app import api

    db = tmp_path / "test.db"
    monkeypatch.setattr(api, "DB_PATH", db)
    p = tmp_path / "scores.csv"
    p.write_text(VALID_CSV, encoding="utf-8")

    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"

    content = p.read_bytes()
    r = client.post("/import", files={"file": ("scores.csv", content, "text/csv")})
    assert r.status_code == 200
    assert r.json()["inserted"] == 3

    r = client.get("/students/2023100101")
    assert r.status_code == 200
    assert r.json()["average"] == 92

    r = client.get("/courses/CS101")
    assert r.json()["pass_rate"] == 0.5

    assert client.get("/students/9999999999").status_code == 404
    assert client.get("/stats").json()["records"] == 3
