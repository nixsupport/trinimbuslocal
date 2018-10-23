import boto3
import time

#Start of editable section
Region="us-west-2"
Profile="trinimbus"
ami_id="ami-a3a9d8db"

AZ1="us-west-2a"
AZ2="us-west-2b"

VPCCidr="10.0.0.0/16"
PubSub1Cidr="10.0.2.0/24"
PubSub2Cidr="10.0.4.0/24"
PriSub1Cidr="10.0.1.0/24"
PriSub2Cidr="10.0.3.0/24"
#End of editable section

ec2Session = boto3.Session(profile_name=Profile,region_name=Region)
ec2Client = ec2Session.client('ec2')
ec2Res = ec2Session.resource('ec2')

MyTags = [{"Key":"Name","Value":"flyhigh"},{"Key":"env","Value":"dev"}]

print "Building infrastructure in %s region" %(Region)
#Create VPC 
create_vpc_resp=ec2Client.create_vpc(CidrBlock=VPCCidr)
vpc=ec2Res.Vpc(create_vpc_resp["Vpc"]["VpcId"])
vpc_id=create_vpc_resp["Vpc"]["VpcId"]
vpc.wait_until_available()
print "Created VPC: %s" %(vpc_id)
#Create Subnets

PubSub1=vpc.create_subnet(CidrBlock=PubSub1Cidr,AvailabilityZone=AZ1)
PubSub2=vpc.create_subnet(CidrBlock=PubSub2Cidr,AvailabilityZone=AZ2)
print "Created Public Subnets: %s %s " % (PubSub1.id, PubSub2.id)

PriSub1=vpc.create_subnet(CidrBlock=PriSub1Cidr,AvailabilityZone=AZ1)
PriSub2=vpc.create_subnet(CidrBlock=PriSub2Cidr,AvailabilityZone=AZ2)

print "Created Private Subnets: %s %s" % (PriSub1.id, PriSub2.id)

#Enable DNS hostnames in new VPC

vpc.modify_attribute(EnableDnsSupport = {'Value':True})
vpc.modify_attribute(EnableDnsHostnames = {'Value':True})

#Create IGW

create_ig_resp=ec2Client.create_internet_gateway()
igw_id=create_ig_resp["InternetGateway"]["InternetGatewayId"]
igw=ec2Res.InternetGateway(igw_id)
vpc.attach_internet_gateway(InternetGatewayId=igw_id)

print "Created and attached IGW: %s" % (igw_id)
#Route Tables

PubRouteTable=ec2Res.create_route_table(VpcId=vpc_id)
PubRouteTable.associate_with_subnet(SubnetId=PubSub1.id)
PubRouteTable.associate_with_subnet(SubnetId=PubSub2.id)
print "Created Public Route Table"

PriRouteTable=ec2Res.create_route_table(VpcId=vpc_id)
PriRouteTable.associate_with_subnet(SubnetId=PriSub1.id)
PriRouteTable.associate_with_subnet(SubnetId=PriSub2.id)
print "Created Private Route Table"
#Internet traffic route
outflowRoute=ec2Client.create_route(RouteTableId=PubRouteTable.id,DestinationCidrBlock="0.0.0.0/0",GatewayId=igw_id)
print "Added IGW route to public route table"

#Allocate EIP For NAT gateway
eip_resp=ec2Client.allocate_address(Domain="vpc")
allocation_id=eip_resp["AllocationId"]

#Create NAT Gateway 
nat_resp = ec2Client.create_nat_gateway(AllocationId=allocation_id,SubnetId=PubSub1.id)
nat_id = nat_resp["NatGateway"]["NatGatewayId"]
print "Created NAT Gateway: %s" %(nat_id)
print "Waiting for NAT Gateway to be available"
#Wait for NAT to be available. It will take a few minutes
nat_waiter = ec2Client.get_waiter('nat_gateway_available')
nat_waiter.wait(NatGatewayIds=[nat_id])
#Tag NAT GW
ec2Client.create_tags(Resources=[nat_id],Tags=MyTags)

natroute = ec2Client.create_route(RouteTableId=PriRouteTable.id,DestinationCidrBlock="0.0.0.0/0",NatGatewayId=nat_id)
print "Added NAT Route to Private Route Table"
#Tag them all
print "Tagging all resources"
vpc.create_tags(Tags=MyTags)
PubSub1.create_tags(Tags=MyTags)
PubSub2.create_tags(Tags=MyTags)
PriSub1.create_tags(Tags=MyTags)
PriSub2.create_tags(Tags=MyTags)

