#!/usr/bin/env bash
set -euo pipefail
ECR_REPOSITORY="${ECR_REPOSITORY:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
AWS_REGION="${AWS_REGION:-us-east-1}"
CONTAINER_NAME="self-healing-demo"
if [ -z "$ECR_REPOSITORY" ]; then
  exit 2
fi
IMAGE="${ECR_REPOSITORY}:${IMAGE_TAG}"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REPOSITORY"
docker pull "$IMAGE"
if docker ps -q --filter "name=${CONTAINER_NAME}" | grep -q .; then
  docker stop "$CONTAINER_NAME" || true
  docker rm "$CONTAINER_NAME" || true
fi
docker run -d --name "$CONTAINER_NAME" \
  -p 5000:5000 \
  -e DEPLOYMENT_VERSION="${IMAGE_TAG}" \
  -e ENVIRONMENT="${ENVIRONMENT:-production}" \
  --restart unless-stopped \
  "$IMAGE"
sleep 2
docker ps -a
exit 0
