# Use official uv image to copy the binary
FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.12-slim

# Copy the uv binary from the official image
COPY --from=uv_bin /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    RELOAD=false

WORKDIR /app

# Copy dependency files first for better layer caching
COPY uv.lock pyproject.toml ./

# Install dependencies without cache mount for better compatibility on Railway
RUN uv sync --frozen --no-install-project

# Copy the rest of the application
COPY . .

# Final sync to install the project itself
RUN uv sync --frozen

# Use the virtual environment by default
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Make startup script executable
RUN chmod +x scripts/start.sh

# Production command using the startup script
CMD ["./scripts/start.sh"]