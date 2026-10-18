# score-query-system

学生成绩查询系统的最小可运行复现：**CSV 批量导入（含校验）→ 成绩查询 → 统计看板**。

技术栈：Python / FastAPI / SQLite（标准库 sqlite3，零外部服务依赖）

> 原项目为 Java + SQL + HTML/CSS；本复现用 Python + SQLite 实现**同一套业务逻辑**，
> 便于在任何机器上一键运行。SQL 语句、表结构与校验规则保持一致思路。

## 功能

- 成绩 CSV 批量导入：字段校验（学号 10 位、课程号格式、分数 0-100、学期格式），
  错误行逐条报告，成功行入库并返回统计
- 查询：
  - `GET /students/{sid}` 学生全部成绩、均分、排名
  - `GET /courses/{cid}` 课程均分、最高/最低、及格率、分数段分布
  - `GET /scores?term=` 按学期筛选
- 统计看板：`GET /stats` 总人数、总课程数、整体均分与及格率、各分数段人数
- 前端单页：查询 + 看板

## 快速开始

```bash
pip install -r requirements.txt
python -m app.cli import data/sample_scores.csv   # 导入示例数据
uvicorn app.api:app --port 8002                    # http://localhost:8002/
```

Docker：`docker compose up -d --build`

## 目录

```
app/
  db.py       建表与连接（SQLite）
  importer.py CSV 解析 + 校验 + 批量插入
  service.py  查询与统计 SQL
  api.py      FastAPI 路由
  cli.py      命令行导入
  web/index.html
data/sample_scores.csv  示例成绩数据
tests/       导入校验 / 查询 / 统计 / API 测试
```

## 测试

```bash
python -m pytest -q
```
