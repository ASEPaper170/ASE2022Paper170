#!/bin/bash

echo "Building GOAT binaries..."
echo ""

./benchmarks/run.py --dir ase_results

echo "Analysis results:"
./benchmarks/tally.py ase_results
./benchmarks/list_bugs.py ase_results

echo "Total reports:"
./benchmarks/list_bugs.py ase_results | wc -l