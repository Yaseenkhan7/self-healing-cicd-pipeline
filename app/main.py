"""
Self-Healing CI/CD Pipeline Demo Application
A simple Flask web application used to demonstrate the self-healing pipeline.
It exposes a health endpoint and simulates real application behavior.
"""

import os
import logging
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request

# --------------------------------------------------------------------------- #
#  Logging configuration                                                       #
# --------------------------------------------------------------------------- #
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Application factory                                                         #
# --------------------------------------------------------------------------- #
app = Flask(__name__)

# Track application start time for uptime calculation
APP_START_TIME = time.time()
DEPLOYMENT_VERSION = os.getenv("DEPLOYMENT_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


# --------------------------------------------------------------------------- #
#  Routes                                                                      #
# --------------------------------------------------------------------------- #

@app.route("/")
def index():
    """Render the main application page."""
    logger.info("Request received: GET /")
    return render_template(
        "index.html",
        version=DEPLOYMENT_VERSION,
        environment=ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


@app.route("/health")
def health():
    """
    Health-check endpoint consumed by the CI/CD self-healing scripts.

    Returns HTTP 200 when the application is ready to serve traffic,
    and HTTP 503 when it is in a degraded or unavailable state.
    """
    uptime_seconds = int(time.time() - APP_START_TIME)
    payload = {
        "status": "healthy",
        "version": DEPLOYMENT_VERSION,
        "environment": ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("Health check passed – uptime %ds", uptime_seconds)
    return jsonify(payload), 200


@app.route("/metrics")
def metrics():
    """Lightweight Prometheus-style metrics endpoint (plaintext)."""
    uptime = int(time.time() - APP_START_TIME)
    body = (
        f"# HELP app_uptime_seconds Total uptime of the application in seconds.\n"
        f"# TYPE app_uptime_seconds gauge\n"
        f'app_uptime_seconds{{version="{DEPLOYMENT_VERSION}",env="{ENVIRONMENT}"}} {uptime}\n'
        f"# HELP app_info Static information about the running application.\n"
        f"# TYPE app_info gauge\n"
        f'app_info{{version="{DEPLOYMENT_VERSION}",env="{ENVIRONMENT}"}} 1\n'
    )
    return body, 200, {"Content-Type": "text/plain; version=0.0.4"}


@app.route("/api/status")
def api_status():
    """JSON status endpoint for downstream service checks."""
    return jsonify(
        {
            "service": "self-healing-cicd-demo",
            "version": DEPLOYMENT_VERSION,
            "environment": ENVIRONMENT,
            "ready": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.errorhandler(404)
def not_found(_error):
    logger.warning("404 – path not found: %s", request.path)
    return jsonify({"error": "Not found", "path": request.path}), 404


@app.errorhandler(500)
def internal_error(_error):
    logger.error("500 – internal server error: %s", str(_error))
    return jsonify({"error": "Internal server error"}), 500


# --------------------------------------------------------------------------- #
#  Entry point                                                                 #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    logger.info(
        "Starting application v%s on port %d (env=%s, debug=%s)",
        DEPLOYMENT_VERSION, port, ENVIRONMENT, debug,
    )
    app.run(host="0.0.0.0", port=port, debug=debug)
