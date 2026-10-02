"""An upstream error envelope is untrusted, including fields conventionally numeric."""
import io
import json
import unittest
import socket
import ssl
import threading
import os
from contextlib import redirect_stderr, redirect_stdout
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.client import IncompleteRead, HTTPException
from urllib.error import URLError, HTTPError
from unittest.mock import patch

from entrotter_engine.rpc import RPC, RPCError, RPCRejected, OwnedTraceRPC


class RPCDiagnosticTests(unittest.TestCase):
    def rejection(self, error):
        rpc = RPC('https://example.invalid')
        reply = io.BytesIO(json.dumps({'jsonrpc': '2.0', 'id': 1, 'error': error}).encode())
        with patch.object(rpc.opener, 'open', return_value=reply):
            with self.assertRaises(RPCRejected) as caught:
                rpc.call('eth_call', [])
        return str(caught.exception)

    def test_untrusted_code_cannot_enter_diagnostics(self):
        marker = 'UPSTREAM_PRIVATE_DIAGNOSTIC_MARKER'
        for code in [marker, {'nested': marker}, [marker]]:
            with self.subTest(code=code):
                message = self.rejection({'code': code, 'message': 'ignored upstream message'})
                self.assertNotIn(marker, message)
                self.assertEqual(message, 'RPC rejected eth_call')

    def test_error_message_and_data_are_never_echoed(self):
        message = self.rejection({'code': -32000, 'message': 'PRIVATE_MESSAGE', 'data': 'PRIVATE_DATA'})
        self.assertEqual(message, 'RPC rejected eth_call')

    def test_non_object_error_does_not_echo_untrusted_text(self):
        self.assertEqual(self.rejection('PRIVATE_ENVELOPE'), 'RPC rejected eth_call')