igw.create_tags(Tags=MyTags)
PubRouteTable.create_tags(Tags=MyTags)
PriRouteTable.create_tags(Tags=MyTags)

#Create Public and Private Security Groups
print "Creating Security Groups"
frontendSG = ec2Res.create_security_group(GroupName="frontendSG",Description="SG for ELB",VpcId=vpc_id)
pubSG = ec2Res.create_security_group(GroupName="pubSG",Description="SG for Public Subnets",VpcId=vpc_id)
priSG = ec2Res.create_security_group(GroupName="priSG",Description="SG for Private Subnets",VpcId=vpc_id)
bastionHostSG = ec2Res.create_security_group(GroupName="bastionHostSG",Description="SG for Bastion Host",VpcId=vpc_id)
rdsSG = ec2Res.create_security_group(GroupName="rdsSG",Description="SG for RDS",VpcId=vpc_id)

print "Tagging Security Groups"
frontendSG.create_tags(Tags=MyTags)
pubSG.create_tags(Tags=MyTags)
priSG.create_tags(Tags=MyTags)
bastionHostSG.create_tags(Tags=MyTags)
rdsSG.create_tags(Tags=MyTags)

#Add Security Group rules
print "Adding Rules in Security Groups"
ec2Client.authorize_security_group_ingress(GroupId=bastionHostSG.id,IpProtocol="tcp",FromPort=22,ToPort=22,CidrIp="0.0.0.0/0")

ec2Client.authorize_security_group_ingress(GroupId=frontendSG.id,IpProtocol="tcp",FromPort=80,ToPort=80,CidrIp="0.0.0.0/0")
ec2Client.authorize_security_group_ingress(GroupId=frontendSG.id,IpProtocol="tcp",FromPort=443,ToPort=443,CidrIp="0.0.0.0/0")

ec2Client.authorize_security_group_ingress(GroupId=pubSG.id, IpPermissions=[{'IpProtocol': 'tcp',"FromPort": 80,"ToPort":80,"UserIdGroupPairs":[{"GroupId":frontendSG.id}]}])
ec2Client.authorize_security_group_ingress(GroupId=priSG.id, IpPermissions=[{'IpProtocol': 'tcp',"FromPort": 80,"ToPort":80,"UserIdGroupPairs":[{"GroupId":pubSG.id}]}])
ec2Client.authorize_security_group_ingress(GroupId=priSG.id, IpPermissions=[{'IpProtocol': 'tcp',"FromPort": 80,"ToPort":80,"UserIdGroupPairs":[{"GroupId":frontendSG.id}]}])                                                                                      
ec2Client.authorize_security_group_ingress(GroupId=priSG.id, IpPermissions=[{'IpProtocol': 'tcp',"FromPort": 22,"ToPort":22,"UserIdGroupPairs":[{"GroupId":bastionHostSG.id}]}])
ec2Client.authorize_security_group_ingress(GroupId=rdsSG.id, IpPermissions=[{'IpProtocol': 'tcp',"FromPort": 3306,"ToPort":3306,"UserIdGroupPairs":[{"GroupId":bastionHostSG.id}]}])
ec2Client.authorize_security_group_ingress(GroupId=rdsSG.id, IpPermissions=[{'IpProtocol': 'tcp',"FromPort": 3306,"ToPort":3306,"UserIdGroupPairs":[{"GroupId":priSG.id}]}])
print "--------------------------------------"                                           
print "VPC Setup Completed"
print "--------------------------------------"
print "Creating Application Load Balancer"
albClient = ec2Session.client('elbv2')
alb_resp = albClient.create_load_balancer(Name="flyhighLB",Subnets=[PubSub1.id,PubSub2.id],SecurityGroups=[frontendSG.id],Scheme='internet-facing',Tags=MyTags)
alb_arn = alb_resp["LoadBalancers"][0]["LoadBalancerArn"]
#Wait for Load Balancer to be available

print "Waiting for ALB to be available. It will take a while"
alb_waiter = albClient.get_waiter('load_balancer_available')
alb_waiter.wait(LoadBalancerArns=[alb_arn])
print "ALB ARN: %s " % (alb_arn)
print "----------------------------"
print "Creating Target Group"
tg_resp = albClient.create_target_group(Name='flyhighTG',Protocol='HTTP',Port=80,VpcId=vpc_id,HealthCheckPath='/')
tg_arn = tg_resp["TargetGroups"][0]["TargetGroupArn"]
print "Target Group ARN: %s" % (tg_arn)
#Wait for Target Groups to be in service
#####
key_resp = ec2Client.create_key_pair(KeyName="flyhighKP")
print "Generating Key %s" % (key_resp['KeyName'])
print key_resp['KeyMaterial']
####

