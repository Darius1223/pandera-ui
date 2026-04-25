FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY pandera_ui/ ./pandera_ui/
COPY frontend/ ./frontend/

EXPOSE 8765

CMD ["uv", "run", "pandera-ui", "/project", "--host", "0.0.0.0", "--port", "8765"]
