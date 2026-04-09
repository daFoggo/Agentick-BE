# Use official uv image to copy the binary
FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.12-slim

# Copy the uv binary from the official image
COPY --from=uv_bin /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (better caching)
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy the rest of the application
COPY . .

# Final sync to install the project itself
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    uv sync --frozen

# Use the virtual environment by default
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]