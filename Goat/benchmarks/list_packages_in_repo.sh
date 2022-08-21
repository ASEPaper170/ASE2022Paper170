#! /usr/bin/env bash

set -euo pipefail

ROOT=$(realpath "$(dirname "$0")/..")

GOPATH=$(realpath "$1")
REPONAME="$2"
REPOPATH="$GOPATH/$REPONAME"

MODULES=$(find "$REPOPATH" -name "go.mod" ! -ipath "*/vendor/*")
if [[ ! -z "$MODULES" ]]; then
	for F in $MODULES; do
		MODULEPATH=$(dirname "$F")
		MODULENAME=$(sed -nr 's/^module (\S+)/\1/p' "$F")
		#echo -e "\tPackages in ${MODULEPATH}:" > /dev/stderr

		PACKAGES=$(cd "$MODULEPATH" && env GOPATH="$GOPATH" \
				go list -test -f '{{.ImportPath}},{{.Name}}' ./... 2>/dev/null)

		while IFS=, read -r package pname; do
			# Remove .test suffix
			package=${package%".test"}
			# Only match main packages (that aren't just recompiled for testing)
			if [[ "$pname" == "main" ]] && [[ "$package" != *".test]" ]]; then
				echo "${MODULEPATH#"$ROOT/"},$package"
			fi
		done <<< "$PACKAGES"
	done | sort --unique
	# We may have duplicates for main packages with tests, so we filter the output through sort -u
else
	# TODO: moby needs to run in legacy mode
	:
fi
