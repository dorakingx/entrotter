"""Actual trusted diagnostic protocol entrypoint; owned synthetic native only."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_trace_oracle import ReadOnlyFaultProxy, TraceOracleProviderIntegrationTests as Case, assert_port_closed
from entrotter_engine.trace import verify_trace
from entrotter_engine.worker_protocol import encode_trace_request
spec=importlib.util.spec_from_file_location('frozen_integrated_diagnostic',HERE/'helper.py')
diag=importlib.util.module_from_spec(spec);sys.modules[spec.name]=diag;spec.loader.exec_module(diag)


def main():
    output=HERE/'results';output.mkdir()  # Unique run: never replace prior evidence.
    readiness=json.loads((HERE/'readiness.json').read_text())
    for relative,digest in readiness['source_sha256'].items():
        assert sha256((ROOT/relative).read_bytes()).hexdigest()==digest
    finite={'scope':'Integrated trusted diagnostic execute_request on owned native synthetic source; not normal default host dispatch, Docker, historical cause or provider/state attestation.',
        'startup_readiness_sha256':sha256((HERE/'readiness.json').read_bytes()).hexdigest(),
        'source_sha256':readiness['source_sha256'],'cases':{},'fixed_log_filter':'backend'}
    try:
        Case.setUpClass()
        assert Case.parent_value==10
        (output/'unobserved-original-report.json').write_text(json.dumps(Case.report,indent=2)+'\n')
        payload=encode_trace_request(Case.plan)
        (output/'worker-request.json').write_bytes(payload)
        finite['unobserved_original_report_sha256']=sha256((output/'unobserved-original-report.json').read_bytes()).hexdigest()
        finite['worker_request_sha256']=sha256(payload).hexdigest()
        finite['unobserved_original_runtime_seconds']=Case.report['runtime_seconds']
        for label,fault in [('observed_control','none'),('observed_missing_storage','eth_getStorageAt')]:
            before={t.ident for t in threading.enumerate()}
            proxy=ReadOnlyFaultProxy(Case.source.rpc.url,fault,Case.plan['source']['block_number']-1)
            proxy_errors=[];proxy.server.handle_error=lambda *args:proxy_errors.append('handler_error')
            report_path=output/(label+'-report.json');nodes_path=output/(label+'-nodes.json')
            bootstrap=('import json,socket\nfrom pathlib import Path\nfrom urllib.parse import urlsplit\n'
                'from entrotter_engine import evm,worker_protocol\n'
                'original_exit=evm.AnvilSession.__exit__\nnode_rows=[]\n'
                'def observed_exit(self,*args):\n'
                ' original_exit(self,*args)\n'
                ' closed=None\n'
                ' if self.rpc is not None:\n'
                '  with socket.socket() as sock:\n'
                "   sock.settimeout(.2);closed=sock.connect_ex(('127.0.0.1',urlsplit(self.rpc.url).port))!=0\n"
                " node_rows.append({'port_closed':closed,'guardian_returncode':self.process.poll() if self.process is not None else None})\n"
                ' Path('+repr(str(nodes_path))+').write_text(json.dumps(node_rows))\n'
                'evm.AnvilSession.__exit__=observed_exit\n'
                'original_execute=worker_protocol.execute_request\n'
                'def execute_and_preserve(raw):\n'
                ' value=original_execute(raw)\n'
                ' Path('+repr(str(report_path))+').write_text(json.dumps(value["report"],indent=2)+"\\n")\n'
                ' return value\nworker_protocol.execute_request=execute_and_preserve\n')
            assert payload==encode_trace_request(Case.plan)
            request=sha256(payload).hexdigest()
            started=time.monotonic()
            process=None
            try:
                process=subprocess.Popen([sys.executable,'-c',bootstrap+diag.program()],stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,
                    env={**os.environ,'ENTROTTER_RPC_URL':proxy.url,'PYTHONPATH':str(ROOT/'src')})
                body,stderr=process.communicate(payload,timeout=190)
                assert process.returncode==0 and stderr==b'' and len(body)<=16384
                value=diag.validate_response(json.loads(body),request,2)
                assert value['status']=='completed' and value['protocol_verified']
                assert value['observer_errors']==[] and value['discarded_observer_rows']==0
                rows=value['observer_rows'];assert [r['branch'] for r in rows]==['baseline','candidate']
                for row in rows:
                    assert row['request_id']==request and row['node_returncodes']==[0]
                    assert row['reader_threads_closed'] and row['stream_descriptors_closed']
                    assert row['complete_log_scan'] and row['eof_observed_streams']==2
                    assert not row['launch_errors'] and not row['reader_errors']
                report=json.loads(report_path.read_text());assert verify_trace(report)
                assert report['source']==Case.report['source'] and report['plan']==Case.report['plan']
                if fault=='none':
                    assert report['baseline_verified'] and value['baseline_verified']
                    assert report['baseline']==Case.report['baseline'] and report['candidate']==Case.report['candidate']
                    assert all(not r['events'] for r in rows)
                else:
                    assert not report['baseline_verified'] and not value['baseline_verified']
                    assert [r['status'] for r in report['baseline']['outcomes']]==['not_mined','not_mined']
                    assert value['candidate_statuses']==['skipped','not_mined']
                    assert rows[0]['events']=={'execution_skip':2} and rows[1]['events']=={'execution_skip':1}
                    assert proxy.denied['eth_getStorageAt']>0
                nodes=json.loads(nodes_path.read_text());assert len(nodes)==2
                assert all(n=={'port_closed':True,'guardian_returncode':0} for n in nodes)
                (output/(label+'-diagnostic.json')).write_text(json.dumps(value,indent=2)+'\n')
                finite['cases'][label]={'request_id':request,'wall_seconds':round(time.monotonic()-started,6),
                    'trace_runtime_seconds':report['runtime_seconds'],'baseline_verified':value['baseline_verified'],
                    'candidate_statuses':value['candidate_statuses'],'observer_rows':rows,'node_cleanup':nodes,
                    'proxy_requests':dict(proxy.requests),'proxy_denied':dict(proxy.denied),
                    'report_sha256':sha256(report_path.read_bytes()).hexdigest(),
                    'diagnostic_sha256':sha256((output/(label+'-diagnostic.json')).read_bytes()).hexdigest()}
            finally:
                if process is not None:
                    try:os.killpg(process.pid,9)
                    except ProcessLookupError:pass
                    process.wait(timeout=3)
                    for stream in [process.stdin,process.stdout,process.stderr]:
                        if stream is not None:stream.close()
                proxy.close()
                for thread in threading.enumerate():
                    if thread.ident not in before:thread.join(timeout=2)
                assert not [t for t in threading.enumerate() if t.ident not in before]
                assert not proxy_errors
                if label in finite['cases']:finite['cases'][label]['proxy_listener_handler_threads_port_closed']=True
        assert int(Case.source.rpc.call('eth_call',[{'to':Case.fixture['oracle'],'data':'0x'},'latest']),16)==20
        nonces=[Case.source.rpc.call('eth_getTransactionCount',[a,'latest']) for a in Case.fixture['actors']]
        assert nonces==['0x3','0x1'];finite['source_nonces_after']=nonces;finite['source_oracle_after']=20
        finite['unobserved_replay_cleanup']=Case.cleanup_records
    finally:
        Case.doClassCleanups()
        finite['class_cleanup_errors']=len(getattr(Case,'tearDown_exceptions',[]))
        source=getattr(Case,'source',None);finite['source_port_closed']=None
        finite['source_guardian_returncode']=source.process.poll() if source and source.process else None
        if source and source.rpc:
            assert_port_closed(urlsplit(source.rpc.url).port);finite['source_port_closed']=True
        (output/'finite-observations.json').write_text(json.dumps(finite,indent=2)+'\n')
    assert finite['class_cleanup_errors']==0 and finite['source_guardian_returncode']==0
    print(json.dumps({'cases':list(finite['cases']),'nodes':7,'reader_threads':8,'proxies':2,'source_closed':finite['source_port_closed']}))

if __name__=='__main__':main()
