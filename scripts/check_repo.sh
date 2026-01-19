#!/usr/bin/env bash
set -euo pipefail

<<<<<<< ours
git status -sb

if rg -n "<<<<<<<|=======|>>>>>>>" . --glob "!scripts/check_repo.sh"; then
  echo "Merge markers found. Resolve conflicts first."
  exit 1
fi

python -m compileall -q .
python -m pytest || python -m unittest
printf "/end\n" | python main.py
=======
echo "== 1) Merge markers check =="
if rg -n "<<<<<<<|=======|>>>>>>>" -g '!scripts/check_repo.sh' . ; then
  echo
  echo "ERROR: Merge conflict markers found. Resolve them before running."
  exit 1
fi
echo "OK: no merge markers."

echo
echo "== 2) Python syntax (compileall) =="
python -m compileall -q .
echo "OK: compileall."

echo
echo "== 3) Tests =="
if [ -f "pytest.ini" ] || [ -d ".pytest_cache" ] || rg -n "pytest" pyproject.toml setup.cfg requirements.txt 2>/dev/null; then
  python -m pytest
else
  python -m unittest
fi

echo
echo "ALL OK."
>>>>>>> theirs
