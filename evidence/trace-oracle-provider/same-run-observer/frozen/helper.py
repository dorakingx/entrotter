"""Trusted failure-only CI probe; never a public arbitrary-code execution path.

The exact normal image/slot/quotas execute a fixed instrumented protocol call.
Only bounded enums and numeric error codes leave the container. Completion of
this diagnostic cannot replace the mandatory host-default replay success gate.
"""
import argparse
from collections import Counter
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import re
import selectors
import signal
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from urllib.error import HTTPError, URLError
import uuid

from entrotter_engine import isolated, _guardian
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


MAX_LINE = 8192
SCAN_BYTES = 131072
SATURATION = 65535
ANSI = re.compile(rb'\x1b\[[0-9;]*m')
HEADER = re.compile(rb'^\d{4}-\d{2}-\d{2}T[0-9:.]+Z\s+(TRACE|WARN)\s+backend:\s+(.*)$')
EVENTS = {
    b'db error for tx ': 'account_database_skip',
    b'tx execution error, skipping ': 'execution_skip',
    b'Skipping invalid tx [': 'invalid_skip',
    b'Skipping invalid tx execution [': 'validation_skip',
    b'block gas limit exhausting, skipping transaction': 'block_gas_skip',
}


class Parser:
    def __init__(self, expected_hashes):
        self.expected = {x.encode(): i for i, x in enumerate(expected_hashes)}
        self.events = Counter()
        self.indices = Counter()
        self.formats = Counter()
        self.reader_errors = Counter()
        self.bytes = self.scanned = self.overlong = self.unbound = self.partial = 0
        self.eof = self.stop_without_eof = 0
        self.lock = threading.Lock()
        self.stop = threading.Event()

    def line(self, line):
        clean = ANSI.sub(b'', line)
        match = HEADER.fullmatch(clean)
        if not match:
            return
        self.formats['timestamp_level_backend'] += 1
        if clean != line: self.formats['ansi_present'] += 1
        body = match[2]
        for prefix, event in EVENTS.items():
            if not body.startswith(prefix): continue
            hashes = re.findall(rb'0x[0-9a-f]{64}', body[:len(prefix)+70])
            if event == 'block_gas_skip':
                self.events[event] += 1
            elif hashes and hashes[0] in self.expected:
                self.events[event] += 1
                self.indices[self.expected[hashes[0]]] += 1
            else:
                self.unbound += 1
            return

    def drain(self, stream):
        pending = bytearray(); discarding = False
        stopping_deadline = None
        eof = False
        try:
            os.set_blocking(stream.fileno(), False)
            with selectors.DefaultSelector() as selector:
                selector.register(stream,selectors.EVENT_READ)
                while True:
                    if self.stop.is_set() and stopping_deadline is None:
                        stopping_deadline=time.monotonic()+.2
                    if stopping_deadline is not None and time.monotonic()>=stopping_deadline:break
                    ready=selector.select(.05)
                    if not ready:
                        if self.stop.is_set():break
                        continue
                    chunk = os.read(stream.fileno(), 4096)
                    if not chunk:
                        eof=True;break
                    with self.lock:
                        self.bytes = min(2**31-1, self.bytes+len(chunk))
                        remaining = SCAN_BYTES-self.scanned
                        if remaining <= 0: continue  # Still drain, never block child.
                        scanned = chunk[:remaining]; self.scanned += len(scanned)
                        for byte in scanned:
                            if byte == 10:
                                if not discarding: self.line(bytes(pending))
                                pending.clear(); discarding = False
                            elif not discarding:
                                pending.append(byte)
                                if len(pending) > MAX_LINE:
                                    self.overlong += 1; pending.clear(); discarding = True
        except BaseException as error:
            category='os_error' if isinstance(error,OSError) else 'value_error' if isinstance(error,ValueError) else 'other'
            with self.lock:self.reader_errors[category]+=1
        finally:
            with self.lock:
                self.partial+=bool(pending or discarding)
                self.eof+=eof
                self.stop_without_eof+=not eof and self.stop.is_set()
            try:stream.close()
            except BaseException:
                with self.lock:self.reader_errors['close_error']+=1

    def finite(self):
        cap = lambda n: min(SATURATION, n)
        return {'events': {k:cap(n) for k,n in self.events.items()},
            'input_indices': {str(k):cap(n) for k,n in self.indices.items()},
            'formatter': {k:cap(n) for k,n in self.formats.items()},
            'raw_bytes_drained': self.bytes, 'raw_bytes_scanned': self.scanned,
            'scan_cap_exhausted':self.bytes>self.scanned,
            'partial_lines_discarded':cap(self.partial),
            'reader_errors':{k:cap(n) for k,n in self.reader_errors.items()},
            'eof_observed_streams':min(2,self.eof),
            'stop_before_eof_streams':min(2,self.stop_without_eof),
            'complete_log_scan':self.eof==2 and not self.reader_errors and self.bytes==self.scanned and not self.partial and not self.overlong,
            'overlong_lines_discarded': cap(self.overlong),
            'unbound_events': cap(self.unbound), 'raw_logs_retained': False,
            'provider_or_state_cause_attested': False}


