# =============================================================================
# Dockerfile — self-healing-cicd-demo
# =============================================================================

FROM python:3.11-slim AS base

# Metadata
LABEL maintainer="Yaseenkhan7"
LABEL description="Self-Healing CI/CD Pipeline Demo Application"

# Build arguments (injected by the CI/CD workflow)
ARG DEPLOYMENT_VERSION=dev
ARG ENVIRONMENT=production

# Runtime environment variables
ENV DEPLOYMENT_VERSION=${DEPLOYMENT_VERSION} \
    ENVIRONMENT=${ENVIRONMENT} \
    PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies in a separate layer for better cache utilisation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE ${PORT}

# Run as non-root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

CMD ["python", "main.py"]
