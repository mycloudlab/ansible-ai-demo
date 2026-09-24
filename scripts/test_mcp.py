#!/usr/bin/env python3
"""Protocol-level MCP test using the same endpoint and token as both clients."""
import json,os,time,requests
s=requests.Session();s.headers.update({'Authorization':'Bearer '+os.environ['AAP_TOKEN'],'Accept':'application/json, text/event-stream'})
url=os.environ.get('AAP_MCP_URL','http://127.0.0.1:3017/mcp/caixa_demo');sequence=0
def call(method,params=None):
 global sequence
 sequence+=1
 r=s.post(url,json={'jsonrpc':'2.0','id':sequence,'method':method,'params':params or {}},timeout=60);r.raise_for_status()
 if r.headers.get('Mcp-Session-Id'):s.headers['Mcp-Session-Id']=r.headers['Mcp-Session-Id']
 d=json.loads(next(l[6:] for l in r.text.splitlines() if l.startswith('data: '))) if r.text.startswith('event:') else r.json()
 if 'error' in d:raise RuntimeError(str(d['error']))
 return d['result']
def tool(name,args):
 d=call('tools/call',{'name':name,'arguments':args})
 if d.get('isError'):raise RuntimeError(json.dumps(d))
 texts=[x['text'] for x in d.get('content',[]) if x['type']=='text']
 try:return json.loads('\n'.join(texts))
 except ValueError:return '\n'.join(texts)
call('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'caixa-demo-verification','version':'1.0'}})
s.post(url,json={'jsonrpc':'2.0','method':'notifications/initialized'},timeout=20).raise_for_status()
names=sorted(t['name'] for t in call('tools/list')['tools']);print('TOOLS',names,flush=True)
assert names==sorted(['job_templates_list','job_templates_launch_create','jobs_retrieve','jobs_stdout_retrieve'])
x=tool('job_templates_list',{'search':'CAIXA diagnose'});print('Template listing completed',flush=True)
x=tool('job_templates_launch_create',{'id':os.environ.get('DIAGNOSE_TEMPLATE_ID','13'),'requestBody':{}});print('Diagnostic launch accepted',flush=True)
# The official server wraps API responses under status and data.
if isinstance(x,dict) and 'data' in x:x=x['data']
jid=x.get('job',x.get('id'));assert jid
for _ in range(180):
 x=tool('jobs_retrieve',{'id':str(jid)})
 if isinstance(x,dict) and 'data' in x:x=x['data']
 if x['status'] not in ['new','pending','waiting','running']:break
 time.sleep(2)
assert x['status']=='successful',x['status']
out=tool('jobs_stdout_retrieve',{'id':str(jid),'format':'json'})
assert 'PLAY RECAP' in str(out)
print('PASS MCP diagnose job',jid,'successful; stdout retrieved',flush=True)
