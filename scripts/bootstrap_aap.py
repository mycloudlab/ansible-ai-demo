import requests,json,time,os
from pathlib import Path
s=requests.Session();s.auth=(os.environ['AAP_ADMIN_USER'],os.environ['AAP_ADMIN_PASSWORD']);base=os.environ['AAP_URL'];statepath=Path('.private/aap-state.json');st=json.loads(statepath.read_text()) if statepath.exists() else {}
def api(method,path,data=None):
 r=s.request(method,base+path,json=data,timeout=40)
 if r.status_code>=400:raise RuntimeError(method+' '+path+' status='+str(r.status_code)+' fields='+','.join(r.json().keys()) if 'json' in r.headers.get('content-type','') else 'API failed '+str(r.status_code))
 return r.json() if r.content else {}
def ctl(method,path,data=None):return api(method,'/api/controller/v2/'+path,data)
def ensure(kind,name,body):
 existing=ctl('GET',kind+'/?name='+requests.utils.quote(name))['results']
 v=existing[0] if existing else ctl('POST',kind+'/',dict(name=name,**body))
 st[name]=v['id'];statepath.write_text(json.dumps(st,indent=2));print(name,v['id'],flush=True);return v
org=ensure('organizations','CAIXA AI Demo',{})
inv=ensure('inventories','CAIXA Demo Inventory',{'organization':org['id']})
state=json.loads(Path('.private/aws-state.json').read_text())
hosts=ctl('GET',f'inventories/{inv["id"]}/hosts/')['results']
if not hosts:ctl('POST',f'inventories/{inv["id"]}/hosts/',{'name':'caixa-demo','variables':json.dumps({'ansible_host':state['public_ip'],'ansible_user':'ubuntu'})})
groups=ctl('GET',f'inventories/{inv["id"]}/groups/')['results']
g=groups[0] if groups else ctl('POST',f'inventories/{inv["id"]}/groups/',{'name':'caixa_demo'})
h=ctl('GET',f'inventories/{inv["id"]}/hosts/')['results'][0];ctl('POST',f'groups/{g["id"]}/hosts/',{'id':h['id']})
cred=ensure('credentials','CAIXA Demo SSH',{'organization':org['id'],'credential_type':7,'inputs':{'username':'ubuntu','ssh_key_data':Path('.private/caixa-demo-key').read_text(),'become_method':'sudo'}})
project=ensure('projects','CAIXA Demo Git',{'organization':org['id'],'scm_type':'git','scm_url':'https://github.com/mycloudlab/ansible-ai-demo.git','scm_branch':'main','scm_update_on_launch':False})
for _ in range(30):
 v=ctl('GET',f'projects/{project["id"]}/');status=v['status']
 if status not in ['pending','running','updating','waiting']:break
 time.sleep(2)
print('Project status',status,flush=True)
if status!='successful':
 upd=ctl('POST',f'projects/{project["id"]}/update/');print('Update started',upd.get('id'),flush=True)
for name in ['execution_network','deploy','diagnose','verify','recover_database','recover_application','validation_evidence','fault_database_stop','fault_validation','fault_oom_once','reset_validation']:
 v=ensure('job_templates','CAIXA '+name,{'organization':org['id'],'inventory':inv['id'],'project':project['id'],'playbook':'playbooks/'+name+'.yml','job_type':'run','execution_environment':2,'become_enabled':name!='execution_network','ask_variables_on_launch':False,'ask_inventory_on_launch':False,'ask_limit_on_launch':False,'timeout':900})
 if name!='execution_network':ctl('POST',f'job_templates/{v["id"]}/credentials/',{'id':cred['id']})
v=ctl('POST',f'job_templates/{st["CAIXA execution_network"]}/launch/',{});st['network_job']=v['job'];statepath.write_text(json.dumps(st,indent=2));print('Network job',v['job'],flush=True)
