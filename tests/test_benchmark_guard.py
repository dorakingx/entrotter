"""No EVM/model calls: verify the benchmark refuses changed frozen inputs."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import benchmark_agent
import check_agent


class BenchmarkGuardTests(unittest.TestCase):
    def test_split_loading_does_not_execute_or_generate(self):
        with patch.object(benchmark_agent, 'run') as execute, patch.object(benchmark_agent, 'CodexPolicy') as model:
            _, evaluation = benchmark_agent.frozen_cases('evaluation', verify_engine=False)
            _, holdout = benchmark_agent.frozen_cases('holdout', verify_engine=False)
            self.assertEqual([x[0]['source']['block_number'] for x in evaluation], [17000000, 18000000, 19000000])
            self.assertEqual([x[0]['source']['block_number'] for x in holdout], [20000000, 21000000])
            execute.assert_not_called()
            model.assert_not_called()

    def test_current_engine_rejects_native_model_checker_before_execution(self):
        with patch.object(sys, 'argv', ['check_agent.py', '--generate-model']), patch.object(check_agent, 'run') as execute, patch.object(check_agent, 'run_agent') as agent, patch('codex_policy.CodexPolicy') as model:
            with self.assertRaisesRegex(ValueError, 'original clean Enginebb8'):
                check_agent.main()
            execute.assert_not_called()
            agent.assert_not_called()
            model.assert_not_called()

    def test_changed_manifest_fails_before_any_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'manifest.json').write_text(json.dumps({'version': 'changed'}))
            with patch.object(benchmark_agent, 'CASES', root), patch.object(benchmark_agent, 'run') as execute:
                with self.assertRaisesRegex(ValueError, 'Frozen manifest changed'):
                    benchmark_agent.frozen_cases('holdout')
                execute.assert_not_called()

    def test_dirty_engine_cannot_silently_change_holdout_policy(self):
        original = benchmark_agent.subprocess.check_output
        def check(argv, **kwargs):
            if argv[-2:] == ['rev-parse', 'HEAD']:
                return 'bb8b3e8d32c7cbd49629d337758f30bfdf805045\n'
            if argv[-2:] == ['status', '--porcelain']:
                return ' M src/changed.py\n'
            return original(argv, **kwargs)
        with patch.object(benchmark_agent.subprocess, 'check_output', check):
            with self.assertRaisesRegex(ValueError, 'clean at the frozen'):
                benchmark_agent.frozen_cases('holdout')


if __name__ == '__main__':
    unittest.main()
