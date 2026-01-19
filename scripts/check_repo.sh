#!/usr/bin/env bash
set -euo pipefail

git status -sb

if rg -n "<<<<<<<|=======|>>>>>>>" . --glob "!scripts/check_repo.sh"; then
  echo "Merge markers found. Resolve conflicts first."
  exit 1
fi

python -m compileall -q .
python -m pytest || python -m unittest
printf "/end\n" | python main.py
