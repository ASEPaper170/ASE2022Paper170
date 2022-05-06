#!/usr/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
NC='\033[0m'

echo -e "The following is a containerized run of GOAT to reproduce the ${GREEN}etcd${NC} bug in the paper."
echo -e "${YELLOW}Requirements${NC}: docker CLI"
echo ""

ROOT=$(realpath "$(dirname "$0")")

DOCKER_BUILDKIT=1 docker build -t goat $ROOT --build-arg REPO="etcd" --build-arg ACTION="./benchmarks/_etcd-bug-run.sh"

docker run --rm -it goat