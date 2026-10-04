#!/usr/bin/env bash
set -euo pipefail
ENTROTTER_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
for component in engine sdk-python cli scenarios website; do
  if [[ ! -d "$ENTROTTER_ROOT/$component" ]]; then
    printf 'Missing monorepo component: %s\n' "$component" >&2
    exit 1
  fi
done
python3 -m venv "$ENTROTTER_ROOT/.venv"
# Install local unpublished Entrotter packages; never resolve their names on PyPI.
"$ENTROTTER_ROOT/.venv/bin/python" -m pip install --no-deps -e "$ENTROTTER_ROOT/engine" -e "$ENTROTTER_ROOT/sdk-python" -e "$ENTROTTER_ROOT/cli"
printf '\nActivate with: source "%s/.venv/bin/activate"\n' "$ENTROTTER_ROOT"
printf 'Then run: entrotter doctor\n'
