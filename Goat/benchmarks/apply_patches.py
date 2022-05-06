#! /usr/bin/env python3

import subprocess
from pathlib import Path
from argparse import REMAINDER, ArgumentParser


PROJECT_ROOT = Path(__file__).parent.parent.absolute()

DIFFS = PROJECT_ROOT / 'examples' / 'diffs'

parser = ArgumentParser()
parser.add_argument("dir", help="Folder in 'external' containing repository folders for which to apply patches (defaults to 'gfuzz')", nargs=REMAINDER)
args = parser.parse_args()

if len(args.dir) > 0:
  REPOS = PROJECT_ROOT / 'external' / ''.join(args)
else:
  REPOS = PROJECT_ROOT / 'external' / 'gfuzz'

lsrepos = subprocess.run(['ls', (REPOS)],
  capture_output=True,
  text=True,
  check=True).stdout.splitlines()

lsdiffrepos = subprocess.run(['ls', (DIFFS)],
  capture_output=True,
  text=True,
  check=True)

visited = {}

for repo in lsdiffrepos.stdout.splitlines():
  if repo in lsrepos:
    if repo == 'kubernetes':
      continue

    visited[repo] = True
    lsdiffs = subprocess.run(['ls', DIFFS/repo],
      capture_output=True,
      text=True,
      check=True).stdout.splitlines()
    
    for diff in lsdiffs:
      PATCHPATH = DIFFS / repo / diff / 'diff.patch'

      REPOPATH = REPOS / repo

      try:
        l = subprocess.run(['git', 'apply', PATCHPATH],
          capture_output=True,
          text=True,
          cwd=REPOPATH)

        if l.returncode == 0:
          print("Patch", diff, 'applied to', repo)
        else:
          print("Failed to apply patch", repo+'/'+diff)
          print(l.stderr)
      except:
        print("Failed to apply patch", repo + "/" + diff)
  else:
    print("No repository for", repo, "found at", REPOS)
    
for repo in lsrepos:
  if visited.get(repo) == None:
    print("Repository", repo, "was not patched")
