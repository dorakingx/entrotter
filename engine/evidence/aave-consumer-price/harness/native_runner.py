"""Prepared native original-protocol probe with read-only owned-node observations."""
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import socket
import sys
import time
from entrotter_engine import evm, trace
from entrotter_engine.artifact import canonical
from entrotter_engine.rpc import RPCError
from entrotter_engine.worker_protocol import execute_request
from evidence import Evidence, error_code
from cache_evidence import CacheEvidence
from consumer_observer import ConsumerObserver, SignalStop

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'run-001'
PROXY = '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419'
AGGREGATOR = '0xe62b71cf983019bff55bc83b48601ce8419650cc'
GETTERS = {'latestRoundData': '0xfeaf968c', 'aggregator': '0x245a7bfc'}
MAX_REPORT = 8 * 1024 * 1024


def category(error):
    return ('timeout' if isinstance(error, (TimeoutError, SignalStop)) else 'rpc_error' if isinstance(error, RPCError)
            else 'execution_error' if isinstance(error, evm.ExecutionError) else 'os_error' if isinstance(error, OSError)
            else 'value_error' if isinstance(error, ValueError) else 'other')


def persist(path, value, limit):
    raw = canonical(value)
    if len(raw) > limit:
        raise ValueError()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)


def decode(method, value):
    size = 160 if method == 'latestRoundData' else 32
    raw = trace.data(value, method, size=size)
    if method == 'aggregator':
        if any(raw[:12]):
            raise ValueError()
        return '0x' + raw[12:].hex()
    words = [raw[i:i + 32] for i in range(0, 160, 32)]
    return {'round_id': int.from_bytes(words[0], 'big'), 'answer': int.from_bytes(words[1], 'big', signed=True),
            'started_at': int.from_bytes(words[2], 'big'), 'updated_at': int.from_bytes(words[3], 'big'),
            'answered_in_round': int.from_bytes(words[4], 'big')}


