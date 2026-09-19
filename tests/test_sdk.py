import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from entrotter_sdk import Client, ClientError, RunResult, verify

def artifact():
    body={'schema_version':'0.1.0','mode':'fixture','scenario':{},'baseline':{},'candidate':{},'comparison':{}}
    data=json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
    body['artifact_id']=hashlib.sha256(data).hexdigest();return body

class SDKTests(unittest.TestCase):
    def test_offline_roundtrip_example(self):
        root = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PYTHONPATH": str(root / "src")}
        result = subprocess.run(
            [sys.executable, "examples/roundtrip.py"],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Verified fixture artifact:", result.stdout)
        self.assertIn("does not establish model correctness", result.stdout)

    def test_valid_hash(self): self.assertTrue(verify(artifact()))
    def test_tamper(self):
        a=artifact();a['mode']='evm-local';self.assertFalse(verify(a))
    def test_unknown_version(self):
        a=artifact();a['schema_version']='2';self.assertFalse(verify(a))
    def test_parse(self): self.assertEqual(RunResult.parse(artifact()).mode,'fixture')
    def test_parse_rejects(self):
        with self.assertRaises(ClientError): RunResult.parse({})
    def test_https_url(self): self.assertEqual(Client('https://example.test').base_url,'https://example.test')
    def test_plaintext_remote_rejected(self):
        with self.assertRaises(ClientError): Client('http://example.test')
    def test_embedded_credentials(self):
        with self.assertRaises(ClientError): Client('https://secret:key@example.test')
    def test_query_rejected(self):
        with self.assertRaises(ClientError): Client('https://example.test?key=secret')
    def test_path_rejected(self):
        with self.assertRaises(ClientError): Client('https://example.test/api')
    def test_zero_timeout(self):
        with self.assertRaises(ClientError): Client(timeout=0)
    def test_id_validation(self):
        with self.assertRaises(ClientError): Client().get('../../etc/passwd')
    def test_run_dispatch(self):
        a=artifact()
        with patch.object(Client,'_request',return_value=a) as call:
            result=Client().run({'x':1});call.assert_called_once_with('POST','/v1/runs',{'x':1});self.assertEqual(result.artifact_id,a['artifact_id'])
    def test_get_must_match_id(self):
        with patch.object(Client,'_request',return_value=artifact()),self.assertRaises(ClientError): Client().get('a'*64)
    def test_body_limit(self):
        with self.assertRaises(ClientError): Client().run({'big':'x'*270000})

if __name__=='__main__': unittest.main()
