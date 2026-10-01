import importlib, os, tempfile
from pathlib import Path
from entrotter_engine.artifact import seal
report=seal({'schema_version':'0.1.0','mode':'fixture','example':'retention boundary'})
for module_name in ['entrotter_engine.artifact','entrotter_cli.main']:
 module=importlib.import_module(module_name)
 with tempfile.TemporaryDirectory() as directory:
  root=Path(directory);os.environ['ENTROTTER_EXPORT_STATE_DIR']=str(root/'state')
  for i in range(129):module.write_report(report,root/'outputs'/f'{i}.json')
  observed=len(list((root/'outputs').glob('*.json')))
  print(module_name,'completed exports:',observed,'expected cap:128','FAIL' if observed>128 else 'PASS')