def guardian_main():
    # All arguments are constructed by the trusted diagnostic, never a public caller.
    request_id, branch, hashes, lifetime = sys.argv[1:5]
    if not re.fullmatch('[0-9a-f]{64}', request_id) or branch not in {'baseline','candidate'}:
        return 2
    hashes=json.loads(hashes)
    if not isinstance(hashes,list) or not 1 <= len(hashes) <= 32 or any(not re.fullmatch('0x[0-9a-f]{64}',x) for x in hashes):
        return 2
    lifetime=float(lifetime)
    if not .1 <= lifetime <= 150: return 2
    parser=Parser(hashes); threads=[]; processes=[]
    original=subprocess.Popen
    def launch(command, **kwargs):
        # Preserve guardian argv/stdin/signals/terminate/kill behavior.
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, 'RUST_LOG':'backend'})
        process=original(command,**kwargs);processes.append(process)
        try:
            for stream in [process.stdout,process.stderr]:
                thread=threading.Thread(target=parser.drain,args=(stream,),daemon=True)
                thread.start();threads.append(thread)
        except BaseException:
            launch_errors['reader_start_error']+=1
            try:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill();process.wait(timeout=2)
            except BaseException:launch_errors['child_cleanup_error']+=1
            finally:
                parser.stop.set()
                end=time.monotonic()+.5
                for thread in threads:thread.join(timeout=max(0,end-time.monotonic()))
                for stream in [process.stdout,process.stderr]:
                    if not stream.closed:
                        try:stream.close()
                        except BaseException:launch_errors['stream_close_error']+=1
            raise
        return process
    _guardian.subprocess.Popen=launch
    result=None; supervisor_error=None; launch_errors=Counter()
    try:
        result=_guardian.supervise(sys.argv[5:],lifetime)
        return result
    except BaseException as error:
        supervisor_error='os_error' if isinstance(error,OSError) else 'value_error' if isinstance(error,ValueError) else 'other'
        return 1
    finally:
        _guardian.subprocess.Popen=original
        parser.stop.set()
        end=time.monotonic()+.5
        for thread in threads:thread.join(timeout=max(0,end-time.monotonic()))
        record={'observer_version':'0.1.0','request_id':request_id,'branch':branch,
            'guardian_result':result,'node_returncodes':[p.poll() for p in processes],
            'supervisor_error':supervisor_error,'launch_errors':dict(launch_errors),
            'reader_threads_closed':all(not t.is_alive() for t in threads),
            'stream_descriptors_closed':all(p.stdout.closed and p.stderr.closed for p in processes),
            **parser.finite()}
        data=json.dumps(record,separators=(',',':')).encode()
        if len(data)>4096:raise ValueError('Finite observer output exceeded bound')
        sys.stdout.buffer.write(data);sys.stdout.buffer.flush()



