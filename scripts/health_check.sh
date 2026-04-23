#!/usr/bin/env bash
# =============================================================================
# health_check.sh — Deployment health-check script
#
# Polls the application's /health endpoint at configurable intervals.
# Exits 0 on success, 1 if the service does not become healthy within the
# maximum number of allowed attempts.
#
# Usage:
#   ./scripts/health_check.sh [HOST] [MAX_RETRIES] [RETRY_INTERVAL]
#
# Defaults:
#   HOST            http://localhost:5000
#   MAX_RETRIES     10
#   RETRY_INTERVAL  15  (seconds)
# =============================================================================

set -euo pipefail

# --------------------------------------------------------------------------- #
#  Configuration                                                               #
# --------------------------------------------------------------------------- #
HOST="${1:-${APP_HOST:-http://localhost:5000}}"
MAX_RETRIES="${2:-${HEALTH_MAX_RETRIES:-10}}"
RETRY_INTERVAL="${3:-${HEALTH_RETRY_INTERVAL:-15}}"
HEALTH_ENDPOINT="${HOST}/health"

# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #
timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log()       { echo "[$(timestamp)] $*"; }
log_info()  { log "INFO  $*"; }
log_warn()  { log "WARN  $*"; }
log_error() { log "ERROR $*" >&2; }

# --------------------------------------------------------------------------- #
#  Main health-check loop                                                      #
# --------------------------------------------------------------------------- #
log_info "Starting health check — target: ${HEALTH_ENDPOINT}"
log_info "Max retries: ${MAX_RETRIES}, interval: ${RETRY_INTERVAL}s"

attempt=1
while [ "${attempt}" -le "${MAX_RETRIES}" ]; do
    log_info "Attempt ${attempt}/${MAX_RETRIES} …"

    HTTP_STATUS=$(
        curl --silent \
             --output /dev/null \
             --write-out "%{http_code}" \
             --max-time 10 \
             --connect-timeout 5 \
             "${HEALTH_ENDPOINT}" 2>/dev/null || echo "000"
    )

    if [ "${HTTP_STATUS}" -eq 200 ]; then
        log_info "Health check PASSED (HTTP ${HTTP_STATUS}) after ${attempt} attempt(s)."
        exit 0
    fi

    log_warn "Health check FAILED — HTTP ${HTTP_STATUS} (attempt ${attempt}/${MAX_RETRIES})."

    if [ "${attempt}" -lt "${MAX_RETRIES}" ]; then
        log_info "Waiting ${RETRY_INTERVAL}s before next attempt …"
        sleep "${RETRY_INTERVAL}"
    fi

    attempt=$((attempt + 1))
done

log_error "Service at ${HEALTH_ENDPOINT} did not become healthy after ${MAX_RETRIES} attempt(s)."
log_error "Triggering self-healing workflow …"
exit 1
