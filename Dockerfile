FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=development \
    KNOWLEDGE_PATH=knowledge

WORKDIR /app

RUN addgroup --system advisory && adduser --system --ingroup advisory advisory

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY api ./api
COPY engine ./engine
COPY integrations ./integrations
COPY languages ./languages
COPY knowledge ./knowledge
RUN python -m pip install --no-cache-dir --no-deps .

USER advisory
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2)"

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
