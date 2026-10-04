from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from entrotter_engine.api import EngineServer
from entrotter_engine.runner import run
from entrotter_sdk import Client, verify
from entrotter_cli.main import main
from contextlib import redirect_stdout
import io

W=Path(__file__).resolve().parents[1]
class WorkspaceTests(unittest.TestCase):
    def test_all_exported_reports_reproduce_exactly(self):
        for p in (W/'scenarios/fixtures').glob('*.json'):
            with self.subTest(scenario=p.name):
                expected=json.loads((W/'website/reports'/p.name).read_text())
                self.assertEqual(run(json.loads(p.read_text())),expected)
    def test_cli_local_verify_inspect(self):
        with tempfile.TemporaryDirectory() as d,redirect_stdout(io.StringIO()):
            out=str(Path(d)/'report.json')
            self.assertEqual(main(['run',str(W/'scenarios/fixtures/liquidity-shock.json'),'--local','-o',out]),0)
            self.assertEqual(main(['verify',out]),0)
            self.assertEqual(main(['inspect',out]),0)
    def test_sdk_api_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            s=EngineServer(0,output=d);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            try:
                client=Client(f'http://127.0.0.1:{s.server_port}')
                self.assertEqual(client.health()['status'],'ok')
                scenario=json.loads((W/'scenarios/fixtures/liquidity-shock.json').read_text())
                result=client.run(scenario);self.assertTrue(verify(result.report))
                self.assertEqual(client.get(result.artifact_id).report,result.report)
            finally:s.shutdown();s.server_close();t.join()
    def test_public_manifest_boundaries(self):
        manifest=json.loads((W/'repositories.json').read_text())
        self.assertEqual(manifest['owner'],'dorakingx')
        self.assertEqual(manifest['name'],'entrotter')
        self.assertEqual(manifest['visibility'],'public')
        self.assertEqual(len(manifest['components']),6)
        for repo in manifest['components']:
            for name in ['LICENSE','README.md','AGENTS.md','CONTRIBUTING.md','SECURITY.md']:
                self.assertTrue((W/repo['path']/name).is_file())
    def test_copied_fixture_contract(self):
        self.assertEqual((W/'engine/tests/data/fixture.json').read_bytes(),(W/'scenarios/fixtures/liquidity-shock.json').read_bytes())
    def test_no_cname(self):
        self.assertEqual(list((W/'website').rglob('CNAME')),[])

if __name__=='__main__':unittest.main()
