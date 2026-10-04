import assert from 'node:assert/strict';
import {readFile,readdir,writeFile} from 'node:fs/promises';
import {createHash,webcrypto} from 'node:crypto';
import vm from 'node:vm';
const [root,oldPath,output]=process.argv.slice(2);
const names=(await readdir(root+'/causal-v1')).filter(n=>/^causal-uniswap-.*\.json$/.test(n)).map(n=>'causal-v1/'+n);
names.push('agent-local-prescribed.json','agent-local-risk.json','agent-local-codex.json','historical-uniswap.json');
assert.equal(names.length,19);
const source=await readFile('app.js','utf8'),oldSource=await readFile(oldPath,'utf8');
function context(code){const c=vm.createContext({document:{getElementById:()=>({value:'none',addEventListener:()=>{}})},crypto:webcrypto,TextEncoder,fetch:()=>{throw Error('No network allowed')}});vm.runInContext(code,c);return c;}
const before=context(oldSource),after=context(source),rows=[];
for(const name of names.sort()){
  const bytes=await readFile(root+'/'+name);const data=JSON.parse(bytes);
  await before.checkHash(data);await after.checkHash(data);
  assert.equal(JSON.stringify(after.evmViewModel(data)),JSON.stringify(before.evmViewModel(data)),name);
  rows.push({path:'evidence/'+name,file_sha256:createHash('sha256').update(bytes).digest('hex'),artifact_id:data.artifact_id,unchanged_evm_view_model:true});
}
await writeFile(output,JSON.stringify({status:'passed',reports:rows,old_source_sha256:createHash('sha256').update(oldSource).digest('hex'),new_source_sha256:createHash('sha256').update(source).digest('hex'),scope:'Offline exact production hash and EVM view-model comparison on 19 existing public reports; no new chain/model execution'},null,2)+'\n');
console.log('All 19 existing reports retain exact hash acceptance and EVM view model');
