#!/usr/bin/env python3
"""Launch a fixed AAP template and collect its result; credentials only via environment."""
import json,os,time,urllib.request,urllib.error,sys
BASE=os.environ['AAP_URL'].rstrip('/')+'/api/controller/v2/'
TOKEN=os.environ['AAP_TOKEN']
def request(path,body=None):
 req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
def run(template_id):
 launched=request(f'job_templates/{int(template_id)}/launch/',{})
 jid=launched['job']
 for _ in range(180):
  job=request(f'jobs/{jid}/')
  if job['status'] not in ['new','pending','waiting','running']:
   return {'job':jid,'status':job['status'],'failed':job['failed'],'url':os.environ['AAP_URL'].rstrip('/')+f'/execution/jobs/playbook/{jid}/details'}
  time.sleep(2)
 raise TimeoutError(f'Job {jid} remains active; inspect AAP before retrying')
if __name__=='__main__':
 result=run(sys.argv[1]);print(json.dumps(result));sys.exit(1 if result['failed'] else 0)
