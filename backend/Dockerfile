FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# System deps (keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Copy only dependency manifests first (maximize cache reuse)
COPY pyproject.toml uv.lock ./

RUN uv sync --locked

# Now copy the rest of the application source
COPY . .

# Ensure entrypoint is executable (if not already in repo with +x)
RUN chmod +x /app/entrypoint.sh