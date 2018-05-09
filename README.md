#A simple web app to deploy on AWS with RDS connectivity
#Infrastructure as code

Below is the high level architecture of this assignment.

1. One VPC with two private and two public subnets placed in two separate AZs (us-east-1a and us-east-1b) in N. Virginia region.
2. One MySQL RDS instance t2.micro running in one of the private subnet.
3. Two web servers running in two different AZs, again in the private subnet.
4. RDS receives traffic only from the web servers on port 3306.
5. NAT gateway is running in a public subnet to provide internet connectivity to resources running in private subnets.
6. ELB is the public facing resource which receives all the traffic from internet and pass it to internal web servers.
7. Users communicate over HTTPS, which means data in-transit is secure. 
8. Any user try to access the web app over HTTP will be redirected to HTTPS.
9. This app is highly available and fault tolerant by design. Autoscaling keeps one instance running in each AZ. In case of any failure, a new instance will be launched automatically.
10. CodeDeploy is integrated with autoscaling group so that deployment can be done on any new instance automatically.
11. Github has been integrated with CodeDeploy so that any new push in Git will trigger the deployment.

##How the infrastructure is created?
Creation of VPC and its componenets like IGW, NAT GW, Subnets, Security Groups, Route tables along with configuraiton like adding routes in the route tables, inbound rules for security groups, etc are implemented using Python.
The script "create_infra.py" can be found in the "aws" folder. It can be launched to create identical environment. 
A custom AMI is baked to launch instances in Autoscaling group. The custom AMI contains installation and configuration of PHP and Apache. It helps in reducing the overall time for a new instance to start serving requests.


##Testing
In order to test high availability and fault tolerance, try shutting down one instance manually. Application can bear this outage and launch a new instance and start responding to user requests in a short time.

New features that can be added but out of scope of this assignment.

1. To make the application scalable by using autoscaling with cloudwatch.
2. Allow deployment rollback in case of any failure. It can be achieved by triggering a Lambda function on any failed deployment, which makes a call to CodeDeploy, fetch the last successful deployment and trigger that again.
3. Make database highly available by launching RDS in Multi-AZ mode.
4. Manage session state with ElastiCache
