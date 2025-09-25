FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT="/usr/local" \
    PATH="/usr/local/bin:$PATH"

# System deps (keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install uv (pin version for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy only dependency manifests first (maximize cache reuse)
COPY pyproject.toml uv.lock ./

RUN uv sync --locked

# Now copy the rest of the application source
COPY . .

# Ensure entrypoint is executable (if not already in repo with +x)
RUN chmod +x /app/entrypoint.sh