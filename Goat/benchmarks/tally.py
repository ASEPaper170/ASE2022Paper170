#! /usr/bin/env python3

import math
import subprocess
from pathlib import Path
from argparse import ArgumentParser
from get_result_dir import get_dir

ROOT = Path(__file__).parent
parser = ArgumentParser()
parser.add_argument("result", help="Result folder to tally (opts for latest when absent).", nargs="?", default="")
args = parser.parse_args()

# Latest result folder
result_dir = get_dir(args.result)

lsres = subprocess.run(['ls', (ROOT / result_dir)],
  capture_output=True,
  text=True,
  check=True)

repos = lsres.stdout.splitlines()

completed = 0
aborted = 0
skipped = 0
fails = 0

for repo in repos:
  path = ROOT / result_dir / repo / '*.txt'

  wc = subprocess.run(
    'grep -rP "Aborted" ' + path.__str__() + ' | wc -l',
    text=True,
    shell=True,
    capture_output=True,)
  aborted += int(wc.stdout)
  skippedrun = subprocess.run(
    'grep -rP "Skipped" ' + path.__str__() + ' | wc -l',
    text=True,
    shell=True,
    capture_output=True,)
  skipped += int(skippedrun.stdout)
  completerun = subprocess.run(
    'grep -rP "SA completed" ' + path.__str__() + ' | wc -l',
    text=True,
    shell=True,
    capture_output=True,)
  completed += int(completerun.stdout)
  failedrun = subprocess.run(
    'grep -rP "failed" ' + path.__str__() + ' | wc -l',
    text=True,
    shell=True,
    capture_output=True,)
  fails += int(failedrun.stdout)

if 'results_' in result_dir:
  result_name = result_dir.split('results_')[1].replace('#', ' ')
else:
  result_name = result_dir

print("Tallying results for", result_name)
print("Aborted analyses: ", aborted)
print("Completed analyses: ", completed)
print("Skipped analyses: ", skipped)
print("Failed:", fails)
if aborted + completed + skipped != 0:
  print("Percentage completed vs. skipped or aborted:", math.floor(float(completed / (aborted + completed + skipped) * 10000)) / 100, "%")
else:
  print("Percentage completed vs. skipped: 0%")
