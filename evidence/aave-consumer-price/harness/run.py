"""Prepared-only bounded host. Run only after independent frozen-harness review."""
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import subprocess
import sys
import time
import certifi
from cache_evidence import finite_row, group_absent, port_closed
from evidence import atomic

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def observe_cache(output, cleanup_deadline):
    """Observe only. A stale grandchild PID is never signalled for cleanup."""
    path=output/'owned-cache.json'
    if not path.exists():
        return [], ['no_owned_cache_ledger_available']
    try:
        if path.stat().st_size>16384:raise ValueError()
        rows=json.loads(path.read_text())
        if type(rows) is not list or len(rows)>1:raise ValueError()
        rows=[finite_row(row) for row in rows]
    except BaseException:
        return [], ['owned_cache_ledger_error']
    errors=[]
    for row in rows:
        try:
            while True:
                try:os.kill(row['pid'],0); absent=False
                except ProcessLookupError:absent=True
                group=group_absent(row['pid'])
                remaining=cleanup_deadline-time.monotonic()
                closed=port_closed(row['port'],min(.2,remaining)) if row['port'] is not None and remaining>0 else None
                if absent and group and (closed is True or closed is None):break
                if time.monotonic()>=cleanup_deadline:break
                time.sleep(min(.05,max(0,cleanup_deadline-time.monotonic())))
            row.update(host_pid_absent=absent,host_group_absent=group,host_port_closed=closed)
            if not absent or not group:errors.append('owned_cache_process_remains')
            if closed is False:errors.append('owned_cache_port_remains_open')
            if closed is None:errors.append('owned_cache_port_unobserved' if row['port'] is None else 'owned_cache_observation_budget_exhausted')
        except BaseException:
            errors.append('owned_cache_observation_error')
    try:atomic(output/'host-cache-cleanup.json',rows,16384)
    except BaseException:errors.append('owned_cache_evidence_error')
    return rows,errors

def main():
    readiness=json.loads((HERE/'readiness.json').read_text())
    for path,digest in readiness['source_sha256'].items():
        if sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen source mismatch')
    if sha256(Path(certifi.where()).read_bytes()).hexdigest()!=readiness['CA_sha256']:raise ValueError('Frozen CA mismatch')
    binary=Path(readiness['anvil_binary_path'])
    if sha256(binary.read_bytes()).hexdigest()!=readiness['anvil_binary_sha256']:raise ValueError('Frozen binary mismatch')
    versions={v for v in re.findall(r'ENTROTTER_RPC_URL:\s*(\S+)',(ROOT/'.github/workflows/isolated.yml').read_text())}
    if len(versions)!=1:raise ValueError('Existing fixed source missing')
    url=versions.pop()  # Never copied into evidence/argv/stdout.
    output=HERE/'run-001';output.mkdir()  # Fail rather than replace any prior raw run.
    env={**os.environ,'ENTROTTER_RPC_URL':url,'SSL_CERT_FILE':certifi.where(),
        'PYTHONPATH':str(ROOT/'src'),'PATH':str(binary.parent)+os.pathsep+os.environ.get('PATH','')}
    process=None;body=bytearray();primary=None;cleanup=[];started=time.monotonic()
    def expired(*args):raise TimeoutError()
    signal.signal(signal.SIGTERM,expired);signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,190)
    try:
        process=subprocess.Popen([sys.executable,str(HERE/'native_runner.py')],stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True,env=env)
        os.set_blocking(process.stdout.fileno(),False)
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ)
            while selector.get_map():
                for key,_ in selector.select(.1):
                    raw=os.read(key.fd,4096)
                    if not raw:selector.unregister(key.fileobj)
                    else:
                        body.extend(raw)
                        if len(body)>16384:raise ValueError()
        process.wait(timeout=2)
        if process.returncode!=0:primary='child_exit'
    except BaseException as error:primary='timeout' if isinstance(error,TimeoutError) else 'host_error'
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        try:
            if process is not None:
                try:
                    if process.poll() is None:
                        try:os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                        process.wait(timeout=3)
                finally:
                    if process.stdout is not None:process.stdout.close()
        except BaseException:cleanup.append('client_cleanup_error')
        ledger=output/'owned-nodes.json'
        cleanup_deadline=time.monotonic()+10
        if ledger.exists():
            rows=[]
            try:
                if ledger.stat().st_size>16384:raise ValueError()
                rows=json.loads(ledger.read_text())
                if not isinstance(rows,list) or len(rows)>2:raise ValueError()
            except BaseException:
                cleanup.append('owned_ledger_error');rows=[]
            for row in rows:
                try:
                    pid,port=row['guardian_pid'],row['port']
                    if type(pid) is not int or pid<=1 or type(port) is not int or not 1<=port<=65535:raise ValueError()
                    if not row.get('closed'):
                        try:os.killpg(pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                        except OSError:cleanup.append('owned_group_cleanup_error')
                    end=min(cleanup_deadline,time.monotonic()+3)
                    while True:
                        with socket.socket() as sock:
                            sock.settimeout(.2);closed=sock.connect_ex(('127.0.0.1',port))!=0
                        if closed or time.monotonic()>=end:break
                        time.sleep(.05)
                    row['host_port_closed']=closed
                    if not closed:cleanup.append('owned_port_remains_open')
                except BaseException:
                    cleanup.append('owned_row_cleanup_error')
            try:(output/'host-owned-cleanup.json').write_text(json.dumps(rows,indent=2)+'\n')
            except BaseException:cleanup.append('owned_cleanup_evidence_error')
        else:
            cleanup.append('no_owned_ledger_available')
        try:cache_rows,cache_errors=observe_cache(output,cleanup_deadline)
        except BaseException:cache_rows,cache_errors=[],['owned_cache_observation_error']
        cleanup.extend(cache_errors)
        result={'host_primary_error':primary,'host_cleanup_errors':cleanup,'child_returncode':process.returncode if process else None,'stdout_bytes':len(body),'host_seconds':round(time.monotonic()-started,6),'native_only_no_Docker_quotas':True,'max_anvil_nodes':2,'max_fixed_cache_children':1,'host_observed_cache_rows':len(cache_rows),'cache_host_observation_scope':'PID/group/port observations after owner client stopped; pipe closure and aggregate stats are native-child observations only. No signals sent to cache grandchild identifiers.'}
        (output/'host-result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))

if __name__=='__main__':main()
