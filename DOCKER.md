# Docker Usage

Run the full stack:

```bash
docker compose up --build
```

The frontend is available at:

```text
http://localhost:5173
```

The backend is available at:

```text
http://localhost:8000
```

The voice orchestrator expects the Ollama model to be present. Pull it once after the Ollama container starts:

```bash
docker compose exec ollama ollama pull qwen2.5:7b-instruct
```

Useful checks:

```bash
curl http://localhost:8000/health
curl http://localhost:5173/health
```

Data is stored in Docker volumes:

- `backend-data` for the SQLite database
- `ollama-data` for downloaded Ollama models

To stop the stack:

```bash
docker compose down
```
