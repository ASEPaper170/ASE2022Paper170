#!/usr/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
NC='\033[0m'

echo "The following is a containerized full run of GOAT on all benchmarks."
echo -e "${YELLOW}Requirements${NC}: docker CLI"


echo "Benchmark run started."

ROOT=$(realpath "$(dirname "$0")")

DOCKER_BUILDKIT=1 docker build -t goat $ROOT --build-arg REPO="$REPO" --build-arg ACTION="./benchmarks/_full-benchmarks.sh"

docker run --rm -it goat