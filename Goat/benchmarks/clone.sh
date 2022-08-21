#! /usr/bin/env bash

set -euo pipefail

ROOT=$(realpath "$(dirname "$0")/..")

EXT="$ROOT/external"
DOCKERIZED="dockerized"

if [[ ! -d "$EXT" ]]; then
	mkdir "$EXT"
fi

if [[ ! -f "$EXT/go.mod" ]]; then
	echo "module external" > "$EXT/go.mod"
fi

CWD="$PWD"
GFUZZ="$EXT/gfuzz"

rm -rf "$GFUZZ"
mkdir "$GFUZZ"

while IFS=, read -r NAME REPO COMMITHASH
do
	case $# in
		1) if [[ !($1 = $DOCKERIZED || $1 = $NAME) ]]; then
				continue
			fi;;
		2) if [[ ! $1 = $NAME ]]; then
				continue
			fi;;
	esac

	if [ $NAME = "kubernetes" ]; then
		function skip {
			echo ""
			echo "Running Docker version: skipping kubernetes"
			echo ""
		}

		case $# in
		1) if [ $1 = $DOCKERIZED ]; then
				skip
				continue
			fi;;
		2) if [ $2 = $DOCKERIZED ]; then
				skip
				continue
			fi;;
		esac
	fi

	echo "Cloning $NAME"

	REPOPATH="$GFUZZ/$NAME"
	mkdir "$REPOPATH" && cd "$REPOPATH"

	# https://stackoverflow.com/a/43136160/1098680
	if ! (git init && \
		git remote add origin "$REPO" && \
		git fetch --depth 1 origin "$COMMITHASH" && \
		git checkout FETCH_HEAD); then
		echo "Failed to clone $NAME"
		exit 1
	fi

	case "$NAME" in
		grpc)
			# Quick fix to let our tool detect unit tests, bypassing reflection
			shopt -s globstar
			sed -i 's/func (s) Test/func Test/g' **/*.go
			shopt -u globstar
			;;
		kubernetes)
			echo "Generating needed files for kubernetes"
			make generated_files
			# Remove hack/tools module which is not supposed to be buildable
			rm -r hack/tools
			echo "Fixing broken es-image module"
			cd "cluster/addons/fluentd-elasticsearch/es-image" && \
				env GOPATH="$GFUZZ" go mod tidy
			;;
	esac
done < "$ROOT/benchmarks/gfuzz.csv"

cd "$CWD"