class SafeRPCFailureTests(unittest.TestCase):
    def failure(self, error, method='eth_call'):
        rpc = RPC('https://example.invalid/private?token=PRIVATE_URL')
        with patch.object(rpc.opener, 'open', side_effect=error):
            with self.assertRaises(RPCError) as caught:
                rpc.call(method, [{'private': 'PRIVATE_PARAM'}])
        self.assertIsInstance(caught.exception, RuntimeError)
        self.assertNotIn('PRIVATE', str(caught.exception))
        self.assertNotIn('PRIVATE', json.dumps(caught.exception.diagnostics))
        return caught.exception

    def test_timeout_types_do_not_require_error_messages(self):
        for error in [TimeoutError('PRIVATE_TIMEOUT'), URLError(TimeoutError('PRIVATE_REASON'))]:
            with self.subTest(type=type(error).__name__):
                failure = self.failure(error)
                self.assertEqual(failure.diagnostics, {'code': 'timeout', 'method': 'eth_call'})

    def test_http_connection_and_tls_classification_without_private_fields(self):
        cases = [
            (HTTPError('https://PRIVATE_URL', 403, 'PRIVATE_MESSAGE', {}, None), 'http_error'),
            (URLError(ConnectionRefusedError('PRIVATE_CONNECTION')), 'connection_error'),
            (URLError(socket.gaierror('PRIVATE_DNS')), 'connection_error'),
            (URLError(ssl.SSLCertVerificationError('PRIVATE_CERT')), 'tls_error'),
            (OSError('PRIVATE_UNKNOWN_TRANSPORT'), 'transport_error'),
            (URLError('PRIVATE_TEXT_REASON'), 'transport_error'),
        ]
        for error, expected in cases:
            with self.subTest(code=expected):
                self.assertEqual(self.failure(error).code, expected)

    def test_hostile_exception_formatters_and_reason_access_are_never_required(self):
        class HostileReason(URLError):
            @property
            def reason(self):
                raise ValueError('PRIVATE_PROPERTY')
            @reason.setter
            def reason(self, value):
                pass
            def __str__(self):
                raise AssertionError('private exception formatted')
            def __repr__(self):
                raise AssertionError('private exception represented')
        class HostileTimeout(TimeoutError):
            def __str__(self):
                raise AssertionError('private exception formatted')
            def __repr__(self):
                raise AssertionError('private exception represented')
        self.assertEqual(self.failure(HostileReason('PRIVATE')).code, 'transport_error')
        self.assertEqual(self.failure(HostileTimeout('PRIVATE')).code, 'timeout')

    def test_response_failures_and_rejection_are_distinct(self):
        cases = [
            (b'PRIVATE_MALFORMED_JSON', 'invalid_response', RPCError),
            (b'[' * 2000 + b'0' + b']' * 2000, 'invalid_response', RPCError),
            (b'{"id":999,"result":"PRIVATE"}', 'invalid_response', RPCError),
            (b'{"id":1}', 'invalid_response', RPCError),
            (b'x' * (4 * 1024 * 1024 + 1), 'response_too_large', RPCError),
            (b'{"id":1,"error":{"message":"PRIVATE","code":"PRIVATE","data":"PRIVATE"}}', 'rejected', RPCRejected),
        ]
        for raw, code, kind in cases:
            rpc = RPC('https://example.invalid')
            with self.subTest(code=code), patch.object(rpc.opener, 'open', return_value=io.BytesIO(raw)):
                with self.assertRaises(kind) as caught:
                    rpc.call('eth_call')
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(caught.exception.method, 'eth_call')
                self.assertNotIn('PRIVATE', str(caught.exception))

    def test_http_protocol_and_incomplete_read_bytes_are_not_exposed_or_retained(self):
        for error in [IncompleteRead(b'PRIVATE_PARTIAL_BODY', 100), HTTPException('PRIVATE_PROTOCOL')]:
            rpc = RPC('https://example.invalid/private?token=PRIVATE_URL')
            response = io.BytesIO()
            with self.subTest(kind=type(error).__name__), patch.object(rpc.opener, 'open', return_value=response), \
                 patch.object(response, 'read', side_effect=error):
                with self.assertRaises(RPCError) as caught:
                    rpc.call('eth_call')
                self.assertEqual(caught.exception.code, 'invalid_response')
                self.assertNotIn('PRIVATE', str(caught.exception))
                self.assertIsNone(caught.exception.__context__)

    def test_arbitrary_method_and_constructor_codes_cannot_enter_diagnostics(self):
        error = RPCError('compatible RuntimeError args', code='PRIVATE_CODE', method='PRIVATE_METHOD')
        self.assertEqual(error.args, ('compatible RuntimeError args',))
        self.assertEqual(error.diagnostics, {'code': 'unknown', 'method': None})
        error.diagnostics['code'] = 'PRIVATE_MUTATION'
        self.assertEqual(error.code, 'unknown')
        rpc = RPC('https://example.invalid')
        with patch.object(rpc.opener, 'open') as opened:
            with self.assertRaises(RPCError) as caught:
                rpc.call('PRIVATE_METHOD')
            opened.assert_not_called()
        self.assertEqual(caught.exception.diagnostics, {'code': 'invalid_request', 'method': None})

    def test_ordinary_upstream_and_local_still_deny_raw_broadcast(self):
        for local in [False, True]:
            rpc = RPC('http://127.0.0.1:1', local=local)
            with patch.object(rpc.opener, 'open') as opened:
                with self.assertRaises(RPCError) as caught:
                    rpc.call('eth_sendRawTransaction', ['PRIVATE_RAW'])
                opened.assert_not_called()
            self.assertEqual(caught.exception.code, 'invalid_request')
            self.assertNotIn('PRIVATE', json.dumps(caught.exception.diagnostics))

    def test_owned_trace_method_diagnostics_allow_fixed_mine_only(self):
        rpc = OwnedTraceRPC('http://127.0.0.1:1')
        with patch.object(rpc.opener, 'open', side_effect=TimeoutError('PRIVATE')):
            with self.assertRaises(RPCError) as caught:
                rpc.call('evm_mine')
        self.assertEqual(caught.exception.diagnostics, {'code': 'timeout', 'method': 'evm_mine'})


class LoopbackRPCFailureTests(unittest.TestCase):
    @contextmanager
    def server(self, mode):
        released = threading.Event()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                size = int(self.headers['Content-Length'])
                request = json.loads(self.rfile.read(size))
                if mode == 'timeout':
                    released.wait(1)
                self.send_response(503 if mode == 'http_error' else 200)
                if mode == 'truncated':
                    self.send_header('Content-Length', '9999')
                self.end_headers()
                body = (b'PRIVATE_HTTP_BODY' if mode == 'http_error' else b'PRIVATE_INVALID_JSON' if mode == 'invalid_response'
                        else json.dumps({'id': request['id'], 'error': {'code': 'PRIVATE_CODE', 'message': 'PRIVATE_BODY'}}).encode())
                if mode == 'truncated':
                    body = json.dumps({'id': request['id'], 'result': 'valid-JSON-in-truncated-body'}).encode()
                try:
                    self.wfile.write(body)
                except OSError:
                    pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .01})
        thread.start()
        try:
            yield server.server_port
        finally:
            released.set()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive(), 'owned HTTP server thread leaked')

    def test_actual_http_timeout_and_error_responses_have_safe_codes_and_closed_ports(self):
        for mode in ['timeout', 'http_error', 'invalid_response', 'rejected', 'truncated']:
            with self.subTest(mode=mode):
                with self.server(mode) as port:
                    rpc = RPC(f'http://127.0.0.1:{port}/private?token=PRIVATE_URL', timeout=.05 if mode == 'timeout' else 1)
                    with self.assertRaises(RPCError) as caught:
                        rpc.call('eth_call', ['PRIVATE_PARAM'])
                    self.assertEqual(caught.exception.code, 'invalid_response' if mode == 'truncated' else mode)
                    self.assertEqual(caught.exception.method, 'eth_call')
                    self.assertNotIn('PRIVATE', str(caught.exception))
                    self.assertNotIn('PRIVATE', json.dumps(caught.exception.diagnostics))
                    if mode == 'rejected':
                        self.assertIsInstance(caught.exception, RPCRejected)
                with socket.socket() as client:
                    client.settimeout(.1)
                    self.assertNotEqual(client.connect_ex(('127.0.0.1', port)), 0)


