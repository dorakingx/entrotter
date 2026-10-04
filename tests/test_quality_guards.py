"""Security boundaries for executable verification tools; no EVM or network."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


class VerificationGuards(unittest.TestCase):
    def test_optimized_interpreter_rejects_wrong_wheel_before_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/entrotter_engine"
            source.mkdir(parents=True)
            (source / "__init__.py").write_text('VALUE = "expected"\n')
            wheel = root / "wrong.whl"
            with ZipFile(wheel, "w") as archive:
                archive.writestr("entrotter_engine/__init__.py", 'VALUE = "wrong"\n')
                archive.writestr(
                    "entrotter_engine-0.1.0.dist-info/METADATA",
                    "License-Expression: MIT\n",
                )
            code = """import json,runpy,subprocess,sys
calls=[]
def forbidden(*args,**kwargs):
    calls.append('installation_or_execution')
    raise RuntimeError('Unexpected subprocess before wheel rejection')
subprocess.run=forbidden
script=sys.argv.pop(1)
try:
    runpy.run_path(script,run_name='__main__')
except AssertionError:
    print(json.dumps({'rejected':True,'calls':calls}))
except Exception as error:
    print(json.dumps({'rejected':False,'calls':calls,'error':type(error).__name__}))
"""
            arguments = [
                sys.executable,
                "-O",
                "-c",
                code,
                str(ROOT / "scripts/check_default_wheels.py"),
            ]
            for name in ["engine", "sdk", "cli"]:
                arguments += [
                    "--" + name + "-source",
                    str(root),
                    "--" + name + "-wheel",
                    str(wheel),
                ]
            arguments += [
                "--reference",
                str(root / "reference.json"),
                "--output",
                str(root / "result.json"),
            ]
            result = subprocess.run(
                arguments,
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, "PYTHONOPTIMIZE": "1"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"rejected": True, "calls": []})
            self.assertFalse((root / "result.json").exists())


if __name__ == "__main__":
    unittest.main()
