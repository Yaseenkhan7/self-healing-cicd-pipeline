FROM python:3.11-slim AS base

LABEL maintainer="Yaseenkhan7"
LABEL description="Self-Healing CI/CD Pipeline Demo Application"

ARG DEPLOYMENT_VERSION=dev
ARG ENVIRONMENT=production

ENV DEPLOYMENT_VERSION=${DEPLOYMENT_VERSION} \
    ENVIRONMENT=${ENVIRONMENT} \
    PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE ${PORT}

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

CMD ["python", "main.py"]
