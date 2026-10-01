import json, os, subprocess, sys, tempfile, time, uuid
from pathlib import Path
sys.path.insert(0, 'scripts')
import build_worker as b
code = 'import time; print("ENTROTTER_DEADLINE_' + uuid.uuid4().hex + '", flush=True); time.sleep(60)'
started=time.monotonic()
with b.client() as prefix, tempfile.TemporaryDirectory(prefix='entrotter-deadline-probe-') as directory:
    root=Path(directory)
    (root/'Dockerfile').write_text('FROM cgr.dev/chainguard/python@sha256:011e73b4e30e0fe9407a42b82a920b4fa13ebc0bf029a48b714f950df254ca20\nRUN '+json.dumps(['python3','-c',code])+'\n')
    def probe(prefix, root, archive):
        b.run_build_command([*prefix,'build','--no-cache','--progress=plain',str(root)],own_session=False)
    b.prepare_image=probe
    try:
        with b.build_deadline(10):
            b.prepare_supervised(prefix,root,None,10)
    except ValueError as error:
        assert 'deadline' in str(error),error
    else:
        raise AssertionError('Stalled build did not time out')
elapsed=time.monotonic()-started
scan='''import json,os,sys
from pathlib import Path
expected=('python3'+chr(0)+'-c'+chr(0)+sys.argv[1]+chr(0)).encode()
found=[]
for path in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        if path.read_bytes()==expected: found.append(int(path.parent.name))
    except (FileNotFoundError,PermissionError,ProcessLookupError): pass
print(json.dumps(found))
'''
result=subprocess.run(['colima','ssh','--profile','entrotter','--','/usr/bin/python3','-c',scan,code],capture_output=True,text=True,timeout=15,check=True)
remaining=json.loads(result.stdout)
report={'deadline_seconds':10,'elapsed_seconds':round(elapsed,3),'daemon_probe_processes_remaining':remaining,'scope':'Actual isolated BuildKit RUN sleeping for 60 seconds; local Docker client lifetime/session termination'}
Path('evidence/worker-build-deadline/docker-timeout.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
assert elapsed<13 and not remaining, report