def guardian_program():
    imports = ('from collections import Counter\n'
        'import json,os,re,selectors,subprocess,sys,threading,time\n'
        'from entrotter_engine import _guardian\n')
    constants = ('MAX_LINE='+repr(MAX_LINE)+'\nSCAN_BYTES='+repr(SCAN_BYTES)+
        '\nSATURATION='+repr(SATURATION)+'\nANSI=re.compile('+repr(ANSI.pattern)+
        ')\nHEADER=re.compile('+repr(HEADER.pattern)+')\nEVENTS='+repr(EVENTS)+'\n')
    return imports+constants+inspect.getsource(Parser)+'\n'+inspect.getsource(guardian_main)+'\nsys.exit(guardian_main())\n'


def validate_observer_row(row, request_id, branch, count):
    fields={'observer_version','request_id','branch','guardian_result','node_returncodes',
        'supervisor_error','launch_errors','reader_threads_closed','stream_descriptors_closed',
        'events','input_indices','formatter','raw_bytes_drained','raw_bytes_scanned',
        'scan_cap_exhausted','partial_lines_discarded','reader_errors','eof_observed_streams',
        'stop_before_eof_streams','complete_log_scan','overlong_lines_discarded','unbound_events',
        'raw_logs_retained','provider_or_state_cause_attested'}
    if not isinstance(row,dict) or set(row)!=fields:raise ValueError()
    if row['observer_version']!='0.1.0' or row['request_id']!=request_id or row['branch']!=branch:raise ValueError()
    def integer(value,maximum):
        if type(value) is not int or not 0<=value<=maximum:raise ValueError()
    def counters(value,allowed):
        if not isinstance(value,dict) or not set(value)<=allowed:raise ValueError()
        for number in value.values():integer(number,65535)
    counters(row['events'],{'account_database_skip','execution_skip','invalid_skip','validation_skip','block_gas_skip'})
    counters(row['input_indices'],{str(i) for i in range(count)})
    counters(row['formatter'],{'timestamp_level_backend','ansi_present'})
    counters(row['reader_errors'],{'os_error','value_error','other','close_error'})
    counters(row['launch_errors'],{'reader_start_error','child_cleanup_error','stream_close_error'})
    for key in ['partial_lines_discarded','overlong_lines_discarded','unbound_events']:integer(row[key],65535)
    integer(row['raw_bytes_drained'],2**31-1);integer(row['raw_bytes_scanned'],131072)
    if row['raw_bytes_scanned']>row['raw_bytes_drained']:raise ValueError()
    integer(row['eof_observed_streams'],2);integer(row['stop_before_eof_streams'],2)
    if row['eof_observed_streams']+row['stop_before_eof_streams']>2:raise ValueError()
    for key in ['reader_threads_closed','stream_descriptors_closed','scan_cap_exhausted','complete_log_scan']:
        if type(row[key]) is not bool:raise ValueError()
    if row['scan_cap_exhausted']!=(row['raw_bytes_drained']>row['raw_bytes_scanned']):raise ValueError()
    complete=(row['eof_observed_streams']==2 and not row['reader_errors'] and
        row['raw_bytes_drained']==row['raw_bytes_scanned'] and not row['partial_lines_discarded'] and not row['overlong_lines_discarded'])
    if row['complete_log_scan']!=complete:raise ValueError()
    if row['raw_logs_retained'] is not False or row['provider_or_state_cause_attested'] is not False:raise ValueError()
    if row['supervisor_error'] not in {None,'os_error','value_error','other'}:raise ValueError()
    if row['guardian_result'] is not None and (type(row['guardian_result']) is not int or not -128<=row['guardian_result']<=255):raise ValueError()
    codes=row['node_returncodes']
    if not isinstance(codes,list) or len(codes)>1:raise ValueError()
    if any(code is not None and (type(code) is not int or not -128<=code<=255) for code in codes):raise ValueError()
    return row


