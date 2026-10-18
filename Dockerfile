FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data

RUN useradd -r -u 10001 appuser && chown -R appuser /srv
USER appuser

EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8002/healthz',timeout=2)"

CMD ["sh", "-c", "python -m app.cli import data/sample_scores.csv && uvicorn app.api:app --host 0.0.0.0 --port 8002"]
