FROM python:3.13-slim AS runtime

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

# Install uv (pin version for reproducibility)
ARG UV_VERSION=0.8.17
ADD https://astral.sh/uv/${UV_VERSION}/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

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