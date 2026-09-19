# Status

## SDK round-trip example

- Added an offline synthetic artifact verification and temporary-file roundtrip,
  plus an optional local API/scenario path.
- Verified: `PYTHONPATH=src python3 examples/roundtrip.py` printed the fixture
  artifact hash and integrity limitation.
- Verified: `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 16 tests
  passed, including the offline example subprocess test.
- No API, chain, or paid service was contacted.
