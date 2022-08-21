#!/usr/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
NC='\033[0m'


function help {
  echo -e "Available commands (optional components in ${GREEN}green${NC}):"
  echo -e "-- ${BLUE}run ${GREEN}[package]${NC} - Run the analysis on the specified package. If a package is not specified, the analysis will run on the complete benchmark suite."
  echo -e "   ${RED}WARNING${NC}: A complete run may take more than 24 hours"
  echo ""
  echo -e "-- ${BLUE}list ${GREEN}[repo]${NC} - List all analyzable packages in a repository. If [repo] is not specified, all packages across all repositories are listed"
  echo -e "-- ${BLUE}search ${GREEN}[repo] ${BLUE}[regex]${NC} - Search for all packages matching the string/regular expression. Narrows the search to entry points in [repo], if specified"
  # echo -e "-- ${BLUE}run-repo [repo]${NC} - Run the analysis on the specified repository."
  echo -e ""
  echo -e "-- ${YELLOW}exit${NC} - Terminate interactive GOAT session"
}

echo "Welcome to an interactive run of GOAT."
help

ROOT=$(realpath "$(dirname "$0")/..")
GFUZZ="$ROOT/external/gfuzz"

while [[ true ]]; do
  echo ""
  echo -n ">: "
  read -a COMMAND
  case ${COMMAND[0]} in
    list)
      if [ ${COMMAND[1]} ]; then
        LIST_COMM="$ROOT/benchmarks/list_packages_in_repo.sh $GFUZZ ${COMMAND[1]}"
      else
        LIST_COMM="$ROOT/benchmarks/list_packages.sh"
      fi
      while IFS=, read -r PACKAGE ENTRYPOINT; do
        echo $ENTRYPOINT
      done <<< $($LIST_COMM)
      ;;
    search)
      if [ ${COMMAND[1]} ]; then
        if [ ${COMMAND[2]} ]; then
          while IFS=, read -r PACKAGE ENTRYPOINT; do
            echo $ENTRYPOINT
          done <<< $($ROOT/benchmarks/list_packages_in_repo.sh $GFUZZ ${COMMAND[1]}) | grep ${COMMAND[2]}
        else
          while IFS=, read -r PACKAGE ENTRYPOINT; do
            echo $ENTRYPOINT
          done <<< $($ROOT/benchmarks/list_packages.sh) | grep ${COMMAND[1]}
        fi
      else
        echo -e "${RED}ERROR${NC} No search criterion provided."
      fi
      ;;
    run)
      rm -rf $ROOT/benchmarks/interactive_session
      echo "Building Goat binary..."
      echo ""

      if [ ${COMMAND[1]} ]; then
        $ROOT/benchmarks/run.py --dir interactive_session --entry_point ${COMMAND[1]} --flags -psets GCatch
      else
        $ROOT/benchmarks/run.py --dir interactive_session --flags -psets GCatch
      fi
      echo ""
      if [[ -d $ROOT/benchmarks/interactive_session ]]; then
        $ROOT/benchmarks/list_bugs.py interactive_session
      fi
      ;;
    exit)
      echo ""
      echo "Exiting interactive GOAT"
      exit 0;;
    *)
      echo "Unknown command: ${COMMAND[0]}"
      help
  esac
done