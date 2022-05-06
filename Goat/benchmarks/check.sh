#! /usr/bin/env bash

set -euo pipefail

ROOT=$(realpath "$(dirname "$0")/..")
GFUZZ="$ROOT/external/gfuzz"

TO_CHECK=$("$ROOT/benchmarks/list_packages.sh")

while IFS=, read -r MODULEPATH PACKAGE
do
	echo "Checking $MODULEPATH $PACKAGE"

	go run Goat -gopath "$GFUZZ" -modulepath "$ROOT/$MODULEPATH" \
		-include-tests -task check-can-build "$PACKAGE"

done <<< "$TO_CHECK"
