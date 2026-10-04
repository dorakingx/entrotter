from pathlib import Path
import ast,json,subprocess,hashlib
root=Path.cwd();base='6368eef29dd7beb694da9174f46d1518b38d52d5'
class Normalize(ast.NodeTransformer):
 def visit_Name(self,node):
  if node.id=='failed_run':node.id='result'
  return node

def representation(node):return ast.dump(Normalize().visit(node),include_attributes=False) if node is not None else None

def predicate(node):
 if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):return node.operand
 if isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.ops[0],ast.NotIn):
  node.ops=[ast.In()];return node
 raise ValueError('Unexpected guard form')
results=[]
for p in sorted((root/'scripts').glob('*.py')):
 relative=str(p.relative_to(root))
 old=subprocess.run(['git','show',base+':'+relative],capture_output=True,text=True)
 if old.returncode:continue
 tree=ast.parse(old.stdout);expected=[(representation(n.test),representation(n.msg)) for n in ast.walk(tree) if isinstance(n,ast.Assert)]
 if not expected:continue
 found=[]
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,ast.If) and len(n.body)==1 and isinstance(n.body[0],ast.Raise):
   exception=n.body[0].exc
   if isinstance(exception,ast.Call) and isinstance(exception.func,ast.Name) and exception.func.id=='AssertionError':
    found.append((representation(predicate(n.test)),representation(exception.args[0]) if exception.args else None))
 if sorted(map(str,expected))!=sorted(map(str,found)):raise ValueError(relative+' predicates or lazy messages changed')
 results.append({'file':relative,'original_assertions':len(expected),'explicit_guards':len(found),'predicates_and_lazy_messages_equal':True})
result={'baseline_commit':base,'status':'passed','total_converted':sum(r['explicit_guards'] for r in results),'files':results,'normalization':'Ignore AST locations, invert Ruff membership rewrites, normalize failed_run/result variable rename; embedded installed-venv path check is separately explicit'}
Path('/tmp/entrotter-coordination-predicate-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
