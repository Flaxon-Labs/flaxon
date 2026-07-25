
---

## docs/deployment.md

```markdown
# Deployment

## Overview

Flaxon applications can be deployed in various ways, from simple single-process servers to multi-worker production deployments.

## Running in Production

```bash
# Single worker
flaxon run app:app --host 0.0.0.0 --port 8000

# Multiple workers
flaxon run app:app --host 0.0.0.0 --port 8000 --workers 4

# Using Python
from flaxon import Flaxon

app = Flaxon("my-app")
app.run(host="0.0.0.0", port=8000, workers=4)

Environment Variables
bash
# Required for production
export FLAXON_ENV=production
export FLAXON_DEBUG=false
export FLAXON_SECRET_KEY=your-secret-key
export FLAXON_ALLOWED_HOSTS=api.example.com,example.com
Docker Deployment
Dockerfile
dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install flaxon[standard]

COPY . .

CMD ["flaxon", "run", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
Build and Run
bash
docker build -t my-app .
docker run -p 8000:8000 -e FLAXON_ENV=production -e FLAXON_SECRET_KEY=your-secret my-app
Docker Compose
yaml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLAXON_ENV=production
      - FLAXON_DEBUG=false
      - FLAXON_SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=flaxon
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=flaxon

  redis:
    image: redis:7-alpine
Reverse Proxy (Nginx)
nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
Health Checks
python
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    # Check database, cache, etc.
    return {"status": "ready"}
Production Checklist
□ Set FLAXON_ENV=production
□ Set FLAXON_DEBUG=false
□ Set FLAXON_SECRET_KEY (32+ random bytes)
□ Set FLAXON_ALLOWED_HOSTS to your domains
□ Use HTTPS (terminate at reverse proxy)
□ Use multiple workers (--workers 4)
□ Monitor health endpoints
□ Set up logging
□ Use a database connection pool
□ Use Redis for rate limiting and caching
□ Use a reverse proxy for TLS termination