# Self-Healing CI/CD Pipeline

A production-grade demonstration of automated failure detection, AI-driven root-cause analysis, and self-healing deployments — simulating real-world Site Reliability Engineering (SRE) practices with GitHub Actions.

[![CI/CD Pipeline](https://github.com/Yaseenkhan7/self-healing-cicd-pipeline/actions/workflows/cicd.yml/badge.svg)](https://github.com/Yaseenkhan7/self-healing-cicd-pipeline/actions/workflows/cicd.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: flake8](https://img.shields.io/badge/code%20style-flake8-black)](https://flake8.pycqa.org/)


---

## Overview

Modern microservices deployments fail in ways that are difficult to anticipate. This project implements a **self-healing CI/CD pipeline** that:

1. **Detects failures** automatically through configurable health-check polling after every deployment.
2. **Collects and analyses logs** from the failed run using an OpenAI-powered root-cause-analysis engine.
3. **Takes corrective action** — rolling back to a stable version or retrying the deployment — based on the AI's recommendation.
4. **Notifies stakeholders** in real time via Slack, so the team always knows what happened and why.

The whole lifecycle — from a code push to automated recovery — runs inside GitHub Actions with no external orchestration tools required.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GitHub Actions Runner                         │
│                                                                     │
│  Push / PR  ──►  ┌────────┐  ┌────────┐  ┌────────────────────┐   │
│                  │  Test  │─►│ Build  │─►│      Deploy        │   │
│                  └────────┘  └────────┘  └────────┬───────────┘   │
│                                                    │               │
│                                          ┌─────────▼─────────┐    │
│                                          │   Health  Gate     │    │
│                                          │  /health polling   │    │
│                                          └────┬──────────┬────┘    │
│                                         PASS  │          │ FAIL    │
│                                               │          │         │
│                                               ▼          ▼         │
│                                        ┌──────────┐ ┌──────────┐  │
│                                        │  Notify  │ │Self-Heal │  │
│                                        │ (Slack)  │ │          │  │
│                                        └──────────┘ └────┬─────┘  │
│                                                          │         │
│                                      ┌───────────────────┼──────┐ │
│                                      │  AI Log Analysis  │      │ │
│                                      │  (OpenAI GPT)     │      │ │
│                                      └───────┬───────────┘      │ │
│                                              │                   │ │
│                              ┌───────────────┼──────────────┐   │ │
│                              │               │              │   │ │
│                          rollback          retry       escalate │ │
│                              │               │              │   │ │
│                              ▼               ▼              ▼   │ │
│                        ┌──────────┐   ┌──────────┐  ┌─────────┐│ │
│                        │ Rollback │   │  Redeploy│  │  Slack  ││ │
│                        │ Script   │   │          │  │  Alert  ││ │
│                        └──────────┘   └──────────┘  └─────────┘│ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---|---|
| 🔍 **Health-Check Polling** | `scripts/health_check.sh` polls `/health` with configurable retries before declaring a deployment unhealthy |
| 🤖 **AI Root-Cause Analysis** | `scripts/log_analyzer.py` sends logs to OpenAI GPT and returns a structured JSON report with a recommended action |
| ♻️ **Automated Rollback** | `scripts/rollback.sh` reverts the service to the last known-good version and verifies recovery |
| 🔁 **Smart Retry** | The pipeline retries a deployment when the AI identifies a transient fault (e.g., a connection blip) |
| 📣 **Slack Alerts** | Real-time notifications for deployment success, self-healing activation, and unrecoverable failures |
| 🐳 **Docker-Ready** | A production-quality `Dockerfile` with a non-root user, build-arg injection, and a built-in `HEALTHCHECK` |
| 📊 **Metrics Endpoint** | A Prometheus-compatible `/metrics` endpoint for integration with Grafana / Alertmanager |
| ✅ **Full Test Suite** | 100% route coverage with `pytest` and `pytest-cov` |

---

## Project Structure

```
self-healing-cicd-pipeline/
├── .github/
│   └── workflows/
│       └── cicd.yml          # GitHub Actions pipeline definition
├── app/
│   ├── Dockerfile            # Production-ready container image
│   ├── main.py               # Flask web application
│   ├── requirements.txt      # Python dependencies
│   └── templates/
│       └── index.html        # Application front-end
├── scripts/
│   ├── health_check.sh       # Deployment health-gate script
│   ├── log_analyzer.py       # AI-driven root-cause analysis
│   └── rollback.sh           # Automated rollback & verification
├── tests/
│   └── test_app.py           # Application unit & route tests
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Docker (optional, for container builds)
- An OpenAI API key (optional; the analyser has an offline fallback)

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Yaseenkhan7/self-healing-cicd-pipeline.git
cd self-healing-cicd-pipeline

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r app/requirements.txt
```

### Running the Application

```bash
# Start the Flask development server
FLASK_ENV=development python app/main.py

# The app will be available at:
#   http://localhost:5000       – main page
#   http://localhost:5000/health   – health check
#   http://localhost:5000/metrics  – Prometheus metrics
#   http://localhost:5000/api/status – JSON status
```

Or with Docker:

```bash
docker build -t self-healing-demo ./app
docker run -p 5000:5000 \
  -e DEPLOYMENT_VERSION=1.0.0 \
  -e ENVIRONMENT=local \
  self-healing-demo
```

### Running Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

Expected output:

```
tests/test_app.py::TestIndexRoute::test_returns_200             PASSED
tests/test_app.py::TestHealthEndpoint::test_status_field_is_healthy PASSED
...
----------- coverage: 97% -----------
```

---

## CI/CD Pipeline

### Pipeline Stages

The pipeline defined in `.github/workflows/cicd.yml` runs on every push to `main` or `develop`:

```
push → test → build → deploy → health-gate → [self-heal] → notify
```

| Stage | Job | Description |
|---|---|---|
| 1 | `test` | `flake8` lint + `pytest` unit tests with coverage upload |
| 2 | `build` | Docker build via `docker/build-push-action` (image push optional) |
| 3 | `deploy` | Starts the application on the runner; collects initial deploy logs |
| 4 | `health-gate` | Runs `health_check.sh`; fails the workflow if the service is unhealthy |
| 5 | `self-heal` | Triggered **only** on health-gate failure — runs AI analysis and acts |
| 6 | `notify` | Sends a Slack message indicating success, self-healing, or unrecoverable failure |

### Self-Healing Flow

When `health-gate` fails, the `self-heal` job:

1. Downloads the deploy-log artifact produced by the `deploy` job.
2. Runs `scripts/log_analyzer.py` against the log.
3. Reads the `recommended_action` field from the JSON output:
   - **`rollback`** → runs `scripts/rollback.sh` to revert to `STABLE_VERSION`.
   - **`retry`** → re-launches the application and verifies health.
   - **`investigate` / `scale`** → logs the recommendation and sends a Slack escalation alert.

---

## Configuration

### GitHub Secrets

Configure the following secrets in **Settings → Secrets and variables → Actions**:

| Secret | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Recommended | OpenAI API key for AI log analysis. Falls back to heuristics if absent. |
| `SLACK_WEBHOOK` | Optional | Slack incoming-webhook URL for pipeline alerts. |
| `DOCKER_USERNAME` | Optional | Docker Hub username for image push. |
| `DOCKER_PASSWORD` | Optional | Docker Hub password / token for image push. |

### Environment Variables

Variables can also be set as repository **variables** (non-secret):

| Variable | Default | Description |
|---|---|---|
| `STABLE_VERSION` | `1.0.0` | The version tag to roll back to during a self-heal. |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model used by the log analyser. |
| `MAX_LOG_CHARS` | `8000` | Maximum log characters sent to the OpenAI API. |

---

## Scripts Reference

### `scripts/health_check.sh`

```bash
./scripts/health_check.sh [HOST] [MAX_RETRIES] [RETRY_INTERVAL]

# Example: poll staging with 10 retries every 15 seconds
./scripts/health_check.sh https://staging.example.com 10 15
```

Exits `0` when the service returns HTTP 200; exits `1` after exhausting all retries.

### `scripts/log_analyzer.py`

```bash
# Analyse a log file
python scripts/log_analyzer.py --log-file deploy.log --output report.json

# Pipe from stdin
cat /var/log/app.log | python scripts/log_analyzer.py

# Offline heuristic mode (no API key required)
python scripts/log_analyzer.py --log-file deploy.log --offline
```

The script exits `0` for `no_action`/`retry` recommendations and `2` for `rollback`/`investigate`/`scale`.

### `scripts/rollback.sh`

```bash
STABLE_VERSION=1.2.3 APP_HOST=https://api.example.com ./scripts/rollback.sh
```

Exits `0` on successful rollback with a confirmed healthy service; exits `1` if rollback fails.

---

## AI Log Analysis

`scripts/log_analyzer.py` uses the OpenAI Chat Completions API with a carefully crafted system prompt to act as a senior SRE. It returns a structured JSON report:

```json
{
  "generated_at": "2024-11-15T10:32:00+00:00",
  "log_source": "deploy.log",
  "analysis": {
    "root_cause": "Container terminated due to OOM — RSS exceeded 512 MB limit.",
    "severity": "critical",
    "recommended_action": "rollback",
    "explanation": "The new build introduced a memory regression...",
    "remediation_steps": [
      "Roll back to the previous stable version immediately.",
      "Profile heap usage of the new build.",
      "..."
    ]
  }
}
```

When `OPENAI_API_KEY` is not set (or the API is unreachable), the script automatically falls back to a **pattern-matching heuristic engine** that covers the most common failure categories: OOM kills, connection-refused errors, and non-zero exit codes.

---

## Alerting

Slack notifications are sent at two points in the pipeline:

1. **End of pipeline** (`notify` job) — reports success, self-healing recovery, or unrecoverable failure.
2. **During rollback** (`rollback.sh`) — sends an alert when rollback starts and when it completes.

To enable Slack alerts, add your incoming-webhook URL as the `SLACK_WEBHOOK` secret. You can create a webhook at [api.slack.com/messaging/webhooks](https://api.slack.com/messaging/webhooks).

---

## Contributing

Pull requests are welcome! For significant changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a Pull Request

Please make sure tests pass before submitting (`pytest tests/ -v`).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