#PriSub1Id = "subnet-0a6f3576a8a7f7918"
#PriSub1Id = PriSub1Id[1:-1]
#PriSub2Id = "subnet-07043364aff30c85b"
#PriSub = PriSub1Id,PriSub2Id

PriSubId = ','.join([PriSub1.id,PriSub2.id])
#print PriSubId
#PriSub2Id = PriSub2Id[1:-1]

print "------------------------------"
print "Creating AutoScaling"
asClient = ec2Session.client('autoscaling')
lc_resp = asClient.create_launch_configuration(LaunchConfigurationName='flyhighLC',ImageId=ami_id,KeyName='flyhighKP',SecurityGroups=[priSG.id],InstanceType='t2.micro',IamInstanceProfile="assignments")
asg_resp = asClient.create_auto_scaling_group(AutoScalingGroupName='flyhighASG',LaunchConfigurationName='flyhighLC',MinSize=2,MaxSize=2,DesiredCapacity=2,VPCZoneIdentifier=PriSubId,TargetGroupARNs=[tg_arn])
#create tags
	
print "Waiting for autoscaling to kick-in"
time.sleep(60)
asClient.attach_load_balancer_target_groups(AutoScalingGroupName='flyhighASG',TargetGroupARNs=[tg_arn])

#####
# Placeholder for getting Certificate ARN
#####

#Add Listener
print "Creating ALB Listener"
lstnr_resp = albClient.create_listener(LoadBalancerArn=alb_arn,Protocol='HTTPS',Port=443,Certificates=[{'CertificateArn':'arn:aws:iam::272462672480:server-certificate/flyhighCert'}],DefaultActions=[{'Type':'forward','TargetGroupArn':tg_arn}])
time.sleep(20)
print "Listener Created"
print "------------------"


print "Creating Database Infrastructure"

#Create DB Subnet Group
dbSubnetGroup = "flyhighRDSSubGrp"
dbName = "employee"
dbInstance = "flyhighdbinstance"
rdsClient=ec2Session.client('rds')
rdsSG_resp = rdsClient.create_db_subnet_group(DBSubnetGroupName=dbSubnetGroup,DBSubnetGroupDescription=dbSubnetGroup,SubnetIds=[PriSub1.id,PriSub2.id],Tags=MyTags)
print "Creating RDS DB Instance"
rdsDBInstance_resp = rdsClient.create_db_instance(DBName=dbName,
	DBInstanceIdentifier=dbInstance,
	AllocatedStorage=20,
	StorageType='gp2',
	DBInstanceClass='db.t2.micro',
	Engine='mysql',
	MasterUsername='flyhighdbU',
	MasterUserPassword='flyhighdbP',
	VpcSecurityGroupIds=[rdsSG.id],
	DBSubnetGroupName=dbSubnetGroup,
	AvailabilityZone='us-west-2b',
	BackupRetentionPeriod=0,
	MultiAZ=False)
print "Waiting for DB Instance to be available. It will take several minutes"
rds_waiter=rdsClient.get_waiter('db_instance_available')
rds_waiter.wait(DBInstanceIdentifier=dbInstance)

rdsClient=ec2Session.client('rds')
dbInstance = "flyhighdbinstance"
#Describe DB Instances:
rdsDBs = rdsClient.describe_db_instances(DBInstanceIdentifier=dbInstance)
print "Copy below information"
print "----------------------------"
print "%s@%s:%s" %(rdsDBs['DBInstances'][0]['MasterUsername'],rdsDBs['DBInstances'][0]['Endpoint']['Address'],rdsDBs['DBInstances'][0]['Endpoint']['Port'])
print "------------------------------------------"
print "Web and Database configuration completed"
print "------------------------------------------"
print "Creating CodeDeploy artifacts"

cdClient = ec2Session.client('codedeploy')
cdappName = "flyhighWebApp"
print 'Creating CodeDeploy application'
cd_createApp_resp = cdClient.create_application(applicationName=cdappName,computePlatform="Server")
print 'Creating CodeDeploy Deployment Group'
cd_create_depGrp = cdClient.create_deployment_group(applicationName=cdappName,deploymentGroupName="flyhighDepGrp",autoScalingGroups=['flyhighASG'],
	serviceRoleArn='arn:aws:iam::272462672480:role/aws-codedeploy-service-role',
	)
print "------------------------"
print "Congratulations! Required infrastructure has been setup."
print "Please configure GitHub and start deploying"
print "-------------------------"