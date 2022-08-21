#!/usr/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
NC='\033[0m'

echo "The following is a containerized interactive run of GOAT."
echo -e "${YELLOW}Requirements${NC}: docker CLI"
echo -e "${GREEN}Repositories${NC}: kubernetes, etcd, go-ethereum, grpc, prometheus, tidb"
echo ""

function print_mls {
  for l in $@; do
    echo $l
  done
}

REPOS=("etcd" "go-ethereum" "grpc" "prometheus" "tidb")

if [ ! -z $1 ]; then
  for repo in ${REPOS[@]}; do
    if [ $1 = $repo ]; then
      FOUND=true
    fi
  done
  if [ $FOUND ]; then
    echo "Building image and cloning chosen repository: $1"
    REPO=$1
  else 
    echo "Repository not found: $1. Must be one of:"
    print_mls ${REPOS[@]}
    exit 1
  fi

else
  echo "Building image and cloning all repositories"
  echo "To run interactive GOAT with a specific repository, provide it as an argument."
  echo ""
fi

ROOT=$(realpath "$(dirname "$0")")

DOCKER_BUILDKIT=1 docker build -t goat $ROOT --build-arg REPO="$REPO"

docker run --rm -it goat