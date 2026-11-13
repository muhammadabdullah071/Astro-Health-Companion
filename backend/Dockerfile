# Build context is ./backend (see docker-compose.yml).
# The image holds only the backend code. contract/, data/sample/ and rag/ are mounted
# from the repo by docker-compose.yml, so the app finds them at /app/<folder>
# (config.py computes the repo root as /app because the code lives in /app/backend).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/status')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