def collect_observer_rows(processes, request_id, count):
    rows=[];discarded=0;errors=[]
    deadline=time.monotonic()+3
    def record(phase,error):
        if len(errors)<8:errors.append({'phase':phase,'category':error_summary(error)['category']})
    for branch,process in processes:
        try:
            if process.stdin is not None and not process.stdin.closed:process.stdin.close()
            if process.poll() is None:
                try:process.wait(timeout=max(.001,min(.5,deadline-time.monotonic())))
                except subprocess.TimeoutExpired:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait(timeout=max(.001,min(.5,deadline-time.monotonic())))
            if process.stdout is None:raise ValueError()
            body=bytearray()
            os.set_blocking(process.stdout.fileno(),False)
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ)
                while selector.get_map():
                    if time.monotonic()>=deadline:raise TimeoutError()
                    for key,_ in selector.select(.05):
                        chunk=os.read(key.fd,4096)
                        if not chunk:selector.unregister(key.fileobj)
                        else:
                            body.extend(chunk)
                            if len(body)>4096:raise ValueError()
            try:row=validate_observer_row(json.loads(body),request_id,branch,count)
            except BaseException as error:
                record('validation',error);discarded+=1
            else:rows.append(row)
        except BaseException as error:
            record('pipe_or_process',error);discarded+=1
        finally:
            try:
                # This is the uniquely owned guardian session, including a
                # descendant retaining its output after the direct child exits.
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                if process.poll() is None:
                    process.wait(timeout=.5)
            except BaseException as error:record('cleanup',error)
            finally:
                try:
                    if process.stdout is not None:process.stdout.close()
                except BaseException as error:record('cleanup',error)
    return rows,discarded,errors


