FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        'curl=8.14.1-*' \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY .env ./.env

RUN mkdir -p /app/models

EXPOSE 8011

CMD ["python", "-m", "app.main"]
HEALTHCHECK --interval=5s --timeout=10s --start-period=10s --retries=20 \
    CMD curl -f http://localhost:8011/health || exit 1