class NativeTraceDiagnosticTests(unittest.TestCase):
    def plan(self):
        return {'trace_version': '0.1.0', 'source': {'chain_id': 1, 'block_number': 19000000,
                'block_hash': '0x' + 'ab' * 32}, 'through_index': 0, 'skip_indices': []}

    def test_actual_native_cli_explains_rpc_kind_without_private_provider_values(self):
        from entrotter_engine import __main__ as cli
        with patch.dict(os.environ, {'ENTROTTER_RPC_URL': 'https://PRIVATE_URL'}), \
             patch('entrotter_engine.trace.load_trace', return_value=self.plan()), \
             patch('entrotter_engine.trace.capture_source', side_effect=RPCError('PRIVATE_ORIGINAL', code='timeout', method='evm_mine')), \
             patch('entrotter_engine.trace.AnvilSession') as node, \
             patch('entrotter_engine.trace.replay_branch') as replay:
            stderr, stdout = io.StringIO(), io.StringIO()
            with redirect_stderr(stderr), redirect_stdout(stdout):
                result = cli.main(['trace-run', 'unused-plan', '--native', '-o', 'unused-output'])
        self.assertEqual(result, 1)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn('Canonical trace RPC failed; original inputs/state may be unavailable. No fixture substitution.', stderr.getvalue())
        self.assertIn('[rpc_code=timeout; rpc_method=evm_mine]', stderr.getvalue())
        self.assertNotIn('PRIVATE', stderr.getvalue())
        node.assert_not_called()
        replay.assert_not_called()

    def test_native_boundary_ignores_forged_properties_and_raw_slot_values(self):
        from entrotter_engine.trace import run_trace_native
        from entrotter_engine.evm import ExecutionError
        class Forged(RPCError):
            @property
            def diagnostics(self):
                raise AssertionError('untrusted diagnostics property accessed')
            @property
            def code(self):
                return 'PRIVATE_CODE'
            @property
            def method(self):
                return 'PRIVATE_METHOD'
        errors = [Forged('PRIVATE_ORIGINAL', code={'private': 'PRIVATE_CODE'}, method=['PRIVATE_METHOD']),
                  Forged('PRIVATE_ORIGINAL', code='http_error', method='eth_getBlockByNumber')]
        class Uninitialized(RPCError):
            def __init__(self):
                RuntimeError.__init__(self, 'PRIVATE_UNINITIALIZED')
        errors.append(Uninitialized())
        for error, suffix in zip(errors, ['[rpc_code=unknown; rpc_method=unknown]',
                                         '[rpc_code=http_error; rpc_method=eth_getBlockByNumber]',
                                         '[rpc_code=unknown; rpc_method=unknown]']):
            with self.subTest(suffix=suffix), patch.dict(os.environ, {'ENTROTTER_RPC_URL': 'https://PRIVATE_URL'}), \
                 patch('entrotter_engine.trace.capture_source', side_effect=error):
                with self.assertRaises(ExecutionError) as caught:
                    run_trace_native(self.plan())
                self.assertTrue(str(caught.exception).endswith(suffix))
                self.assertNotIn('PRIVATE', str(caught.exception))

    def test_default_worker_failure_envelope_stays_exact(self):
        from entrotter_engine import _isolated_worker as worker
        stdin = type('Input', (), {'buffer': io.BytesIO(b'{}')})()
        stdout = io.StringIO()
        with patch.object(worker.sys, 'stdin', stdin), patch.object(worker.sys, 'stdout', stdout), \
             patch.object(worker, 'execute_request', side_effect=RPCError('PRIVATE', code='timeout', method='evm_mine')):
            self.assertEqual(worker.main(), 1)
        self.assertEqual(stdout.getvalue(), '{"error":"isolated_execution_failed"}')


if __name__ == '__main__':
    unittest.main()
