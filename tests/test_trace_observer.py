"""Trusted diagnostic observer transport, finite privacy and owned lifecycle."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('observer_diagnostic',ROOT/'tests_isolated/diagnose_trace_worker.py')
diagnostic=importlib.util.module_from_spec(spec);sys.modules[spec.name]=diagnostic;spec.loader.exec_module(diagnostic)
TX='0x'+'12'*32
REQUEST='34'*32
SECRET='private-url-token-must-never-be-emitted'


class GuardianObserverTests(unittest.TestCase):
    def guardian(self,code,*,lifetime=2,close_owner=False,thread_failure=False):
        program=diagnostic.guardian_program()
        if thread_failure:
            injection="import threading;original_start=threading.Thread.start;calls=0\ndef fail(self):\n global calls\n calls+=1\n if calls==2:raise RuntimeError("+repr(SECRET)+")\n return original_start(self)\nthreading.Thread.start=fail\n"
            program=injection+program
        started=time.monotonic()
        process=subprocess.Popen([sys.executable,'-c',program,REQUEST,'baseline',json.dumps([TX]),str(lifetime),sys.executable,'-c',code],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            start_new_session=True,env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
        try:
            if close_owner:process.stdin.close();process.stdin=None
            process.wait(timeout=5)
            body=process.stdout.read(4097);stderr=process.stderr.read(4097)
            self.assertLessEqual(len(body),4096);self.assertEqual(stderr,b'')
            row=json.loads(body)
            diagnostic.validate_observer_row(row,REQUEST,'baseline',1)
            self.assertNotIn(SECRET,body.decode());self.assertTrue(row['reader_threads_closed'])
            self.assertTrue(row['stream_descriptors_closed'])
            return row,process.returncode,time.monotonic()-started
        finally:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            if process.stdin is not None:process.stdin.close()
            process.stdout.close();process.stderr.close();process.wait(timeout=2)

    def test_real_embedded_guardian_exit_seven_remains_readable(self):
        row,rc,_=self.guardian('import sys;sys.exit(7)')
        self.assertEqual(rc,7);self.assertEqual(row['guardian_result'],7)
        self.assertEqual(row['node_returncodes'],[7])
        self.assertTrue(row['complete_log_scan'])

    def test_both_streams_bind_events_to_original_index_without_private_text(self):
        line='2026-10-02T00:00:00.123Z TRACE backend: tx execution error, skipping '+TX+' err='+SECRET+'\n'
        code='import os;os.write(1,'+repr(line.encode())+');os.write(2,'+repr(line.encode())+')'
        row,rc,_=self.guardian(code)
        self.assertEqual(rc,0);self.assertEqual(row['events'],{'execution_skip':2})
        self.assertEqual(row['input_indices'],{'0':2})

    def test_flood_cap_and_overlong_lines_explicitly_mark_incomplete(self):
        row,rc,_=self.guardian("import os;os.write(1,b'x'*10000+b'\\n');os.write(2,b'y'*1000000)")
        self.assertEqual(rc,0);self.assertTrue(row['scan_cap_exhausted'])
        self.assertGreater(row['overlong_lines_discarded'],0)
        self.assertFalse(row['complete_log_scan'])

    def test_original_lifetime_kills_term_ignoring_child(self):
        row,rc,elapsed=self.guardian('import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)',lifetime=.3)
        self.assertEqual(rc,124);self.assertEqual(row['node_returncodes'],[-signal.SIGKILL])
        self.assertLess(elapsed,3.5)

    def test_owner_eof_stops_original_guardian(self):
        row,rc,elapsed=self.guardian('import time;time.sleep(30)',close_owner=True)
        self.assertEqual(rc,0);self.assertEqual(row['node_returncodes'],[-signal.SIGTERM])
        self.assertLess(elapsed,1)

    @unittest.skipUnless(hasattr(os,'fork'),'POSIX fork required')
    def test_descendant_held_pipe_closes_readers_but_marks_incomplete(self):
        row,rc,elapsed=self.guardian('import os,time;pid=os.fork();\nif pid==0:time.sleep(30)\n')
        self.assertEqual(rc,0);self.assertLess(elapsed,1.5)
        self.assertEqual(row['eof_observed_streams'],0)
        self.assertEqual(row['stop_before_eof_streams'],2)
        self.assertFalse(row['complete_log_scan'])
        # Test owner finalizer kills descendants in the owned session; original
        # supervise continues to manage only its direct child, unchanged.

    def test_second_reader_start_failure_cleans_owned_node_and_descriptors(self):
        row,rc,elapsed=self.guardian('import time;time.sleep(30)',thread_failure=True)
        self.assertEqual(rc,1);self.assertEqual(row['launch_errors'],{'reader_start_error':1})
        self.assertEqual(row['supervisor_error'],'other')
        self.assertEqual(row['node_returncodes'],[-signal.SIGTERM])
        self.assertLess(elapsed,1.5)

    def test_reader_exception_is_finite_and_descriptor_closes(self):
        read,write=os.pipe();os.close(write);stream=os.fdopen(read,'rb')
        parser=diagnostic.Parser([TX])
        with patch.object(diagnostic.os,'read',side_effect=OSError(SECRET)):parser.drain(stream)
        self.assertTrue(stream.closed);self.assertEqual(parser.finite()['reader_errors'],{'os_error':1})
        self.assertNotIn(SECRET,json.dumps(parser.finite()))

    def test_row_rejects_resealed_unsafe_unbound_and_contradictory_data(self):
        row,_,_=self.guardian('pass')
        changes=[{'request_id':'56'*32},{'branch':'candidate'},{'input_indices':{'1':1}},
            {'events':{SECRET:1}},{'raw_url':SECRET},{'complete_log_scan':False},
            {'raw_logs_retained':True},{'guardian_result':True},{'raw_bytes_drained':-1},
            {'scan_cap_exhausted':True},{'eof_observed_streams':True}]
        for change in changes:
            with self.subTest(keys=list(change)),self.assertRaises(ValueError):
                diagnostic.validate_observer_row({**row,**change},REQUEST,'baseline',1)


class CollectorTests(unittest.TestCase):
    def process(self,code):
        return subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,start_new_session=True)

    def test_unsafe_and_unbound_output_is_discarded_with_secondary_error_only(self):
        for text in [SECRET,json.dumps({'request_id':'56'*32}), 'x'*8192]:
            process=self.process('print('+repr(text)+')')
            rows,discarded,errors=diagnostic.collect_observer_rows([('baseline',process)],REQUEST,1)
            self.assertEqual(rows,[]);self.assertEqual(discarded,1)
            self.assertTrue(errors);self.assertTrue(process.stdout.closed)
            self.assertIsNotNone(process.poll());self.assertNotIn(SECRET,json.dumps(errors))

    def test_real_bound_guardian_row_is_collected_without_normal_report_mutation(self):
        program=diagnostic.guardian_program()
        process=subprocess.Popen([sys.executable,'-c',program,REQUEST,'baseline',json.dumps([TX]),'2',sys.executable,'-c','pass'],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True,
            env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
        process.wait(timeout=2)
        rows,discarded,errors=diagnostic.collect_observer_rows([('baseline',process)],REQUEST,1)
        self.assertEqual(len(rows),1);self.assertEqual(discarded,0);self.assertEqual(errors,[])
        self.assertEqual(rows[0]['request_id'],REQUEST)
        self.assertTrue(process.stdout.closed)

    def test_cleanup_failure_is_secondary_and_descriptor_still_closes(self):
        process=self.process('print('+repr(SECRET)+')');process.wait(timeout=2)
        original_poll=process.poll
        with patch.object(process,'poll',return_value=None), \
                patch.object(process,'wait',side_effect=PermissionError(SECRET)), \
                patch.object(diagnostic.os,'killpg',side_effect=PermissionError(SECRET)):
            rows,discarded,errors=diagnostic.collect_observer_rows([('baseline',process)],REQUEST,1)
        self.assertEqual(rows,[]);self.assertEqual(discarded,1)
        self.assertTrue(process.stdout.closed);self.assertIsNotNone(original_poll())
        self.assertTrue(any(e['phase']=='cleanup' for e in errors))
        self.assertNotIn(SECRET,json.dumps(errors))

    @unittest.skipUnless(hasattr(os,'fork'),'POSIX fork required')
    def test_collector_deadline_kills_descendant_retaining_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            port_file=Path(directory)/'owned-port'
            code=('import os,socket,time\nfrom pathlib import Path\n'
                'pid=os.fork()\nif pid==0:\n'
                " sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen()\n"
                ' Path('+repr(str(port_file))+').write_text(str(sock.getsockname()[1]))\n'
                ' time.sleep(30)\nelse:\n'
                ' while not Path('+repr(str(port_file))+').exists():time.sleep(.01)\n')
            process=self.process(code)
            try:
                process.wait(timeout=2);port=int(port_file.read_text())
                with socket.socket() as sock:
                    self.assertEqual(sock.connect_ex(('127.0.0.1',port)),0)
                started=time.monotonic()
                rows,discarded,errors=diagnostic.collect_observer_rows([('baseline',process)],REQUEST,1)
                self.assertEqual(rows,[]);self.assertEqual(discarded,1)
                self.assertIn({'phase':'pipe_or_process','category':'timeout'},errors)
                self.assertTrue(process.stdout.closed);self.assertLess(time.monotonic()-started,4)
                deadline=time.monotonic()+1
                while True:
                    with socket.socket() as sock:
                        closed=sock.connect_ex(('127.0.0.1',port))!=0
                    if closed:break
                    self.assertLess(time.monotonic(),deadline);time.sleep(.01)
            finally:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                for stream in [process.stdin,process.stdout]:
                    if stream is not None:stream.close()
                process.wait(timeout=2)


class EmbeddedProtocolTests(unittest.TestCase):
    def run_embedded(self,program,payload):
        process=subprocess.run([sys.executable,'-c',program],input=payload,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,
            env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
        self.assertEqual(process.returncode,0);self.assertEqual(process.stderr,b'')
        self.assertLessEqual(len(process.stdout),diagnostic.MAX_OUTPUT)
        self.assertNotIn(SECRET,process.stdout.decode())
        return json.loads(process.stdout)

    def test_secondary_collector_error_preserves_primary_trace_failure(self):
        payload=b'{"worker_version":"1","trace":{}}'
        bootstrap=("from entrotter_engine import worker_protocol\n"
            "from entrotter_engine.rpc import RPCError\n"
            "def original_failure(raw):raise RPCError("+repr(SECRET)+")\n"
            "worker_protocol.execute_request=original_failure\n")
        source=diagnostic.program().rsplit('image_main()',1)[0]
        source+=("def failed_collector(*args):raise PermissionError("+repr(SECRET)+")\n"
            "collect_observer_rows=failed_collector\nimage_main()\n")
        result=self.run_embedded(bootstrap+source,payload)
        diagnostic.validate_response(result,sha256(payload).hexdigest(),2)
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['error']['category'],'rpc_error')
        self.assertEqual(result['observer_errors'],[{'phase':'cleanup','category':'os_error'}])
        self.assertFalse(result['protocol_verified']);self.assertIsNone(result['baseline_verified'])

    def test_outer_envelope_rejects_unbound_reordered_or_extra_observer_rows(self):
        guardian=GuardianObserverTests(methodName='runTest')
        row,_,_=guardian.guardian('pass')
        from test_trace_diagnostic import response
        value=response(REQUEST)
        value.update(observed_input_count=1,observer_rows=[row])
        diagnostic.validate_response(value,REQUEST,1)
        changes=[{'observer_rows':[row,row]},
            {'observer_rows':[{**row,'branch':'candidate'},row]},
            {'observer_rows':[{**row,'request_id':'56'*32}]},
            {'observed_input_count':2},{'discarded_observer_rows':2},
            {'observer_errors':[{'phase':'cleanup','category':SECRET}]}]
        for change in changes:
            with self.subTest(keys=list(change)),self.assertRaises(ValueError):
                diagnostic.validate_response({**value,**change},REQUEST,1)


if __name__=='__main__':unittest.main()
