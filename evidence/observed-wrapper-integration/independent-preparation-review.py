"""Read-only source and retained offline evidence checks; no case execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

ROOT=Path(__file__).resolve().parents[2]
Q=ROOT/'.quality/observed-wrapper-integration'
BASE='9b49fe2e53afb6a7bb35548034e222f0bdac624c'
OLD='bd5527f71d3c561335e7786b6f4421572cd9aad6'
NEW='40bea57e25ab94c0d0f6136b4c3a5af4a99e6a1d'
hashes={}
def digest(data):return hashlib.sha256(data).hexdigest()
def read(p):
    data=p.read_bytes();hashes[str(p.relative_to(ROOT))]=digest(data);return data
def load(p):return json.loads(read(p))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
assert git('rev-parse','HEAD')==BASE
names=['.github/workflows/ci.yml','.github/workflows/quality.yml','bounded-worker-pins.json','quality-inputs.json']
all_changed=set(git('diff','--name-only',BASE).splitlines())
assert set(names)<=all_changed
assert all(n.endswith('.md') for n in all_changed-set(names))  # Root's later docs are explicitly outside this source review.
for name in names[1:]:
    before=old(name);after=read(ROOT/name)
    assert before.count(OLD.encode())==1 and after==before.replace(OLD.encode(),NEW.encode())
before=old(names[0]);after=read(ROOT/names[0]);assert before.count(OLD.encode())==1
previous=yaml.safe_load(before);current=yaml.safe_load(after)
previous['jobs']['bounded-default']['steps'][1]['with']['ref']=NEW
new_steps=[s for s in current['jobs']['bounded-default']['steps'] if s.get('name')=='Inspect the supported observation wrapper with engine, SDK and viewer']
assert len(new_steps)==1 and set(new_steps[0])=={'name','run'}
without=yaml.safe_load(after)
without['jobs']['bounded-default']['steps'].remove(new_steps[0]);assert without==previous
pins=load(ROOT/'bounded-worker-pins.json');policy=load(ROOT/'quality-inputs.json')
assert pins['engine']==policy['dependency_commits']['worker-engine']==NEW
local=load(Q/'local-readers.json');steps=load(Q/'steps.json')
assert local['status']=='passed' and local['workflow_sha256']==digest(after) and local['pins']==pins
assert len(steps)==len(local['steps'])==6
workflow={s.get('name'):s.get('run') for s in current['jobs']['bounded-default']['steps'] if 'run' in s}
old_workflow={s.get('name'):s.get('run') for s in previous['jobs']['bounded-default']['steps'] if 'run' in s}
for i,(row,outcome) in enumerate(zip(steps,local['steps']),1):
    script=read(Q/f'step-{i}.sh');body=workflow[row['name']].encode()
    assert script==body and digest(body)==row['workflow_script_sha256']==outcome['workflow_script_sha256']
    assert outcome['name']==row['name'] and outcome['returncode']==0
    if i<=5:assert body==old_workflow[row['name']].encode()
    read(Q/f'step-{i}.log')
workspace=Q/'workspace';outdir=workspace/'entrotter/evidence/bounded-agent-integration/integration-ci'
for name,pin in pins.items():
    path=workspace/name
    assert path.is_symlink()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=path).decode().strip()==pin
    assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=path).decode().strip()
for name,expected in local['output_sha256'].items():assert digest(read(outdir/name))==expected
prior=ROOT/'.quality/consumer-price-integration/ci-workspace-9b49/coordination-integration-evidence'
prior_outputs={}
for name in ['trace-reader.json','trace-comparison-reader.json','trace-consumer-reader.json','trace-funding-reader.json','trace-oracle-reader.json']:
    a=load(outdir/name);b=load(prior/name);a['pins']['engine']=OLD
    assert a==b,name;prior_outputs[name]=digest(read(prior/name))
new=load(outdir/'trace-observed-reader.json')
assert new['status']=='passed' and new['pins']==pins
wrapper_path=workspace/'engine/evidence/owned-consumer-observations/historical-32/observed-trace.json'
raw=wrapper_path.read_bytes();wrapper=json.loads(raw)
assert digest(raw)==new['wrapper_sha256']=='7010848300c353310fb78dab7f377daea4226633e49af3c1a384bcb3a579ba9d'
assert new['wrapper_artifact_id']==wrapper['artifact_id'] and new['consumer_classification']==wrapper['classification']
exported=load(outdir/'observed-transaction-replay.json');assert exported==wrapper['trace_report']
assert new['trace_artifact_id']==exported['artifact_id']==new['viewer']['artifact_id']
assert new['export_sha256']=='245d52672445bf16e8f19f685790e99f34e1a625a2aa5b98e5c36e15cbdfb82f'
assert new['baseline_receipts_equal_originals']==32 and new['candidate_executed']==31 and new['skip_indices']==[12]
assert new['viewer']['node']=='v22.23.1'
assert new['viewer']['counts']=={'identical':12,'omitted':1,'structural':19,'execution':0,'unavailable':0}
assert len(new['viewer']['classifications'])==32
for i,(tx,b,c,node) in enumerate(zip(exported['source']['inputs'],exported['baseline']['outcomes'],exported['candidate']['outcomes'],new['viewer']['classifications'])):
    assert tx['index']==b['index']==c['index']==node['index']==i and tx['hash']==b['hash']==c['hash']
    assert b['receipt']==tx['original_receipt'] and not b['differing_fields'] and b['status']=='executed'
    if i==12:assert c['status']=='skipped' and 'receipt' not in c
    else:
        assert c['status']=='executed'
        diff={k for k,v in tx['original_receipt'].items() if c['receipt'][k]!=v}
        assert diff==(set() if i<12 else {'transactionIndex','cumulativeGasUsed'})
        assert set(c['differing_fields'])==diff
    assert node['kind']==('identical' if i<12 else 'omitted' if i==12 else 'structural')
    assert node['executionFields']==[]
assert len(new['prices'])==4
for row,source,price in zip(new['prices'],wrapper['observations'],[257082415000,256292441874,257082415000,257082415000]):
    assert row['consumer_price']==row['producer_answer']==price
    assert (row['branch'],row['phase'])==(source['branch'],source['phase'])
    assert row['head']==source['head'] and row['code_identities']==source['code']
assert new['viewer_module_sha256']==digest((workspace/'entrotter.github.io/trace-report.mjs').read_bytes())
assert new['comparison_module_sha256']==digest((workspace/'entrotter.github.io/trace-comparison.mjs').read_bytes())
types=load(Q/'local-types.json');assert json.loads(read(Q/'local-types.log'))==types
assert types['status']=='passed_with_explicit_frozen_diagnostics' and types['mypy_version']==policy['mypy_version']=='1.18.2'
assert len(types['sources_sha256'])==21 and types['dependency_commits']==policy['dependency_commits']
assert all(digest(read(ROOT/n))==h for n,h in types['sources_sha256'].items())
assert sum(g['reviewed_diagnostics'] for g in types['groups'])==3
assert [g['exit_code'] for g in types['groups']]==[1,0,0]
ledger=load(workspace/'.quality/observed-reader-export-state/ledger.json')
assert len(ledger['entries'])==1 and ledger['entries'][0]['sha256']==new['export_sha256']
assert ledger['entries'][0]['bytes']==(outdir/'observed-transaction-replay.json').stat().st_size
read(Path(__file__))
review={'status':'passed_no_actionable_preparation_findings','reviewer':'review_cli_agent','base':BASE,'selected_engine':NEW,'reviewed_source_sha256':{n:hashes[n] for n in names},'other_pending_doc_paths_outside_review':sorted(all_changed-set(names)),'reviewer_corrections':['Initial global diff-size assertion stopped because root concurrently prepared two later documentation paths; scoped to the four requested source files and explicitly deferred those docs. No source/test/case failure or rerun.'],'evidence_sha256':hashes,'pins':pins,'old_five_script_bodies_and_complete_JSON_equal_except_engine_pin':True,'old_raw_output_sha256':prior_outputs,'new_reader':{'wrapper_sha256':new['wrapper_sha256'],'export_sha256':new['export_sha256'],'typed_complete_receipt_matches':32,'candidate_executed':31,'skip_indices':[12],'viewer_counts':new['viewer']['counts'],'four_raw_price_views':True,'normal_quota_export_ledger_bound':True,'node':new['viewer']['node']},'types':{'sources':21,'retained_frozen_diagnostics':3,'source_hashes_match':True},'inspection':['Only four source selectors change, one occurrence each bd to40. Entire parsed CI remains identical after removing one new mandatory run step and restoring the bounded-engine selector; all frozen jobs/actions, guards and five old run bodies retained.','All six exact workflow script bytes equal retained step shell files; author six return codes0/logs retained, full output hashes match. Clean selected engine/SDK/viewer/CLI/scenarios Git heads checked read-only.','New trusted fixed step imports strict engine wrapper loader, uses normal bounded report writer, actual SDK and actual Node validators. Sealed fixed digest prevents malformed/resealed data substitution; typed full receipt equality and viewer classifications preserve every row/difference.','Independent raw output comparison confirms32 original baseline receipts and31candidate/skip12/19structural-only, four prices/head/code records. No live EVM/provider/model/browser execution claimed; SDK/viewer inspect only nested trace.','Types retain21 current source hashes and same three explicit frozen diagnostics; dependency policy changes only one worker-engine pin.','No product/source edits, case/test/scanner/network/browser/CI reruns during this review.'], 'findings':[],'limits':['Local retained offline results are not fresh combined CI, Docker32, rendered browser/Pages or provider authentication proof.','Price difference remains a read-only view; no signed consumer strategy, benefit/profit or full-block/root/opcode proof.','Independent software source review is distinct from mandatory human protected-main approval.','Public docs/evidence package and immutable execution snapshot require separate later review.']}
out=Q/'independent-preparation-review.json';out.write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'status':review['status'],'path':str(out),'sha256':digest(out.read_bytes()),'bound_files':len(hashes),'findings':0},indent=2))
