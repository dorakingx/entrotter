Before-fix reproduction uses engine c1671938edde03c59deef64dbb81d7c41a33406b, public forward/reverse scenarios, and Foundry v1.8.3 in PATH. Run the archived reproduce-before.py from that engine checkout. It uses explicit trusted native execution and disposable local Anvil; no archive/model/Docker call. The script writes .quality/core-review/, which must exist. Its before-result and four owned guardian/port cleanup observations are retained separately.

After-fix commands from the new engine checkout:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p test_engine.py -k local_contract -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m ruff check src scripts
python3 -m ruff format --check src scripts
python3 -m mypy src scripts
python3 scripts/check_security.py
```

Use pinned Foundry v1.8.3 for the full native tests. Separate required Linux CI runs actual Docker kernel/lifecycle/report-equality cases; offline mocked admission checks are not Docker evidence.
