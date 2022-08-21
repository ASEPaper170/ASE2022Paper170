#! /usr/bin/env bash

set -euo pipefail

ROOT=$(realpath "$(dirname "$0")/..")
GFUZZ="$ROOT/external/gfuzz"

while IFS=, read -r NAME REPO COMMITHASH; do
	if [[ "$NAME" == "kubernetes" ]]; then
		# Temporarily filter out kubernetes packages because there are a ton
		# and we cannot run go list succesfully in some of the submodules.
		continue
	fi
	#echo "Checking ${NAME}:"

	if [ -d "$ROOT/external/gfuzz/$NAME" ]; then
		"$ROOT/benchmarks/list_packages_in_repo.sh" "$GFUZZ" "$NAME"
	fi
done < "$ROOT/benchmarks/gfuzz.csv"
