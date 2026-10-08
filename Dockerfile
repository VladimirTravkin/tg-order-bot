# syntax=docker/dockerfile:1.7

# ============================================================
# Stage 1: builder — install dependencies with uv
# ============================================================
FROM python:3.11-slim AS builder

# Install uv from the official image (small, no pip needed).
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# uv settings for reproducible, cache-friendly installs.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first (leverages Docker layer caching).
# Only pyproject.toml and uv.lock matter for the dependency layer.
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy the source and metadata needed to install the project itself.
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ============================================================
# Stage 2: runtime — slim image with only what's needed
# ============================================================
FROM python:3.11-slim AS runtime

# Create a non-root user (good security practice).
RUN groupadd --system --gid 1000 bot \
    && useradd --system --uid 1000 --gid bot --create-home bot

WORKDIR /app

# Copy the pre-built virtualenv and project from the builder.
COPY --from=builder --chown=bot:bot /app/.venv /app/.venv
COPY --from=builder --chown=bot:bot /app/src /app/src

# Put the venv's bin first so `python -m tg_order_bot` picks it up.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER bot

# Application entry point.
CMD ["python", "-m", "tg_order_bot"]
