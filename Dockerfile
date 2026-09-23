FROM python:3.11-slim

# Grab the uv binary (fast Python package manager) from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copy the application (backend + static frontend)
COPY app ./app

ENV PORT=8000
EXPOSE 8000

# Render (and most PaaS) inject $PORT at runtime; default to 8000 locally.
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
