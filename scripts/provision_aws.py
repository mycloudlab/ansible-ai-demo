import json,os,subprocess,requests
from pathlib import Path
env=os.environ.copy();env.update(AWS_DEFAULT_REGION='us-east-1',AWS_PAGER='')
Path('.private').mkdir(mode=0o700,exist_ok=True)
statefile=Path('.private/aws-state.json');state=json.loads(statefile.read_text()) if statefile.exists() else {}
def aws(*args):
 r=subprocess.run(['aws',*args,'--output','json'],capture_output=True,text=True,env=env)
 if r.returncode:raise RuntimeError('AWS operation failed: '+args[0]+' '+args[1]+' '+r.stderr[:300])
 return json.loads(r.stdout or '{}')
def save(k,v):state[k]=v;statefile.write_text(json.dumps(state,indent=2));print(k,v,flush=True);return v
if 'vpc' not in state:save('vpc',aws('ec2','create-vpc','--cidr-block','10.42.0.0/24','--tag-specifications','ResourceType=vpc,Tags=[{Key=Name,Value=caixa-ai-demo}]')['Vpc']['VpcId'])
aws('ec2','modify-vpc-attribute','--vpc-id',state['vpc'],'--enable-dns-support','Value=true')
if 'subnet' not in state:save('subnet',aws('ec2','create-subnet','--vpc-id',state['vpc'],'--cidr-block','10.42.0.0/26','--availability-zone','us-east-1a','--tag-specifications','ResourceType=subnet,Tags=[{Key=Name,Value=caixa-ai-demo}]')['Subnet']['SubnetId'])
if 'igw' not in state:
 save('igw',aws('ec2','create-internet-gateway','--tag-specifications','ResourceType=internet-gateway,Tags=[{Key=Name,Value=caixa-ai-demo}]')['InternetGateway']['InternetGatewayId']);aws('ec2','attach-internet-gateway','--internet-gateway-id',state['igw'],'--vpc-id',state['vpc'])
if 'route_table' not in state:
 save('route_table',aws('ec2','create-route-table','--vpc-id',state['vpc'])['RouteTable']['RouteTableId']);aws('ec2','create-route','--route-table-id',state['route_table'],'--destination-cidr-block','0.0.0.0/0','--gateway-id',state['igw']);save('route_association',aws('ec2','associate-route-table','--route-table-id',state['route_table'],'--subnet-id',state['subnet'])['AssociationId'])
if 'security_group' not in state:
 save('security_group',aws('ec2','create-security-group','--group-name','caixa-ai-demo','--description','CAIXA isolated demo: restricted SSH and web','--vpc-id',state['vpc'])['GroupId'])
 ip=requests.get('https://checkip.amazonaws.com',timeout=20).text.strip();save('operator_ip',ip)
 for port in [22,8080]:aws('ec2','authorize-security-group-ingress','--group-id',state['security_group'],'--protocol','tcp','--port',str(port),'--cidr',ip+'/32')
key=Path('.private/caixa-demo-key')
if not key.exists():subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
if 'key_name' not in state:
 aws('ec2','import-key-pair','--key-name','caixa-ai-demo','--public-key-material','fileb://'+str(key)+'.pub');save('key_name','caixa-ai-demo')
if 'instance_id' not in state:
 ami=aws('ssm','get-parameter','--name','/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id')['Parameter']['Value']
 v=aws('ec2','run-instances','--image-id',ami,'--instance-type','t3.small','--key-name',state['key_name'],'--network-interfaces',json.dumps([{'DeviceIndex':0,'SubnetId':state['subnet'],'Groups':[state['security_group']],'AssociatePublicIpAddress':True}]),'--metadata-options','HttpTokens=required,HttpEndpoint=enabled','--block-device-mappings',json.dumps([{'DeviceName':'/dev/sda1','Ebs':{'VolumeSize':12,'VolumeType':'gp3','Encrypted':True,'DeleteOnTermination':True}}]),'--credit-specification','CpuCredits=standard','--tag-specifications','ResourceType=instance,Tags=[{Key=Name,Value=caixa-ai-demo},{Key=Project,Value=ansible-ai-demo}]','ResourceType=volume,Tags=[{Key=Name,Value=caixa-ai-demo}]')
 save('instance_id',v['Instances'][0]['InstanceId'])
inst=aws('ec2','describe-instances','--instance-ids',state['instance_id'])['Reservations'][0]['Instances'][0]
if 'PublicIpAddress' in inst:save('public_ip',inst['PublicIpAddress'])
