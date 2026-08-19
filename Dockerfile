# Multi-stage Dockerfile for the CV Matching service

# Stage 1: Base Python image
FROM python:3.13-slim AS base

WORKDIR /app

# Stage 2: Dependencies installation
FROM base AS dependencies

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

# Install Python dependencies using uv
RUN uv pip install --system .

# Stage 3: Application
FROM base AS application

# Copy installed dependencies from previous stage
COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY cv_matching/ ./cv_matching/
COPY main.py ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
