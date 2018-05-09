# Web App Deployment
## High Level Architecture

1. One VPC with two private and two public subnets placed in two separate AZs (us-west-2a and us-west-2b) in Oregon (us-west-2) region.
2. One MySQL RDS instance t2.micro running in one of the private subnet.
3. Two web servers running in two different AZs, again in the private subnet.
4. RDS receives traffic only from the web servers on port 3306.
5. NAT gateway is running in a public subnet to provide internet connectivity to resources running in private subnets.
6. ELB is the public facing resource which receives all the traffic from internet and pass it to internal web servers.
7. Users communicate over HTTPS, which means data in-transit is secure. 
8. This app is highly available and fault tolerant by design. Autoscaling keeps one instance running in each AZ. 
    In case of any failure, a new instance will be launched automatically.
9. CodeDeploy is integrated with autoscaling group so that deployment can be done on any new instance automatically.
10. Github has been integrated with CodeDeploy Continuous Deployment.
11. A bastion host is launched in public subnet which can be used to access internal servers.

## How the infrastructure is created?
I have written a script "create_infra.py" placed in "aws" folder".
### Script creates following components:
  1. VPC
  2. Public and Private Subnets
  3. IGW and NAT GW
  4. Security Groups - one each for ALB, Public Subnet, Private Subnet and RDS 
  5. Route Tables and adding appropriate routes
  6. ALB and Listener
  7. Target Groups
  8. AutoScaling Launch Configuration
  9. AutoScaling Group
  10. KeyPair
  11. RDS instance
  12. CodeDeploy application and deployment group
### Pre-requisite to use this script
  1. Configure your local environment with AWS keys using "aws configure" command.
  2. Edit the top section of script called editable section. Here you can specify region, profile, CIDR blocks for VPC and Subnets, and AMI ID
  3. I am using a custom baked AMI which contains installation of Apache, PHP and codedeploy agent. It helps in lowering the instance boot time.

## New features that can be added but out of scope of this assignment.

  1. To make the application scalable by using autoscaling with cloudwatch.
  2. Allow deployment rollback in case of any failure. It can be achieved by triggering a Lambda function on any failed deployment, which makes a call to CodeDeploy, fetch the last successful deployment and trigger that again.
  3. Make database highly available by launching RDS in Multi-AZ mode.
  4. Manage session state with ElastiCache
