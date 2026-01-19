#!/usr/bin/env bash
set -euo pipefail

left=$(printf '<%.0s' {1..7})
mid=$(printf '=%.0s' {1..7})
right=$(printf '>%.0s' {1..7})
pattern="${left}|${mid}|${right}"
if rg -n "$pattern" .; then
  echo "Merge markers found. Resolve conflicts first." >&2
  exit 1
fi

python -m compileall -q .

if python - <<'PY'
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec("pytest") else 1)
PY
then
  python -m pytest
else
  python -m unittest
fi
