"""Generating CloudFormation template."""

from ipaddress import ip_network
from ipify import get_ip
from troposphere import (
    Base64,
    ec2,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Template,
)


ApplicationName = "helloworld"
ApplicationPort = "3000"

GithubAccount = "ealejand"
GithubAnsibleURL = "https://github.com/{}/ansible".format(GithubAccount)

AnsiblePullCmd = \
    "/usr/local/bin/ansible-pull -U {} {}.yml -i localhost".format(
        GithubAnsibleURL,
        ApplicationName
    )

# Start building the template
t = Template()
t.add_description("Effective DevOps in AWS: HelloWorld web application")
t.add_parameter(
    Parameter(
        "KeyPair",
        Description="Name of an existing EC2 KeyPair to SSH",
        Type="AWS::EC2::KeyPair::KeyName",
        ConstraintDescription="must be the name of an existing EC2 KeyPair."
    )
)
t.add_resource(
    ec2.SecurityGroup(
        "SecurityGroup",
        GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
        SecurityGroupIngress=[
            ec2.SecurityGroupRule(
                IpProtocol="tcp",
                FromPort="22",
                ToPort="22",
                CidrIp="0.0.0.0/0"
            ),
            ec2.SecurityGroupRule(
                IpProtocol="tcp",
                FromPort=ApplicationPort,
                ToPort=ApplicationPort,
                CidrIp="0.0.0.0/0"
            )
        ]
    )
)

# Generate the script for launching our web service
ud = Base64(Join('\n', [
    "#!/bin/bash",
    "sudo yum install --enablerepo=epel -y git",
    "pip install ansible",
    AnsiblePullCmd,
    "echo '*/10 * * * * {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)]))

# Create our EC2 instance
t.add_resource(
    ec2.Instance(
        "instance",
        ImageId="ami-0e86606d",
        InstanceType="t2.micro",
        SecurityGroups=[Ref("SecurityGroup")],
        KeyName=Ref("KeyPair"),
        UserData=ud,
    )
)

t.add_output(
    Output(
        "InstancePublicIp",
        Description="Public IP of our instance.",
        Value=GetAtt("instance", "PublicIp"),
    )
)

t.add_output(
    Output(
        "WebUrl",
        Description="Application endpoint",
        Value=Join("", [
            "http://", GetAtt("instance", "PublicDnsName"),
            ":", ApplicationPort
        ])
    )
)

print t.to_json()
