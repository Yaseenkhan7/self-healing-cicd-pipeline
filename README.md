# Self-Healing CI/CD Pipeline

This project implements a self-healing CI/CD pipeline using GitHub Actions and AWS. After deployment, automated health checks verify the application. On failure, logs are analyzed using OpenAI, and the pipeline either retries deployment, performs a rollback, or sends a Slack alert based on the diagnosis.


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

![Self-Healing CI/CD Pipeline Architecture](Architecture.png)

---

## Features

- **Automated Health Checks** – Verifies application health after every deployment using the `/health` endpoint.
- **AI-Powered Log Analysis** – Uses OpenAI GPT to analyze deployment logs and identify the root cause of failures.
- **Automatic Rollback** – Restores the last stable deployment if the application fails health checks.
- **Smart Deployment Retry** – Retries deployments automatically when failures are identified as temporary.
- **Slack Notifications** – Sends real-time alerts for successful deployments, recovery actions, and failures.
- **Dockerized Application** – Runs the application in a secure Docker container with built-in health checks.
- **Prometheus Metrics** – Exposes a `/metrics` endpoint for monitoring with Prometheus and Grafana.
- **Automated Testing** – Runs unit tests with `pytest` and `pytest-cov` before deployment to ensure code quality.

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
