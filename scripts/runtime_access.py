import requests,json,secrets,os,re,subprocess
from pathlib import Path
s=requests.Session();s.auth=(os.environ['AAP_ADMIN_USER'],os.environ['AAP_ADMIN_PASSWORD']);base=os.environ['AAP_URL'];st=json.loads(Path('.private/aap-state.json').read_text())
def api(method,path,body=None):
 r=s.request(method,base+path,json=body,timeout=30)
 if r.status_code>=400:raise RuntimeError(path+' status='+str(r.status_code)+' response keys='+str(list(r.json())))
 return r.json() if r.content else {}
u=api('GET','/api/gateway/v1/users/?username=caixa-demo-agent')['results']
if not u:
 pw=secrets.token_urlsafe(32);u=api('POST','/api/gateway/v1/users/',{'username':'caixa-demo-agent','password':pw,'is_superuser':False});Path('.private/runtime-user-password').write_text(pw);os.chmod('.private/runtime-user-password',0o600)
else:u=u[0]
print('Runtime user ID',u['id'])
# Resolve the controller user after gateway synchronization.
cu=api('GET','/api/controller/v2/users/?username=caixa-demo-agent')['results'][0]
for name in ['diagnose','verify','recover_database','recover_application','validation_evidence']:
 jt=api('GET',f'/api/controller/v2/job_templates/{st["CAIXA "+name]}/')
 role=jt['summary_fields']['object_roles']['execute_role']['id'];api('POST',f'/api/controller/v2/roles/{role}/users/',{'id':cu['id']});print('Execute granted',name)
tokenpath=Path('.private/aap-runtime-token')
if not tokenpath.exists():
 s.auth=('caixa-demo-agent',Path('.private/runtime-user-password').read_text());t=api('POST','/api/gateway/v1/tokens/',{'description':'CAIXA demo MCP scoped runtime','scope':'write','application':None});tokenpath.write_text(t['token']);os.chmod(tokenpath,0o600)
s.auth=(os.environ['AAP_ADMIN_USER'],os.environ['AAP_ADMIN_PASSWORD']);print('Runtime token stored privately')
job=api('GET',f'/api/controller/v2/jobs/{st["network_job"]}/');print('Network job',job['status'])
if job['status']=='successful':
 out=s.get(base+f'/api/controller/v2/jobs/{job["id"]}/stdout/?format=txt',timeout=20).text
 ips=re.findall(r'AAP_EGRESS=(\d+\.\d+\.\d+\.\d+)',out);print('AAP execution egress',ips)
 if ips:
  state=json.loads(Path('.private/aws-state.json').read_text());state['aap_egress']=ips[0];Path('.private/aws-state.json').write_text(json.dumps(state,indent=2))
  env=os.environ.copy();env.update(AWS_DEFAULT_REGION='us-east-1',AWS_PAGER='')
  r=subprocess.run(['aws','ec2','authorize-security-group-ingress','--group-id',state['security_group'],'--protocol','tcp','--port','22','--cidr',ips[0]+'/32'],env=env,capture_output=True,text=True);print('SSH ingress rule result',r.returncode)
