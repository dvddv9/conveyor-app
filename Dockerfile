FROM python:3.12-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY conveyor/ ./conveyor/
COPY pyproject.toml README.md ./
COPY .env.example .env
RUN mkdir -p /app/data
EXPOSE 5001 8501
CMD ["python", "-m", "src.main"]
