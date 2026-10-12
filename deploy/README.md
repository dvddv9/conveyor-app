# Deployment

## Docker (recommended)

    cp .env.example .env
    # Edit .env: set DEEPSEEK_API_KEY
    docker compose up -d
    curl http://localhost:5001/health

With local LLM (Ollama):

    docker compose --profile local-llm up -d

## systemd (VPS)

    sudo mkdir -p /opt/conveyor_app
    sudo cp -r . /opt/conveyor_app/
    cd /opt/conveyor_app
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    cp .env.example .env
    sudo cp deploy/systemd/conveyor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now conveyor

## Env vars

| Var | Default | Required |
|-----|---------|----------|
| DEEPSEEK_API_KEY | - | Yes (cloud) |
| OLLAMA_URL | http://localhost:11434 | No |
| PORT | 5001 | No |
| CONVEYOR_API_KEY | "" | No (empty -> 127.0.0.1) |
| API_URL | http://localhost:5001 | No (UI) |
