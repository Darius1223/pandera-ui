# Installation

## Requirements

- Python **3.10+**
- Pandera **0.19+**

## pip

```bash
pip install pandera-ui
```

## uv

```bash
uv add pandera-ui
```

## Extras

### Rich terminal output

Enables a progress spinner and formatted summary table in the CLI:

```bash
pip install pandera-ui[rich]
# or
uv add pandera-ui[rich]
```

### Watch mode

Enables `--watch` / `-w` flag for live reload on `.py` file changes:

```bash
pip install pandera-ui[watch]
# or
uv add pandera-ui[watch]
```

### All extras

```bash
pip install pandera-ui[rich,watch]
```

## Docker

```bash
docker run --rm \
  -v /path/to/myproject:/project:ro \
  -p 8765:8765 \
  ghcr.io/darius-krsk/pandera-ui:latest
```

Or with Docker Compose — create a `docker-compose.yml`:

```yaml
services:
  pandera-ui:
    image: ghcr.io/darius-krsk/pandera-ui:latest
    volumes:
      - /path/to/myproject:/project:ro
    ports:
      - "8765:8765"
```

Then:

```bash
docker compose up
```
