# Select the manifest-driven CLI quality setup

The candidate selects [CLIa10c28d](https://github.com/entrotter/cli/commit/a10c28df460cd7ae9a00f04180417440da7d5f88)
with the same SDKba4, Engine88c6, viewer422d and scenarios8785. The old CLI
quality recipe checked out an obsolete SDK revision rejected by its unchanged
source guard. The corrected recipe reads `sdk_commit` from quality-inputs.json;
separate frozen execution SDK pins remain unchanged.

[CLI setup evidence](https://github.com/entrotter/cli/blob/a10c28df460cd7ae9a00f04180417440da7d5f88/evidence/setup-pin/README.md)
records the exact fresh copied-checkout recipe, its terminal0, full quality
checks and local source-built installed wheels. Seven CLI and five SDK modules
match the original1ce packages; only CLI README metadata and RECORD changed.
An initial wrong-cwd attempt was interrupted130 and proves no complete success.
All six original current CLI CI checks passed separately. This is a verified
setup fix, not a new performance measurement or runtime feature.

This composition changes only the selected CLI pin and current setup guidance.
All eleven offline reader bodies, runtime/scripts/locks and other worker pins
are unchanged against rootb605. Its full five-check/eleven-reader CI results
are historical evidence reused without local reader reruns. Current root CI
will verify the new composition separately; final run links belong in existing
PR55. No fresh EVM/model/browser/media/user run, main merge, Pages deployment or
formal submission is inferred. Independent human main approval remains required;
the improvement goal stays active through the official deadline.
