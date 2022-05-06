#! /usr/bin/env python3

import subprocess
from pathlib import Path
from argparse import REMAINDER, ArgumentParser
from re import split

from get_result_dir import get_dir

parser = ArgumentParser()
parser.add_argument("--dir", help="Folder in 'external' the bug run (defaults to latest)",
  nargs="?")
parser.add_argument("bug", help="Bug path to search for.", nargs=REMAINDER)
args = parser.parse_args()

if not args.bug:
  raise BaseException("No bug specified!")
else:
  bug = args.bug[0]

ROOT = Path(__file__).parent

DIR = get_dir(args.dir)

bug_occurrences = subprocess.run(['grep', '-rP', bug, ROOT / DIR],
  capture_output=True,
  text=True)

bug_occurrences = bug_occurrences.stdout.splitlines()

files = {}

for bug_report in bug_occurrences:
  if 'Source:' in bug_report:
    ns = bug_report.split(':Source:')
    files[ns[0]] = True

runs = []
entry, pset = '', ''
for file in files.keys():
  report = subprocess.run(['less', file],
    capture_output=True,
    text=True).stdout.splitlines()

  goatRun = [
    'go run Goat ',
    ' -visualize ' + report[0].split('./Goat')[1]
  ]

  context = {}

  for line in report[1:]:
    if ': Entry ' in line:
      context['fun'] = split('Entry \d+ of \d+:', line)[1]
    if 'Found PSet ' in line:
      context['pset'] = split('Found PSet ', line)[1].split(' of ')[0]
    if bug in line:
      runStr = goatRun[0]
      if 'pset' in context.keys():
        runStr = runStr + '-pset ' + context['pset'] + ' '
      if 'fun' in context.keys():
        runStr = runStr + '-fun' + context['fun']
      else:
        runStr = goatRun[0] + goatRun[1]
      runStr = runStr + goatRun[1]

      runs.append({
        'run' : runStr,
        # 'pset' : context['pset'],
      })

for run in runs:
  print(run['run'])
  if 'pset' in run:
    print("PSet: ", run['pset'])