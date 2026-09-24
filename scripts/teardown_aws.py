#!/usr/bin/env python3
"""Delete only the demo resources in .private/aws-state.json. Dry run by default."""
import json,subprocess,sys
from pathlib import Path
s=json.loads(Path('.private/aws-state.json').read_text())
commands=[
 ['ec2','terminate-instances','--instance-ids',s['instance_id']],
 ['ec2','wait','instance-terminated','--instance-ids',s['instance_id']],
 ['ec2','delete-key-pair','--key-name',s['key_name']],
 ['ec2','delete-security-group','--group-id',s['security_group']],
 ['ec2','disassociate-route-table','--association-id',s['route_association']],
 ['ec2','delete-route-table','--route-table-id',s['route_table']],
 ['ec2','delete-subnet','--subnet-id',s['subnet']],
 ['ec2','detach-internet-gateway','--internet-gateway-id',s['igw'],'--vpc-id',s['vpc']],
 ['ec2','delete-internet-gateway','--internet-gateway-id',s['igw']],
 ['ec2','delete-vpc','--vpc-id',s['vpc']]]
if '--execute' not in sys.argv:
 for c in commands:print('aws --region us-east-1 '+' '.join(c))
 print('Review the resource IDs; use --execute only when ready to destroy the demo and its data.')
 sys.exit()
r=subprocess.run(['aws','--region','us-east-1','ec2','describe-instances','--instance-ids',s['instance_id'],'--output','json'],check=True,capture_output=True,text=True)
i=json.loads(r.stdout)['Reservations'][0]['Instances'][0]
assert i['VpcId']==s['vpc'] and {'Key':'Project','Value':'ansible-ai-demo'} in i['Tags'],'Resource ownership mismatch'
for c in commands:subprocess.run(['aws','--region','us-east-1',*c],check=True)
