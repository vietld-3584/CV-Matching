# Multi-stage Dockerfile for the CV Matching service

# Stage 1: Base Python image
FROM python:3.14-slim AS base

WORKDIR /app

# Dependencies live in a venv at a fixed path, which the final stage copies whole.
# The path carries no Python version, so bumping the base image needs no edit here -
# the previous layout hardcoded /usr/local/lib/python3.13/site-packages and broke
# silently on a minor version bump.
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Stage 2: Dependencies installation
FROM base AS dependencies

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

# Install Python dependencies using uv
RUN uv venv "$VIRTUAL_ENV" \
    && uv pip install --no-cache .

# Stage 3: Application
FROM base AS application

# Copy the prepared environment from the previous stage
COPY --from=dependencies /opt/venv /opt/venv

# Copy application code. WORKDIR is on sys.path, so `cv_matching` is imported
# from here rather than from site-packages.
COPY cv_matching/ ./cv_matching/
COPY main.py ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
