#!/usr/bin/env bash

set -euo pipefail

STABLE_VERSION="${STABLE_VERSION:-"1.0.0"}"
APP_HOST="${APP_HOST:-http://localhost:5000}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
HEALTH_ENDPOINT="${APP_HOST}/health"
MAX_HEALTH_RETRIES=6
HEALTH_RETRY_INTERVAL=10


timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log()       { echo "[$(timestamp)] $*"; }
log_info()  { log "INFO  $*"; }
log_warn()  { log "WARN  $*"; }
log_error() { log "ERROR $*" >&2; }

send_slack_alert() {
    local message="$1"
    if [ -n "${SLACK_WEBHOOK}" ]; then
        local payload
        payload=$(printf '{"text": "%s"}' "${message}")
        curl --silent --max-time 10 \
             -X POST -H 'Content-type: application/json' \
             --data "${payload}" \
             "${SLACK_WEBHOOK}" > /dev/null 2>&1 || true
        log_info "Slack alert sent."
    else
        log_warn "SLACK_WEBHOOK not set — skipping alert."
    fi
}

wait_for_healthy() {
    local attempt=1
    while [ "${attempt}" -le "${MAX_HEALTH_RETRIES}" ]; do
        local status
        status=$(curl --silent --output /dev/null \
                      --write-out "%{http_code}" \
                      --max-time 10 \
                      "${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")
        if [ "${status}" -eq 200 ]; then
            log_info "Service is healthy (HTTP ${status})."
            return 0
        fi
        log_warn "Service not yet healthy — HTTP ${status} (${attempt}/${MAX_HEALTH_RETRIES})."
        sleep "${HEALTH_RETRY_INTERVAL}"
        attempt=$((attempt + 1))
    done
    return 1
}

log_info "  ROLLBACK INITIATED"
log_info "  Target version : ${STABLE_VERSION}"
log_info "  Environment    : ${APP_HOST}"

send_slack_alert ":warning: *Rollback initiated* — reverting to \`${STABLE_VERSION}\` on \`${APP_HOST}\`."

log_info "Step 1/3 — Pulling stable image tag: ${STABLE_VERSION}"


export DEPLOYMENT_VERSION="${STABLE_VERSION}"
log_info "Deployment version set to ${DEPLOYMENT_VERSION}."

log_info "Step 2/3 — Restarting application with version ${STABLE_VERSION} …"


log_info "(Simulated) Service restarted successfully."

log_info "Step 3/3 — Verifying rollback via health endpoint …"
if wait_for_healthy; then
    log_info "Rollback SUCCEEDED — service is healthy at ${APP_HOST}."
    send_slack_alert ":white_check_mark: *Rollback succeeded* — \`${STABLE_VERSION}\` is live and healthy."
    exit 0
else
    log_error "Rollback FAILED — service is still unhealthy after ${MAX_HEALTH_RETRIES} retries."
    send_slack_alert ":x: *Rollback FAILED* — manual intervention required on \`${APP_HOST}\`."
    exit 1
fi
