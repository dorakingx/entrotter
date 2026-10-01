"""Trusted failure-only CI probe; never a public arbitrary-code execution path.

The exact normal image/slot/quotas execute a fixed instrumented protocol call.
Only bounded enums and numeric error codes leave the container. Completion of
this diagnostic cannot replace the mandatory host-default replay success gate.
"""
import argparse
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import selectors
import signal
import ssl
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
import uuid

from entrotter_engine import isolated
from entrotter_engine.evm import ExecutionError
from entrotter_engine.rpc import RPCError, RPCRejected
from entrotter_engine.trace import load_trace
from entrotter_engine.worker_protocol import encode_trace_request

HOST_TIMEOUT = 190
MAX_OUTPUT = 16 * 1024
PHASES = {'input_validation', 'source_fetch', 'fork_startup', 'fork_parent_check',
          'parent_account', 'header_or_queue', 'mining', 'mined_header', 'receipt', 'complete'}
METHODS = {'none', 'other', 'web3_clientVersion', 'eth_chainId', 'eth_getBlockByNumber',
           'eth_getBalance', 'eth_getCode', 'eth_getTransactionReceipt', 'eth_call',
           'eth_getTransactionCount', 'eth_sendRawTransaction', 'evm_mine',
           'evm_setNextBlockTimestamp', 'evm_setBlockGasLimit', 'anvil_setCoinbase',
           'anvil_setNextBlockBaseFeePerGas', 'anvil_setNextBlockPrevRandao'}
TYPES = {'rpc_rejected', 'rpc_error', 'execution_error', 'value_error', 'timeout',
         'ssl_certificate', 'ssl_error', 'http_error', 'url_error', 'os_error', 'other'}
STATUSES = {'executed', 'skipped', 'nonce_conflict', 'rejected', 'not_mined'}


def error_summary(error):
    # Never call str/repr, copy args, or emit dynamic class names/provider data.
    queue, seen, types = [error], set(), []
    cert_code = http_code = None
    classes = [(RPCRejected, 'rpc_rejected'), (RPCError, 'rpc_error'),
               (ExecutionError, 'execution_error'), (ssl.SSLCertVerificationError, 'ssl_certificate'),
               (ssl.SSLError, 'ssl_error'), (HTTPError, 'http_error'), (URLError, 'url_error'),
               (TimeoutError, 'timeout'), (subprocess.TimeoutExpired, 'timeout'),
               (ValueError, 'value_error'), (OSError, 'os_error')]
    while queue and len(seen) < 8:
        current = queue.pop(0)
        if not isinstance(current, BaseException) or id(current) in seen:
            continue
        seen.add(id(current))
        kind = next((name for cls, name in classes if isinstance(current, cls)), 'other')
        if kind not in types: types.append(kind)
        if isinstance(current, ssl.SSLCertVerificationError):
            code = getattr(current, 'verify_code', None)
            if type(code) is int and 0 <= code <= 65535: cert_code = code
        if isinstance(current, HTTPError) and type(current.code) is int and 100 <= current.code <= 599:
            http_code = current.code
        queue.extend([current.__cause__, current.__context__])
        if isinstance(current, URLError) and isinstance(current.reason, BaseException):
            queue.append(current.reason)
    priority = ['ssl_certificate', 'ssl_error', 'http_error', 'timeout', 'rpc_rejected',
                'rpc_error', 'url_error', 'execution_error', 'value_error', 'os_error', 'other']
    category = next(kind for kind in priority if kind in types)
    return {'category': category, 'types': types, 'ssl_verify_code': cert_code, 'http_status': http_code}


