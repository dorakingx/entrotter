"""Signed synthetic oracle same-block replay with actual parent read savings."""

import shutil
import unittest
from unittest.mock import patch

from entrotter_engine.parent_cache import ParentCache
import test_trace_oracle as oracle


class Uncached:
    def __init__(self, url, parent, deadline):
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@unittest.skipUnless(shutil.which("anvil"), "Pinned Anvil required")
class ParentCacheNativeTests(unittest.TestCase):
    def test_exact_receipts_fewer_reads_and_no_source_repairs(self):
        Case = oracle.TraceOracleProviderIntegrationTests
        with patch("entrotter_engine.trace.ParentCache", Uncached):
            Case.setUpClass()
        self.addCleanup(Case.doClassCleanups)
        uncached = oracle.ReadOnlyFaultProxy(Case.source.rpc.url, "none", 2)
        try:
            with patch("entrotter_engine.trace.ParentCache", Uncached):
                original, _ = Case.run_owned(uncached.url)
        finally:
            uncached.close()
        cached = oracle.ReadOnlyFaultProxy(Case.source.rpc.url, "none", 2)
        bridges = []

        def create(*args, **kwargs):
            bridge = ParentCache(*args, **kwargs)
            bridges.append(bridge)
            return bridge

        try:
            with patch("entrotter_engine.trace.ParentCache", side_effect=create):
                actual, _ = Case.run_owned(cached.url)
        finally:
            cached.close()
        for field in ["source", "baseline", "candidate", "baseline_verified", "plan"]:
            self.assertEqual(actual[field], original[field])
            self.assertEqual(actual[field], Case.report[field])
        reads = {
            "eth_getBalance",
            "eth_getCode",
            "eth_getTransactionCount",
            "eth_getStorageAt",
        }
        self.assertLess(
            sum(cached.requests[m] for m in reads),
            sum(uncached.requests[m] for m in reads),
        )
        self.assertGreater(bridges[0].stats["hits"], 0)
        self.assertEqual(
            [o["status"] for o in actual["baseline"]["outcomes"]],
            ["executed", "executed"],
        )
        self.assertEqual(actual["candidate"]["outcomes"][1]["receipt"]["status"], "0x0")
        self.assertEqual(
            actual["baseline"]["outcomes"][1]["receipt"]["logs"][0]["data"],
            "0x" + (20).to_bytes(32, "big").hex(),
        )
        self.assertEqual(
            Case.source.rpc.call(
                "eth_call", [{"to": Case.fixture["oracle"], "data": "0x"}, "latest"]
            ),
            "0x" + (20).to_bytes(32, "big").hex(),
        )
        self.assertEqual(
            [
                Case.source.rpc.call("eth_getTransactionCount", [a, "latest"])
                for a in Case.fixture["actors"]
            ],
            ["0x3", "0x1"],
        )
        self.observation = {
            "uncached_upstream": dict(uncached.requests),
            "cached_upstream": dict(cached.requests),
            "cache": bridges[0].stats,
            "node_cleanup": list(Case.cleanup_records),
            "proxy_threads_closed": not cached.thread.is_alive()
            and not uncached.thread.is_alive(),
        }
        self.reports = {"original": original, "cached": actual}

    def test_unmined_receipt_fallback_remains_unverified_and_uncached(self):
        Case = oracle.TraceOracleProviderIntegrationTests
        with patch("entrotter_engine.trace.ParentCache", Uncached):
            Case.setUpClass()
        self.addCleanup(Case.doClassCleanups)
        proxy = oracle.ReadOnlyFaultProxy(Case.source.rpc.url, "eth_getStorageAt", 2)
        try:
            with patch("entrotter_engine.trace.ParentCache", Uncached):
                original, _ = Case.run_owned(proxy.url)
            before = proxy.requests["eth_getTransactionReceipt"]
            self.assertGreater(before, 2)  # Includes Anvil's unmined fallback.
            actual, _ = Case.run_owned(proxy.url)
            self.assertEqual(
                proxy.requests["eth_getTransactionReceipt"] - before, before
            )
        finally:
            proxy.close()
        self.assertFalse(actual["baseline_verified"])
        for field in ["source", "baseline", "candidate"]:
            self.assertEqual(actual[field], original[field])
        self.assertEqual(
            [o["status"] for o in actual["baseline"]["outcomes"]],
            ["not_mined", "not_mined"],
        )
        self.assertEqual(
            [o["status"] for o in actual["candidate"]["outcomes"]],
            ["skipped", "not_mined"],
        )
        self.assertTrue(
            all(
                "receipt" not in o
                for branch in ["baseline", "candidate"]
                for o in actual[branch]["outcomes"]
            )
        )
