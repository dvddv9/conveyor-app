# syntax=docker/dockerfile:1

# ---------- builder ----------
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY vishap/ ./vishap/

RUN pip install --no-cache-dir --prefix=/install .

# ---------- runtime ----------
FROM python:3.12-slim

LABEL org.opencontainers.image.title="vishap-analyzer" \
      org.opencontainers.image.description="Vishap — multi-material IT analyst" \
      org.opencontainers.image.source="https://github.com/dvddv9/vishap" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 vishap

COPY --from=builder /install /usr/local

USER vishap
WORKDIR /home/vishap

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VISHAP_DATA_DIR=/home/vishap/.vishap/data

RUN mkdir -p /home/vishap/.vishap/data

EXPOSE 5001 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:5001/health || exit 1

CMD ["python", "-m", "src.main"]
