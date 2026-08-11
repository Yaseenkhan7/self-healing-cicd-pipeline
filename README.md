# Self-Healing CI/CD Pipeline

This project implements a self healing cicd pipeline that combines Infrastructure as Code, CI/CD automation, containerization, and AI-assisted operations. Using Terraform, GitHub Actions, Docker, the pipeline provisions cloud infrastructure, deploys applications to EC2, performs automated testing and security scanning, verifies deployment health, and automatically recovers from failures through retry or rollback mechanisms powered by deployment log analysis using OpenAI API.

## Architecture

![Self-Healing CI/CD Pipeline Architecture](Architecture.png)

---

## Features

- **Infrastructure as Code** – Provisions AWS infrastructure using Terraform for consistent and repeatable deployments.
- **Automated CI/CD Pipeline** – Builds, tests, scans, and deploys the application automatically using GitHub Actions.
- **Containerized Deployment** – Packages the application with Docker for consistent execution across environments.
- **Security Scanning** – Performs automated vulnerability scanning using Trivy before deployment.
- **Automated Testing** – Runs unit tests with Pytest to validate application functionality before release.
- **Health Monitoring** – Verifies application availability through automated post-deployment health checks.
- **AI-Assisted Log Analysis** – Uses the OpenAI API to analyze deployment logs and identify the root cause of failures.
- **Self-Healing Recovery** – Automatically retries failed deployments or rolls back to the last stable version based on AI recommendations.
- **AWS EC2 Deployment** – Deploys containerized applications to Amazon EC2 using AWS Systems Manager (SSM).
- **Real-Time Notifications** – Sends deployment status and recovery updates to Slack for operational visibility.

---

## Project Structure

```
self-healing-cicd-pipeline/
├── .github/
│   └── workflows/
│       └── cicd.yml
├── terraform/
├── app/
│   ├── main.py
│   ├── templates/
│   └── requirements.txt
├── scripts/
│   ├── health_check.sh
│   ├── log_analyzer.py
│   └── rollback.sh
├── tests/
├── Dockerfile
├── requirements.txt
├── README.md
└── LICENSE
```

## CI/CD Pipeline

### Pipeline Stages

The pipeline defined in `.github/workflows/cicd.yml` runs on every push to `main` or `develop`:

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

1. **End of pipeline** (`notify` job) - reports success, self-healing recovery, or unrecoverable failure.
2. **During rollback** (`rollback.sh`) - sends an alert when rollback starts and when it completes.

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
