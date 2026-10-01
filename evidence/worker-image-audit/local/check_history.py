import hashlib,json,os,platform,time
from pathlib import Path
from entrotter_engine.runner import run
from entrotter_engine.artifact import verify
root=Path(os.environ['ENTROTTER_WORKSPACE'])
scenario_path=root/'scenarios/evm/ethereum-uniswap-slippage.json'
reference_path=root/'entrotter/evidence/historical-uniswap.json'
scenario=json.loads(scenario_path.read_text())
reference=json.loads(reference_path.read_text())
runs=[]
for attempt in range(2):
 start=time.monotonic(); report=run(scenario); elapsed=time.monotonic()-start
 assert verify(report) and report == reference, 'Full historical artifact changed'
 runs.append({'wall_seconds':elapsed,'artifact_id':report['artifact_id'],'full_reference_equality':True})
result={'status':'passed','mode':'bounded default archived-state supplied-action execution','runs':runs,'platform':platform.platform(),'image_id':os.environ['ENTROTTER_WORKER_IMAGE'],'scenario_sha256':hashlib.sha256(scenario_path.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limitations':['Same previously explored 19M case; no new model evaluation or holdout','Includes public archive latency; not a performance comparison','No historical trace replay or portfolio profit claim']}
(root/'entrotter/evidence/worker-image-audit/local/historical.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
