"""Recognize actual unittest skips without confusing test names with results."""

import re


def unittest_has_skips(log):
    return bool(
        re.search(
            r"^(?:.*\.\.\. skipped(?:\s|$)|(?:OK|FAILED)\s*\([^\n)]*\bskipped=[1-9][0-9]*\b)",
            log,
            re.MULTILINE,
        )
    )
