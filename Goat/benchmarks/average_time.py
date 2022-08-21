#! /usr/bin/env python3

import subprocess
from argparse import ArgumentParser
from pathlib import Path
from statistics import quantiles

from get_result_dir import get_dir

ROOT = Path(__file__).parent
parser = ArgumentParser()
parser.add_argument(
    "dir",
    help="Result folder to check average time for (opts for latest when absent).",
    nargs="?",
)
args = parser.parse_args()

# Latest result folder
result_dir = get_dir(args.dir)

repos = [p.name for p in (ROOT / result_dir).iterdir()]

times = []

for repo in repos:
    path = ROOT / result_dir / repo / "*.txt"

    rawsources = subprocess.run(
        f'grep -rP "SA completed" {path}',
        text=True,
        shell=True,
        capture_output=True,
    ).stdout.splitlines()

    for line in rawsources:
        parts = line.split("SA completed in ")

        if len(parts) > 1:
            l = parts[1]
            if l.endswith("ms"):
                times.append(float(l[:-2]))
            elif l.endswith("µs"):
                times.append(float(l[:-2]) / 1000)
            elif l.endswith("s"):
                t = 0.0
                if "m" in l:
                    m, l = l.split("m")
                    t += 60 * int(m) * 1000
                times.append(t + float(l[:-1]) * 1000)

print(f"Average completion time: {sum(times) / len(times):.2f}ms for {len(times)} runs")
print(f"Worst time: {max(times):.2f}ms")

qt = quantiles(times, n=100)
for pct in (80, 90, 95, 98, 99):  # Can be updated
    print(f"{pct}% finish in ≤ {qt[pct-1]:.2f}ms")
