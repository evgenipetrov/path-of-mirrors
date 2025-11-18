# Backend Dockerfile for Path of Mirrors
FROM python:3.12-slim AS base

# Arguments for user/group IDs
ARG USER_ID=1000
ARG GROUP_ID=1000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with matching UID/GID
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -m -u ${USER_ID} -g appuser appuser && \
    chown -R appuser:appuser /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./
RUN chown appuser:appuser pyproject.toml uv.lock README.md

# Development stage (with test dependencies)
FROM base AS development

# Install all dependencies including dev
USER appuser
RUN uv sync --frozen

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser tests/ ./tests/

# Add src to PYTHONPATH so imports work correctly
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage (without dev dependencies)
FROM base AS production

# Install only production dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# Add src to PYTHONPATH so imports work correctly
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
