"""Offline boundary checks; historical execution evidence comes from the explicit benchmark."""
import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from direct_anvil_case import load_case, ReadOnlyRPC, OwnedRPC, DirectError
import direct_anvil_case
from benchmark_direct import project


class DirectBenchmarkTests(unittest.TestCase):
    def test_upstream_cannot_broadcast_or_mutate(self):
        rpc = ReadOnlyRPC('https://example.invalid')
        with patch.object(rpc.opener, 'open') as network:
            for method in ['eth_sendTransaction', 'eth_sendRawTransaction', 'anvil_setBalance', 'eth_call']:
                with self.subTest(method=method), self.assertRaises(DirectError):
                    rpc.call(method)
            network.assert_not_called()

    def test_owned_client_takes_only_a_local_port(self):
        for invalid in ['https://example.invalid', True, 0, 65536]:
            with self.subTest(port=invalid), self.assertRaises(DirectError):
                OwnedRPC(invalid)
        self.assertEqual(OwnedRPC(1234).url, 'http://127.0.0.1:1234')

    def test_changed_case_cannot_be_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'case.json'
            path.write_text('{}')
            with patch.object(direct_anvil_case, 'CASE', path):
                with self.assertRaisesRegex(DirectError, 'frozen'):
                    load_case()

    def test_standalone_execution_has_no_engine_imports(self):
        tree = ast.parse(Path(direct_anvil_case.__file__).read_text())
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append(node.module or '')
        self.assertFalse(any('entrotter' in name for name in names))

    def test_projection_rejects_tampered_reference(self):
        with self.assertRaisesRegex(ValueError, 'integrity'):
            project({'schema_version': '0.1.0', 'artifact_id': 'a' * 64})


if __name__ == '__main__':
    unittest.main()