def image_main():
    # This function's trusted source is embedded in the fixed image entrypoint.
    # The admitted JSON contains data only; no supplied code is evaluated.
    from entrotter_engine import trace, evm
    from entrotter_engine.rpc import RPC
    from entrotter_engine.worker_protocol import execute_request
    raw = sys.stdin.buffer.read(262145)
    result = {'diagnostic_version': '0.1.0', 'request_id': sha256(raw).hexdigest(),
              'status': 'failed', 'last': {'phase': 'input_validation', 'branch': 'none',
              'method': 'none', 'transport': 'none'}, 'checkpoints': [], 'dropped_checkpoints': 0,
              'error': None, 'baseline_verified': None, 'protocol_verified': False,
              'candidate_statuses': [], 'authoritative_default_gate': False,
              'observed_input_count':0,'observer_rows':[], 'discarded_observer_rows':0,'observer_errors':[]}
    scope, branch, mined = 'input_validation', 'none', False
    calls = 0
    original_rpc, original_capture, original_replay = RPC.call, trace.capture_source, trace.replay_branch
    original_popen=subprocess.Popen
    observer_processes=[];hashes=[]
    def record(phase, method='none', transport='none'):
        row = {'phase': phase, 'branch': branch, 'method': method, 'transport': transport}
        result['last'] = row
        if not result['checkpoints'] or row != result['checkpoints'][-1]:
            if len(result['checkpoints']) < 32: result['checkpoints'].append(row)
            else: result['dropped_checkpoints'] = min(65535, result['dropped_checkpoints']+1)
    def capture(*args, **kwargs):
        nonlocal scope,hashes
        scope = 'source_fetch'; record(scope)
        captured=original_capture(*args, **kwargs)
        hashes=[row['hash'] for row in captured['inputs']]
        result['observed_input_count']=len(hashes)
        return captured
    def replay(*args, **kwargs):
        nonlocal scope, branch, calls, mined
        calls += 1; branch = 'baseline' if calls == 1 else 'candidate'
        scope = 'fork_startup'; mined = False; record(scope)
        return original_replay(*args, **kwargs)
    def launch_observed(command,*args,**kwargs):
        if not isinstance(command,list) or command[:2]!=[sys.executable,str(Path(evm.__file__).with_name('_guardian.py'))]:
            return original_popen(command,*args,**kwargs)
        if branch not in {'baseline','candidate'} or not hashes or len(observer_processes)>=2:raise ValueError()
        if kwargs.get('start_new_session') is not True:raise ValueError()
        observed=[command[0],'-c',GUARDIAN_PROGRAM,result['request_id'],branch,json.dumps(hashes),command[2],*command[3:]]
        kwargs.update(stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        process=original_popen(observed,*args,**kwargs)
        observer_processes.append((branch,process));return process
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
        value=json.loads(raw)
        if not isinstance(value,dict) or set(value)!={'worker_version','trace'} or value['worker_version']!='1':raise ValueError()
        RPC.call, trace.capture_source, trace.replay_branch = rpc_call, capture, replay
        evm.subprocess.Popen=launch_observed
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
        evm.subprocess.Popen=original_popen
        try:
            rows,discarded,errors=collect_observer_rows(observer_processes,result['request_id'],len(hashes))
            result.update(observer_rows=rows,discarded_observer_rows=discarded,observer_errors=errors)
        except BaseException as error:
            result.update(discarded_observer_rows=len(observer_processes),
                observer_errors=[{'phase':'cleanup','category':error_summary(error)['category']}])
        finally:signal.setitimer(signal.ITIMER_REAL, 0)
    body = json.dumps(result, separators=(',', ':')).encode()
    if len(body) > MAX_OUTPUT: raise ValueError()
    sys.stdout.buffer.write(body); sys.stdout.buffer.flush()


def program():
    # Source comes only from this reviewed helper, never a plan/env/file argument.
    imports = ('import json,sys,signal,ssl,subprocess,os,time,selectors\nfrom hashlib import sha256\nfrom pathlib import Path\n'
               'from urllib.error import HTTPError,URLError\n'
               'from entrotter_engine.evm import ExecutionError\n'
               'from entrotter_engine.rpc import RPCError,RPCRejected\n')
    return (imports + 'MAX_OUTPUT='+str(MAX_OUTPUT)+'\nMETHODS='+repr(METHODS)+'\nGUARDIAN_PROGRAM='+repr(guardian_program())+'\n' +
            inspect.getsource(error_summary) + '\n' + inspect.getsource(validate_observer_row)+'\n'+
            inspect.getsource(collect_observer_rows)+'\n'+inspect.getsource(image_main) + '\nimage_main()\n')


def validate_response(value, request_id, expected_input_count=None):
    fields = {'diagnostic_version', 'request_id', 'status', 'last', 'checkpoints',
              'dropped_checkpoints', 'error', 'baseline_verified', 'protocol_verified',
              'candidate_statuses', 'authoritative_default_gate','observed_input_count',
              'observer_rows','discarded_observer_rows','observer_errors'}
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
    count=value['observed_input_count']
    if type(count) is not int or not 0<=count<=32:raise ValueError()
    if expected_input_count is not None and count not in {0,expected_input_count}:raise ValueError()
    rows=value['observer_rows'];discarded=value['discarded_observer_rows']
    if not isinstance(rows,list) or len(rows)>2 or type(discarded) is not int or not 0<=discarded<=2 or len(rows)+discarded>2:raise ValueError()
    if count==0 and (rows or discarded):raise ValueError()
    branches=[]
    for row in rows:
        if not isinstance(row,dict) or row.get('branch') not in {'baseline','candidate'}:raise ValueError()
        branch=row['branch']
        validate_observer_row(row,request_id,branch,count);branches.append(branch)
    if branches not in [[],['baseline'],['candidate'],['baseline','candidate']]:raise ValueError()
    errors=value['observer_errors']
    if not isinstance(errors,list) or len(errors)>8:raise ValueError()
    for error in errors:
        if not isinstance(error,dict) or set(error)!={'phase','category'}:raise ValueError()
        if error['phase'] not in {'validation','pipe_or_process','cleanup'} or error['category'] not in TYPES:raise ValueError()
    if value['status'] == 'completed':
        if value['error'] is not None or type(value['baseline_verified']) is not bool or value['protocol_verified'] is not True: raise ValueError()
        if count==0 or expected_input_count is not None and count!=expected_input_count:raise ValueError()
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
            result['worker'] = validate_response(json.loads(output), request_id,plan['through_index']+1)
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
