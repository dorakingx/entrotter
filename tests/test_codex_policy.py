"""Offline provider boundary tests; no authenticated model calls in CI."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from codex_policy import bounded_process, parse_events
from entrotter_engine.agent import AgentError


class CodexBoundaryTests(unittest.TestCase):
    def test_one_typed_response_and_usage(self):
        request = {'request_id': 'a' * 64}
        response = {'request_id': request['request_id'], 'choice': 'hold', 'reason': 'local preflight rejected'}
        events = [{'type': 'thread.started', 'thread_id': 'not-published'}, {'type': 'turn.started'},
                  {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': json.dumps(response)}},
                  {'type': 'turn.completed', 'usage': {'input_tokens': 100, 'output_tokens': 20}}]
        raw = '\n'.join(json.dumps(x) for x in events).encode()
        decision, usage = parse_events(raw, request)
        self.assertEqual(decision, response)
        self.assertEqual(usage, {'input_tokens': 100, 'output_tokens': 20})
        for extra in [{'type': 'item.started', 'item': {'type': 'command_execution'}},
                      {'type': 'error', 'message': 'private'}, {'type': 'turn.failed'}]:
            with self.subTest(event=extra), self.assertRaises(AgentError):
                parse_events(raw + b'\n' + json.dumps(extra).encode(), request)
        with self.assertRaises(AgentError):
            parse_events(raw + b'\n' + raw, request)
        with self.assertRaises(AgentError):
            parse_events(b'not JSON', request)

    def test_empty_or_invalid_usage_never_looks_completed(self):
        for raw in [b'', b'{"type":"turn.completed","usage":{"input_tokens":-1}}',
                    b'{"type":"turn.completed","usage":null}']:
            with self.subTest(raw=raw), self.assertRaises(AgentError):
                parse_events(raw, {'request_id': 'a' * 64})

    def test_bounded_process_stdin_and_no_secret_environment_forwarding(self):
        with tempfile.TemporaryDirectory() as directory:
            from unittest.mock import patch
            with patch.dict(os.environ, {'ENTROTTER_RPC_URL': 'secret-upstream', 'ENTROTTER_API_TOKEN': 'secret-token'}):
                data = bounded_process([sys.executable, '-c',
                    'import os,sys; assert "ENTROTTER_RPC_URL" not in os.environ; assert "ENTROTTER_API_TOKEN" not in os.environ; sys.stdout.buffer.write(sys.stdin.buffer.read())'],
                    b'bounded observation', cwd=directory, timeout=5)
            self.assertEqual(data, b'bounded observation')

    def test_output_limit_fails_without_returning_partial_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(AgentError, 'byte limit'):
                bounded_process([sys.executable, '-c', 'print("x" * 1000000)'], b'',
                                cwd=directory, timeout=5, max_output=1024)

    def test_timeout_reaps_owned_child(self):
        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory) / 'pid'
            with self.assertRaisesRegex(AgentError, 'timed out'):
                bounded_process([sys.executable, '-c',
                    'import os,sys,time; open(sys.argv[1],"w").write(str(os.getpid())); time.sleep(20)',
                    str(pidfile)], b'', cwd=directory, timeout=.3)
            self.assertTrue(pidfile.exists())
            with self.assertRaises(ProcessLookupError):
                os.kill(int(pidfile.read_text()), 0)

    def test_nonzero_exit_redacts_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AgentError) as error:
                bounded_process([sys.executable, '-c', 'import sys; sys.stderr.write("secret"); sys.exit(2)'],
                                b'', cwd=directory, timeout=5)
            self.assertNotIn('secret', str(error.exception))


if __name__ == '__main__':
    unittest.main()