def main():
    started = time.monotonic()
    nodes, ledger = [], []
    active = {'branch': None, 'deadline': None}
    result = {'scope': 'Owned native original protocol plus producer and read-only Aave price observations; not Docker, provider/code authentication, signed consumer action, profit or complete G1.',
              'status': 'failed', 'primary_error': None, 'observation_errors': [], 'cleanup_errors': [],
              'observations': [], 'report_sha256': None, 'request_id': None}
    original_session, original_replay, original_popen = trace.AnvilSession, trace.replay_branch, evm.subprocess.Popen
    original_cache = trace.ParentCache
    original_capture = trace.capture_source
    raw = (HERE / 'worker-request.json').read_bytes()
    prefix = json.loads((HERE / 'signed-prefix.json').read_text())
    evidence = Evidence(OUTPUT, sha256(raw).hexdigest(), prefix, category)
    cache_evidence = CacheEvidence(OUTPUT, category)
    caches = []
    consumer = ConsumerObserver(OUTPUT, sha256(raw).hexdigest())
    consumer_protocol_verified = False

    def save_ledger():
        persist(OUTPUT / 'owned-nodes.json', ledger, 16384)

    def secondary(kind, branch, phase, error):
        result[kind].append({'branch': branch, 'phase': phase, 'category': category(error)})

    def launch(command, *args, **kwargs):
        is_guardian = isinstance(command, list) and command[:2] == [sys.executable, str(Path(evm.__file__).with_name('_guardian.py'))]
        is_cache = command == [sys.executable, str(Path(trace.__file__).with_name('_parent_cache.py'))]
        if is_cache and (kwargs.get('start_new_session') is not True or cache_evidence.rows):
            raise ValueError()
        if is_guardian:
            if kwargs.get('start_new_session') is not True or len(ledger) >= 2:
                raise ValueError()
            port = int(command[command.index('--port') + 1])
            if not 1 <= port <= 65535 or active['branch'] not in ('baseline', 'candidate'):
                raise ValueError()
        process = original_popen(command, *args, **kwargs)
        if is_cache:
            try:
                cache_evidence.launched(process)
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                finally:
                    try:
                        process.wait(timeout=2)
                    finally:
                        for stream in (process.stdin, process.stdout):
                            if stream is not None:
                                stream.close()
                raise
        if is_guardian:
            ledger.append({'guardian_pid': process.pid, 'port': port, 'branch': active['branch'], 'closed': False})
            try:
                save_ledger()
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                finally:
                    try:
                        process.wait(timeout=2)
                    finally:
                        if process.stdin is not None:
                            process.stdin.close()
                raise
        return process

    class ObservedCache(original_cache):
        def __init__(self, *args, **kwargs):
            if caches:
                raise ValueError()
            evidence.stage = 'parent_cache_startup'
            super().__init__(*args, **kwargs)
            caches.append(self)

        def __enter__(self):
            value = super().__enter__()
            try:
                cache_evidence.started(self)
            except Exception as error:
                cache_evidence.failure('startup_snapshot', error)
            return value

        def __exit__(self, *exc):
            if not exc or exc[0] is None:
                evidence.stage = 'parent_cache_cleanup'
            try:
                return super().__exit__(*exc)
            finally:
                try:
                    cache_evidence.closed(self)
                except BaseException as error:
                    cache_evidence.failure('closure_snapshot', error)

    def observe(node, phase):
        row = {'branch': node.branch, 'phase': phase, 'values': {}, 'decoded': {}, 'errors': []}
        rpc, deadline = node.rpc, node.deadline
        if rpc is None:
            row['errors'].append({'method': 'none', 'category': 'execution_error'})
        else:
            original_timeout = rpc.timeout
            try:
                for method, params in [('eth_getBlockByNumber', ['latest', False]),
                                       ('latestRoundData', [{'to': PROXY, 'data': GETTERS['latestRoundData']}, 'latest']),
                                       ('aggregator', [{'to': PROXY, 'data': GETTERS['aggregator']}, 'latest'])]:
                    if deadline is None or deadline <= time.monotonic():
                        row['errors'].append({'method': method, 'category': 'timeout'})
                        break
                    rpc.timeout = min(2, deadline - time.monotonic())
                    try:
                        value = rpc.call('eth_call' if method in GETTERS else method, params)
                        if method == 'eth_getBlockByNumber':
                            if not isinstance(value, dict):
                                raise ValueError()
                            trace.data(value.get('hash'), 'head hash', size=32)
                            for field in ('number', 'timestamp'):
                                trace.quantity(value.get(field), field)
                            row['values']['head'] = {k: value[k] for k in ['number', 'hash', 'timestamp']}
                        else:
                            row['decoded'][method] = decode(method, value)
                            row['values'][method] = value
                    except Exception as error:
                        row['errors'].append({'method': method, 'category': category(error)})
            finally:
                rpc.timeout = original_timeout
        result['observations'].append(row)
        result['observation_errors'].extend({'branch': node.branch, 'phase': phase, **err} for err in row['errors'])
        persist(OUTPUT / 'observations.json', result['observations'], 65536)

    def observe_both(node, phase):
        observe(node, phase)
        consumer.observe(node.rpc, node.branch, phase, node.deadline)

    def record_closure(node):
        for row in ledger:
            if node.process is not None and row['guardian_pid'] == node.process.pid:
                row['guardian_returncode'] = node.process.poll()
                with socket.socket() as sock:
                    sock.settimeout(.2)
                    row['port_closed'] = sock.connect_ex(('127.0.0.1', row['port'])) != 0
                row['closed'] = row['guardian_returncode'] is not None and row['port_closed']
        save_ledger()

    class ObservedSession(original_session):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.branch, self.deadline = active['branch'], active['deadline']
            nodes.append(self)

        def __enter__(self):
            super().__enter__()
            previous_call, observed_call = evidence.rpc_wrapper(self.rpc, self.branch + '_replay')
            self.rpc.call = observed_call
            evidence.observing = True
            try:
                observe_both(self, 'before')
            except Exception as error:
                secondary('observation_errors', self.branch, 'before', error)
            finally:
                evidence.observing = False
            return self

        def __exit__(self, *exc):
            evidence.observing = True
            try:
                if exc and exc[0] is not None:
                    result['observations'].append({'branch': self.branch, 'phase': 'after', 'values': {}, 'decoded': {},
                                                   'errors': [{'method': 'none', 'category': 'skipped_primary_failure'}]})
                    consumer.skipped(self.branch, 'after')
                elif self.rpc is not None:
                    observe_both(self, 'after')
            except SignalStop:
                raise
            except Exception as error:
                secondary('observation_errors', self.branch, 'after', error)
            finally:
                evidence.observing = False
                try:
                    super().__exit__(*exc)
                except BaseException as error:
                    secondary('cleanup_errors', self.branch, 'session_exit', error)
                    if not exc or exc[0] is None:
                        raise
                finally:
                    try:
                        record_closure(self)
                    except BaseException as error:
                        secondary('cleanup_errors', self.branch, 'ledger', error)
                        if not isinstance(error, Exception) and (not exc or exc[0] is None):
                            raise

    def replay(captured, url, skipped, deadline):
        active.update(branch='baseline' if evidence.calls == 0 else 'candidate', deadline=deadline)
        return evidence.replay(original_replay, captured, url, skipped, deadline)

    def capture(plan, upstream, deadline):
        return evidence.capture(original_capture, plan, upstream, deadline)

    def expired(*args):
        raise SignalStop()

    signal.signal(signal.SIGALRM, expired)
    signal.signal(signal.SIGTERM, expired)
    signal.setitimer(signal.ITIMER_REAL, 180)
    try:
        result['request_id'] = sha256(raw).hexdigest()
        trace.AnvilSession, trace.replay_branch, evm.subprocess.Popen = ObservedSession, replay, launch
        trace.capture_source = capture
        trace.ParentCache = ObservedCache
        envelope = execute_request(raw)
        if envelope['request_id'] != result['request_id'] or not trace.verify_trace(envelope['report']):
            raise ValueError()
        report = envelope['report']
        frozen = json.loads((HERE / 'signed-prefix.json').read_text())
        source_bound = len(report['source']['inputs']) == len(frozen) and all(
            (a['index'], a['hash'], a['raw'], a['sender']) == (b['index'], b['hash'], b['raw_signed_transaction'], b['recovered_signer'])
            for a, b in zip(report['source']['inputs'], frozen))
        evidence.stage = 'protocol_snapshot'
        persist(OUTPUT / 'protocol-response.json', envelope, MAX_REPORT + 262144)
        persist(OUTPUT / 'report.json', report, MAX_REPORT)
        result['frozen_signed_prefix_bound'] = source_bound
        if not source_bound:
            raise ValueError()
        result.update(status='completed', report_sha256=sha256((OUTPUT / 'report.json').read_bytes()).hexdigest(),
                      baseline_verified=report['baseline_verified'], frozen_signed_prefix_bound=source_bound)
        rows = {(row['branch'], row['phase']): row for row in result['observations']}
        ready = len(rows) == 4 and all(not r['errors'] and set(r['decoded']) == set(GETTERS) for r in rows.values())
        result['owned_observations_complete'] = ready
        result['chosen_parent_and_update_proxy_identity_observed'] = ready and all(r['decoded']['aggregator'] == AGGREGATOR for r in rows.values())
        result['observed_round_ids'] = {f'{branch}_{phase}': row['decoded'].get('latestRoundData', {}).get('round_id') for (branch, phase), row in rows.items()}
        consumer_protocol_verified = report['baseline_verified'] is True and source_bound
        # Receipt verification and getter bytes are separate evidence. Owned view calls are not signed consumer actions.
    except BaseException as error:
        result['primary_error'] = category(error)
        result['primary_stage'] = evidence.stage
        result['primary_code'] = error_code(error)
    finally:
        trace.AnvilSession, trace.replay_branch, evm.subprocess.Popen = original_session, original_replay, original_popen
        trace.capture_source = original_capture
        trace.ParentCache = original_cache
        for cache in caches:
            try:
                if cache.process is not None and cache.process.poll() is None:
                    original_cache.__exit__(cache, TimeoutError, None, None)
            except BaseException as error:
                cache_evidence.failure('rescue_cleanup', error)
            finally:
                try:
                    cache_evidence.closed(cache)
                except BaseException as error:
                    cache_evidence.failure('final_closure_snapshot', error)
        for node in nodes:
            try:
                if node.process is not None and node.process.poll() is None:
                    original_session.__exit__(node, None, None, None)
            except BaseException as error:
                secondary('cleanup_errors', node.branch, 'rescue', error)
            finally:
                try:
                    record_closure(node)
                except BaseException as error:
                    secondary('cleanup_errors', node.branch, 'final_ledger', error)
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            persist(OUTPUT / 'observations.json', result['observations'], 65536)
        except BaseException as error:
            secondary('observation_errors', None, 'final_snapshot', error)
        try:
            consumer.save()
        except BaseException as error:
            # Terminal evidence only, after all owned cleanup; never start more RPC/replay.
            consumer.secondary.append({'category': category(error), 'code': 'consumer_final_snapshot_failed'})
        result['consumer_observation_secondary'] = consumer.secondary
        try:
            result['consumer_price_observation'] = consumer.classify(result['observations'], consumer_protocol_verified)
        except BaseException as error:
            result['consumer_price_observation'] = {'owned_read_only_price_observation_complete': False,
                'unproven_reasons': ['classification_error'], 'category': category(error)}
        result['consumer_observation_file'] = 'consumer-observations.json'
        result['evidence_snapshots'] = evidence.snapshots
        result['evidence_secondary_errors'] = evidence.secondary
        result['failure_stages'] = evidence.failures
        result['parent_cache'] = cache_evidence.rows
        result['cache_observation_errors'] = cache_evidence.secondary
        result['total_seconds'] = round(time.monotonic() - started, 6)
        persist(OUTPUT / 'result.json', result, 65536)
        print(json.dumps({'status': result['status'], 'primary_error': result['primary_error'], 'nodes': len(nodes),
                          'observation_errors': len(result['observation_errors']), 'cleanup_errors': len(result['cleanup_errors'])}))

if __name__ == '__main__':
    main()
