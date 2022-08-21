#! /usr/bin/env python3

import subprocess
from argparse import REMAINDER, ArgumentParser
from datetime import datetime
from pathlib import Path

from get_result_dir import get_dir

ROOT = Path(__file__).parent
parser = ArgumentParser()
parser.add_argument(
    "dir",
    help="Result folder to list bugs for (opts for latest when absent).",
    nargs="?",
    default="",
)
args = parser.parse_args()

# Latest result folder
result_dir = get_dir(args.dir)

repos = [p.name for p in (ROOT / result_dir).iterdir()]

sourcelocs = {}

for repo in repos:
    path = ROOT / result_dir / repo / "*.txt"

    rawsources = subprocess.run(
        f'grep -rP "Source:" {path}',
        text=True,
        shell=True,
        capture_output=True,
    ).stdout.splitlines()

    for l in rawsources:
        l = l.split("Source: ")

        if len(l) > 1:
            sourcelocs[l[1]] = True


str = "\n".join(p.split('/external/gfuzz/')[-1] for p in sorted(sourcelocs))

print("Bugs found:")
print(str)
