
from pathlib import Path
import subprocess,json,os,errno,uuid,urllib.request,hashlib

def run(*args):return subprocess.check_output(args,text=True,timeout=30).strip()
def mount(path):
 d=json.loads(run('findmnt','-J','-T',str(path)))['filesystems'][0]
 return {k:d[k] for k in ('target','source','fstype','options')}
app=Path.home()/'.local/share/entrotter'
mem=dict((x.split(':',1)[0],int(x.split()[1])*1024) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith(('MemTotal:','SwapTotal:')))
devices=[x for x in json.loads(run('lsblk','-b','-J','-o','NAME,SIZE,TYPE,RO,FSTYPE,MOUNTPOINTS'))['blockdevices'] if x['type']=='disk']
assert os.cpu_count()==2 and mem['MemTotal']<=2*1024**3 and mem['SwapTotal']==0
writable_devices=[x for x in devices if not x['ro']]
assert len(writable_devices)==1 and writable_devices[0]['name']=='vda' and int(writable_devices[0]['size'])==10*1024**3
readonly_devices=[x for x in devices if x['ro']]
assert all(Path('/sys/block/'+x['name']+'/ro').read_text().strip()=='1' for x in readonly_devices)
shares=json.loads(run('findmnt','-J','-t','fuse.sshfs'))['filesystems']
assert len(shares)==2
proof=[]
for share in shares:
 assert 'ro' in share['options'].split(',')
 target=Path(share['target']);marker=target/('entrotter-ro-probe-'+uuid.uuid4().hex)
 try:
  fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 except OSError as e:
  assert e.errno==errno.EROFS,(target,e)
  code=e.errno
 else:
  os.close(fd);marker.unlink();raise RuntimeError('Host share accepted a write')
 proof.append({'name':target.name,'mount_readonly':True,'write_errno':code})
paths=['/','/tmp','/var/lib/docker',app,app/'reports']
writable=[{'path':str(p).replace(str(Path.home()),'<guest-home>'),'mount':mount(p)} for p in paths]
assert all(x['mount']['fstype']=='ext4' and x['mount']['source']=='/dev/vda1' for x in writable)
with urllib.request.urlopen('http://127.0.0.1:8787/health',timeout=5) as response:health=json.load(response)
heads={repo:run('git','-C',str(app/repo),'rev-parse','HEAD') for repo in ('engine','sdk','cli')}
clean_sources={repo:not run('git','-C',str(app/repo),'status','--porcelain') for repo in heads}
assert all(clean_sources.values())
source={name:hashlib.sha256((app/name).read_bytes()).hexdigest() for name in ('check_host_envelope.py','check_service.py')}
workers=run('docker','ps','-aq','--filter','label=org.entrotter.worker=true').splitlines()
units=[x for x in run('systemctl','--user','list-units','--all','--no-legend').splitlines() if 'entrotter-host-proof-' in x]
assert not workers and not units
print(json.dumps({'cpu_count':os.cpu_count(),'memory_total_bytes':mem['MemTotal'],'swap_total_bytes':mem['SwapTotal'],'root_block_device_bytes':int(writable_devices[0]['size']),'readonly_block_devices':readonly_devices,'writable_paths':writable,'host_share_probes':proof,'api_health_after_fault_probes':health,'owned_worker_containers':len(workers),'transient_proof_units':len(units),'source_commits':heads,'source_worktrees_clean':clean_sources,'source_sha256':source,'disk_exhaustion_tested':False,'disk_proof_scope':'Actual block geometry and mount topology, not filling the live root disk','systemd':run('systemd','--version').splitlines()[0],'python':run('python3','--version')},indent=2))
