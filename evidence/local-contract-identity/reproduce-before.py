"""Focused actual Anvil case-alias repro; no archive/model/Docker execution."""
import copy, hashlib, json, socket
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from entrotter_engine.runner import run_native
from entrotter_engine.models import validate
from entrotter_engine.artifact import canonical
from entrotter_engine.evm import AnvilSession
s=json.loads(Path('tests/data/local.json').read_text())
low='0x'+'ab'*20
upper='0x'+'AB'*20
s['allowed_targets']=[low]
s['local_contracts']={low:'0x60006000fd',upper:'0x00'}
s['steps']=[{'baseline':None,'candidate':{'to':low,'value_wei':'0','gas':50000}}]
other=copy.deepcopy(s)
other['local_contracts']={upper:'0x00',low:'0x60006000fd'}
root=Path('.quality/core-review')
root.joinpath('forward-scenario.json').write_text(json.dumps(s,indent=2)+'\n')
root.joinpath('reverse-scenario.json').write_text(json.dumps(other,indent=2)+'\n')
validate(s);validate(other)
sessions=[]
class TrackedSession(AnvilSession):
    def __enter__(self):
        sessions.append(self)
        return super().__enter__()
with patch('entrotter_engine.evm.AnvilSession',TrackedSession):
    a=run_native(s);b=run_native(other)
cleanup=[]
for session in sessions:
    port=urlsplit(session.rpc.url).port
    with socket.socket() as sock:
        sock.settimeout(.2)
        open_port=sock.connect_ex(('127.0.0.1',port))==0
    cleanup.append({'guardian_pid':session.process.pid,'guardian_returncode':session.process.poll(),'owned_rpc_port':port,'port_closed':not open_port})
    assert session.process.poll() is not None and not open_port
summary={'canonical_scenarios_equal':canonical(a['scenario'])==canonical(b['scenario']),
         'canonical_scenario_sha256':hashlib.sha256(canonical(s)).hexdigest(),
         'forward_candidate_status':a['candidate']['trace'][0]['status'],
         'reverse_candidate_status':b['candidate']['trace'][0]['status'],
         'forward_gas_used':a['candidate']['metrics']['gas_used'],
         'reverse_gas_used':b['candidate']['metrics']['gas_used'],
         'anvil':a['candidate']['tool_version'],'execution':'explicit native, actual local Anvil',
         'owned_node_cleanup':cleanup,'docker_started':False,'archive_calls':0,'model_calls':0}
assert summary['canonical_scenarios_equal'] and summary['forward_candidate_status']=='success' and summary['reverse_candidate_status']=='reverted'
root.joinpath('result.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