def image_main():
    # This function's trusted source is embedded in the fixed image entrypoint.
    # The admitted JSON contains data only; no supplied code is evaluated.
    from entrotter_engine import trace
    from entrotter_engine.rpc import RPC
    from entrotter_engine.worker_protocol import execute_request
    raw = sys.stdin.buffer.read(262145)
    result = {'diagnostic_version': '0.1.0', 'request_id': sha256(raw).hexdigest(),
              'status': 'failed', 'last': {'phase': 'input_validation', 'branch': 'none',
              'method': 'none', 'transport': 'none'}, 'checkpoints': [], 'dropped_checkpoints': 0,
              'error': None, 'baseline_verified': None, 'protocol_verified': False,
              'candidate_statuses': [], 'authoritative_default_gate': False}
    scope, branch, mined = 'input_validation', 'none', False
    calls = 0
    original_rpc, original_capture, original_replay = RPC.call, trace.capture_source, trace.replay_branch
    def record(phase, method='none', transport='none'):
        row = {'phase': phase, 'branch': branch, 'method': method, 'transport': transport}
        result['last'] = row
        if not result['checkpoints'] or row != result['checkpoints'][-1]:
            if len(result['checkpoints']) < 32: result['checkpoints'].append(row)
            else: result['dropped_checkpoints'] = min(65535, result['dropped_checkpoints']+1)
    def capture(*args, **kwargs):
        nonlocal scope
        scope = 'source_fetch'; record(scope)
        return original_capture(*args, **kwargs)
    def replay(*args, **kwargs):
        nonlocal scope, branch, calls, mined
        calls += 1; branch = 'baseline' if calls == 1 else 'candidate'
        scope = 'fork_startup'; mined = False; record(scope)
        return original_replay(*args, **kwargs)
    def rpc_call(self, method, params=None):
        nonlocal mined
        transport = 'owned' if self.local else 'upstream'
        phase = scope
        if transport == 'owned':
            if method in {'web3_clientVersion', 'eth_chainId'}: phase = 'fork_startup'
            elif method == 'evm_mine': phase = 'mining'
            elif method == 'eth_getTransactionReceipt': phase = 'receipt'
            elif method == 'eth_getBlockByNumber': phase = 'mined_header' if mined else 'fork_parent_check'
            elif method == 'eth_getTransactionCount': phase = 'parent_account'
            else: phase = 'header_or_queue'
        record(phase, method if method in METHODS else 'other', transport)
        value = original_rpc(self, method, params)
        if method == 'evm_mine': mined = True
        return value
    def expired(*args): raise TimeoutError()
    signal.signal(signal.SIGALRM, expired); signal.signal(signal.SIGTERM, expired)
    signal.setitimer(signal.ITIMER_REAL, 180)
    try:
        if not raw or len(raw) > 262144: raise ValueError()
        RPC.call, trace.capture_source, trace.replay_branch = rpc_call, capture, replay
        # Unchanged primitive owns ONE shared150-second budget for both branches.
        envelope = execute_request(raw)
        if (set(envelope) != {'worker_version', 'request_id', 'report'}
                or envelope['request_id'] != result['request_id']
                or not trace.verify_trace(envelope['report'])): raise ValueError()
        result.update(status='completed', baseline_verified=envelope['report']['baseline_verified'],
            protocol_verified=True, candidate_statuses=[r['status'] for r in envelope['report']['candidate']['outcomes']])
        record('complete')
    except BaseException as error:
        result['error'] = error_summary(error)
    finally:
        RPC.call, trace.capture_source, trace.replay_branch = original_rpc, original_capture, original_replay
        signal.setitimer(signal.ITIMER_REAL, 0)
    body = json.dumps(result, separators=(',', ':')).encode()
    if len(body) > MAX_OUTPUT: raise ValueError()
    sys.stdout.buffer.write(body); sys.stdout.buffer.flush()


def program():
    # Source comes only from this reviewed helper, never a plan/env/file argument.
    imports = ('import json,sys,signal,ssl,subprocess\nfrom hashlib import sha256\n'
               'from urllib.error import HTTPError,URLError\n'
               'from entrotter_engine.evm import ExecutionError\n'
               'from entrotter_engine.rpc import RPCError,RPCRejected\n')
    return (imports + 'MAX_OUTPUT='+str(MAX_OUTPUT)+'\nMETHODS='+repr(METHODS)+'\n' +
            inspect.getsource(error_summary) + '\n' + inspect.getsource(image_main) + '\nimage_main()\n')


