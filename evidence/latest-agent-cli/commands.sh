set -eu
mkdir entrotter-candidate
cd entrotter-candidate
git init --quiet entrotter
git -C entrotter fetch --quiet --depth=1 https://github.com/entrotter/entrotter.git 924f60ee90364218a700bf7416496ab86132b339
git -C entrotter checkout --quiet --detach FETCH_HEAD
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

pins = json.loads(Path("entrotter/bounded-worker-pins.json").read_text())
for name, sha in pins.items():
    subprocess.run(["git", "init", "--quiet", name], check=True)
    subprocess.run(["git", "-C", name, "fetch", "--quiet", "--depth=1",
                    f"https://github.com/entrotter/{name}.git", sha], check=True)
    subprocess.run(["git", "-C", name, "checkout", "--quiet", "--detach", "FETCH_HEAD"], check=True)
    actual = subprocess.check_output(["git", "-C", name, "rev-parse", "HEAD"], text=True).strip()
    if actual != sha:
        raise SystemExit(f"Unexpected source revision: {name}")
    print(name, actual)
PY
python3 -m venv --without-pip .venv
export PYTHONPATH="$PWD/engine/src:$PWD/sdk-python/src:$PWD/cli/src"

export ENTROTTER_DOCKER_SOCKET="${ENTROTTER_DOCKER_SOCKET:-/var/run/docker.sock}"
test -S "$ENTROTTER_DOCKER_SOCKET"
.venv/bin/python engine/scripts/build_worker.py --output worker-image.json
export ENTROTTER_WORKER_IMAGE="$(.venv/bin/python -c 'import json; print(json.load(open("worker-image.json"))["image_id"])')"
.venv/bin/python -m entrotter_cli doctor

.venv/bin/python -m entrotter_cli run scenarios/fixtures/liquidity-shock.json --local -o report.json
.venv/bin/python -m entrotter_cli verify report.json
.venv/bin/python -m entrotter_cli inspect report.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path

actual = json.loads(Path("report.json").read_text())
expected = json.loads(Path("entrotter.github.io/reports/liquidity-shock.json").read_text())
if actual != expected:
    raise SystemExit("Report differs from the pinned public fixture")
print("Complete report matches the pinned public fixture")
PY

.venv/bin/python -m entrotter_cli run scenarios/evm/local-branch-revert.json --local -o local-evm.json
.venv/bin/python -m entrotter_cli verify local-evm.json

.venv/bin/python - <<'PY'
import json
from pathlib import Path

reference = json.loads(Path("cli/tests/data/agent-risk-local.json").read_text())
Path("recorded-agent-scenario.json").write_text(json.dumps(reference["scenario"]))
PY
.venv/bin/python -m entrotter_cli agent-run recorded-agent-scenario.json --steps 0 1 -o risk-agent.json
.venv/bin/python -m entrotter_cli replay risk-agent.json -o risk-replayed.json
.venv/bin/python -m entrotter_cli replay cli/tests/data/agent-recorded-local.json -o model-replayed.json
.venv/bin/python -m entrotter_cli verify model-replayed.json
.venv/bin/python -m entrotter_cli inspect model-replayed.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path

for actual, reference in [
    ("risk-agent.json", "cli/tests/data/agent-risk-local.json"),
    ("risk-replayed.json", "cli/tests/data/agent-risk-local.json"),
    ("model-replayed.json", "cli/tests/data/agent-recorded-local.json"),
]:
    if json.loads(Path(actual).read_text()) != json.loads(Path(reference).read_text()):
        raise SystemExit(f"Complete agent report differs: {actual}")
print("Risk execution/replay and recorded-model replay match complete original reports")
PY
