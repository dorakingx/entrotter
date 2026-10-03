# Exact recorded WETH prices in the terminal

`observed-inspect --format text` validates the fixed Aave/WETH wrapper and nested
trace with the selected SDK before printing anything. The default and explicit
JSON output bytes are unchanged. After-prefix baseline/candidate/difference and
four phase prices are scaled with integer-only arithmetic. The original32-record
sample shows2562.92441874 USD versus2570.82415 USD, delta+7.89973126 USD.
Artifact/source IDs, finite unproven reasons, phase head numbers and original
receipt matching remain visible; this is recorded inspection, not fresh execution.

Eight new groups cover the entire independently specified text golden, old JSON
bytes, positive/negative/zero and minimum-unit differences, all six existing
synthetic diagnostics (including2**200), unsupported currency/unit, unmatched
receipts, invalid input and forbidden options. Missing comparison values remain
Unavailable, not zero; a quoted phase price alone does not prove completeness.
Before implementation the new groups reported15 failed assertions because the
option was absent. The shell wrapper ended0 after tail; that is not test success.
After implementation all8 groups and the full100 units passed without skips.
[Complete unit log](unit.log.gz), [full unsuppressed10-source Bandit](bandit.json)
and [source/package manifest](local-verification.json) retain observed evidence.
Ruff14 inputs and mypy10 sources passed; unchanged locked dependency queries are
historical locally, with current mandatoryCI separately required.

Fresh local source wheels were installed without a registry or Engine. All8CLI/
5SDK source, wheel and installed module bytes match; full README metadata and
every RECORD digest/size are checked. Installed8 groups and whole new text, old
price JSON/verification and account text goldens pass with isolated Python and
no PYTHONPATH. The initial module verifier imported executable __main__, invoking
argparse; its finite failure is retained. The corrected verifier reads installed
module origins without executing entry modules; the same fresh environment is
reused without reinstall, source/unit/quality reruns or production changes.

Mandatory installed CI also compares the whole text golden and runs the8 groups.
No new EVM/model/browser/RPC, timing comparison, media/user result, main/Pages,
registry or submission is inferred. Human main approval remains separate and the
improvement goal continues through the official deadline.