def validate_response(value, request_id):
    fields = {'diagnostic_version', 'request_id', 'status', 'last', 'checkpoints',
              'dropped_checkpoints', 'error', 'baseline_verified', 'protocol_verified',
              'candidate_statuses', 'authoritative_default_gate'}
    if not isinstance(value, dict) or set(value) != fields: raise ValueError()
    if value['diagnostic_version'] != '0.1.0' or value['request_id'] != request_id: raise ValueError()
    if value['status'] not in {'completed', 'failed'} or value['authoritative_default_gate'] is not False: raise ValueError()
    if type(value['dropped_checkpoints']) is not int or not 0 <= value['dropped_checkpoints'] <= 65535: raise ValueError()
    def checkpoint(row):
        if not isinstance(row, dict) or set(row) != {'phase', 'branch', 'method', 'transport'}: raise ValueError()
        if row['phase'] not in PHASES or row['branch'] not in {'none', 'baseline', 'candidate'}: raise ValueError()
        if row['method'] not in METHODS or row['transport'] not in {'none', 'owned', 'upstream'}: raise ValueError()
    checkpoint(value['last'])
    if not isinstance(value['checkpoints'], list) or len(value['checkpoints']) > 32: raise ValueError()
    for row in value['checkpoints']: checkpoint(row)
    if not isinstance(value['candidate_statuses'], list) or len(value['candidate_statuses']) > 32: raise ValueError()
    if any(status not in STATUSES for status in value['candidate_statuses']): raise ValueError()
    if type(value['protocol_verified']) is not bool: raise ValueError()
    if value['status'] == 'completed':
        if value['error'] is not None or type(value['baseline_verified']) is not bool or value['protocol_verified'] is not True: raise ValueError()
    else:
        if value['baseline_verified'] is not None or value['protocol_verified'] is not False or value['candidate_statuses']: raise ValueError()
        error = value['error']
        if not isinstance(error, dict) or set(error) != {'category', 'types', 'ssl_verify_code', 'http_status'}: raise ValueError()
        if error['category'] not in TYPES or not isinstance(error['types'], list) or not 1 <= len(error['types']) <= 8: raise ValueError()
        if any(kind not in TYPES for kind in error['types']): raise ValueError()
        for key, lower, upper in [('ssl_verify_code', 0, 65535), ('http_status', 100, 599)]:
            if error[key] is not None and (type(error[key]) is not int or not lower <= error[key] <= upper): raise ValueError()
    return value


def run_diagnostic(plan):
    payload = encode_trace_request(plan); request_id = sha256(payload).hexdigest()
    owner = uuid.uuid4().hex
    result = {'diagnostic_version': '0.1.0', 'request_id': request_id, 'worker': None,
              'host_error': None, 'cleanup_error': None, 'docker_exit_code': None, 'cleanup_verified': False}
    with isolated.client() as prefix, tempfile.TemporaryFile() as stdin:
        isolated.verify_daemon(prefix)
        if isolated._slot(prefix) is not None:
            raise isolated.WorkerBusy('Diagnostic shared slot is occupied')
        args = isolated.worker_args(prefix, os.environ.get('ENTROTTER_WORKER_IMAGE', ''), isolated.WORKER_NAME, fork=True)
        args[len(prefix)+1:len(prefix)+1] = ['--label', isolated.OWNER_LABEL+'='+owner]
        args = [*args[:-1], '--entrypoint=python3', args[-1], '-c', program()]
        stdin.write(payload); stdin.seek(0)
        process = None
        try:
            process = subprocess.Popen(args, stdin=stdin, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, start_new_session=True)
            deadline = time.monotonic()+HOST_TIMEOUT; output = bytearray()
            if process.stdout is None: raise ValueError()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline-time.monotonic()
                    if remaining <= 0: raise TimeoutError()
                    for key, _ in selector.select(min(.1, remaining)):
                        chunk = os.read(key.fd, 8192)
                        if not chunk: selector.unregister(key.fileobj)
                        else:
                            output.extend(chunk)
                            if len(output) > MAX_OUTPUT: raise ValueError()
            result['docker_exit_code'] = process.wait(timeout=max(.001, deadline-time.monotonic()))
            if result['docker_exit_code'] != 0: raise ExecutionError()
            result['worker'] = validate_response(json.loads(output), request_id)
        except BaseException as error:
            result['host_error'] = error_summary(error)
        finally:
            try:
                if process is not None:
                    try:
                        try: os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                        process.wait(timeout=3)
                    finally:
                        if process.stdout is not None: process.stdout.close()
            except BaseException as error:
                result['cleanup_error'] = error_summary(error)
            finally:
                try:
                    isolated._cleanup(prefix, owner)
                    result['cleanup_verified'] = result['cleanup_error'] is None
                except BaseException as error:
                    result['cleanup_error'] = error_summary(error)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan'); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    # Data-only regular-file loader retains256KiB bounds; no env/code selection.
    try:
        result = run_diagnostic(load_trace(args.plan))
    except BaseException as error:
        result = {'diagnostic_version': '0.1.0', 'worker': None,
                  'host_error': error_summary(error), 'cleanup_verified': None}
    body = json.dumps(result, indent=2)+'\n'
    if len(body.encode()) > MAX_OUTPUT: raise ValueError()
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(body)
    print(json.dumps({'diagnostic': 'recorded', 'cleanup_verified': result['cleanup_verified']}))
    return 0 if result['cleanup_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
