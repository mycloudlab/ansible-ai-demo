import requests,json,time,re,os
from pathlib import Path
admin=requests.Session();admin.auth=(os.environ['AAP_ADMIN_USER'],os.environ['AAP_ADMIN_PASSWORD']);runtime=requests.Session();runtime.headers['Authorization']='Bearer '+Path('.private/aap-runtime-token').read_text();base=os.environ['AAP_URL']+'/api/controller/v2/';ids=json.loads(Path('.private/aap-state.json').read_text());records=[]
def run(name,session=admin):
 r=session.post(base+f'job_templates/{ids["CAIXA "+name]}/launch/',json={},timeout=40);r.raise_for_status();jid=r.json()['job'];print('Launched',name,jid,flush=True)
 for _ in range(180):
  d=session.get(base+f'jobs/{jid}/',timeout=30).json()
  if d['status'] not in ['new','pending','waiting','running']:break
  time.sleep(2)
 out=session.get(base+f'jobs/{jid}/stdout/?format=txt',timeout=30).text
 Path(f'.private/job-{jid}.txt').write_text(out)
 records.append({'template':name,'job':jid,'status':d['status']});Path('.private/scenario-results.json').write_text(json.dumps(records,indent=2));print('Finished',name,jid,d['status'],flush=True)
 if d['status']!='successful':raise RuntimeError(f'Job {jid} failed; private evidence saved')
 return out
state=json.loads(Path('.private/aws-state.json').read_text());app='http://'+state['public_ip']+':8080'
def health():
 try:return requests.get(app+'/health',timeout=5).status_code
 except requests.RequestException:return -1
def register():return requests.post(app+'/people',data={'name':'Pessoa Teste','email':'teste@example.invalid'},timeout=8).status_code
run('verify',runtime);assert health()==200 and register()==201
run('fault_database_stop');assert health()==503 and register()==503
out=run('diagnose',runtime);assert 'DATABASE_UNAVAILABLE' in out and 'inactive' in out
run('recover_database',runtime);assert health()==200 and register()==201
run('fault_validation');assert health()==200 and register()==500
out=run('validation_evidence',runtime);assert 'VALIDATION_RULE_DEMO' in out and '500' in out
run('reset_validation');assert register()==201
run('fault_oom_once')
for _ in range(15):
 if health()==-1:break
 time.sleep(1)
assert health()==-1
out=run('diagnose',runtime);assert 'OOM_DEMO_TRIGGER_CONSUMED' in out and 'OutOfMemoryError' in out
run('recover_application',runtime);assert health()==200 and register()==201
time.sleep(5);assert health()==200
# An operational token must not be able to launch an injected fault or deploy.
for n in ['deploy','fault_database_stop','fault_validation','fault_oom_once','reset_validation']:
 r=runtime.post(base+f'job_templates/{ids["CAIXA "+n]}/launch/',json={},timeout=20);assert r.status_code in [403,404],(n,r.status_code)
print('PASS all three scenarios, recoveries and runtime RBAC denials',flush=True)
