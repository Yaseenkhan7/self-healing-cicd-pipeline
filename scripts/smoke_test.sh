#!/usr/bin/env bash
set -euo pipefail
ALB_DNS="${ALB_DNS:-}"
if [ -z "$ALB_DNS" ]; then
  exit 2
fi
URL="http://$ALB_DNS/health"
ATTEMPTS=0
until [ $ATTEMPTS -ge 10 ]
do
  STATUS=$(curl --write-out "%{http_code}" --silent --output /dev/null "$URL" || echo "000")
  if [ "$STATUS" = "200" ]; then
    exit 0
  fi
  ATTEMPTS=$((ATTEMPTS+1))
  sleep 6
done
exit 1
