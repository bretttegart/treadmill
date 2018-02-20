from treadmill.infra import constants
from treadmill.infra.connection import Connection
import re
import logging

_LOGGER = logging.getLogger(__name__)

class Listener(object):
    def __init__(self, data={}):
        if 'Listeners' in data:
            data = data.get('Listeners')
        self.arn = data.get('ListenerArn')
        self.loadBalancerArn = data.get('LoadBalancerArn')
        self.port = data.get('Port')
        self.protocol = data.get('Protocol', 'TCP')
        self.certificates = data.get('Certificates', [])
        self.defaultActions = data.get('DefaultActions')
        if self.protocol == 'HTTPS':
            self.sslPolicy = data.get('SslPolicy', 'ELBSecurityPolicy-TLS-1-2-2017-01')

        try:
            self.loadBalancerName = self.loadBalancerArn.split('/')[2]
            self.name = "{}:{}".format(self.loadBalancerName, self.port)
        except:
            self.name = "<None>"


    def __str__(self):
        return "<ELB_Listener({})>".format(self.name)

    def __repr__(self):
        return "<ELB_Listener({})>".format(self.name)


    def getConfiguration(self):
        conf = {
            "LoadBalancerArn": self.loadBalancerArn,
            "Protocol": self.protocol,
            "Port": self.port,
            "Certificates": self.certificates,
            "DefaultActions": self.defaultActions,
        }
        if self.protocol == 'HTTPS':
            conf["SslPolicy"] = self.sslPolicy
        return conf


class LoadBalancer(object):
    def __init__(self, data={}):
        if 'LoadBalancers' in data:
            data = data.get('LoadBalancers')
        self.name = data.get('LoadBalancerName', None)
        self.arn = data.get('LoadBalancerArn', None)
        self.vpcId = data.get('VpcId', None)
        self.type = data.get('Type', 'network')
        self.status = data.get('State').get('Code') if 'State' in data else None
        self.scheme = data.get('Scheme', 'internal')
        self.ipProtocol = data.get('IpAddressType', 'ipv4')
        self.dnsName = data.get('DNSName', None)
        self.dnsZone = data.get('CanonicalHostedZoneId', None)
        self.creationDate = data.get('CreatedTime', None)
        self.availabilityZones = data.get('AvailabilityZones', None)
        self.subnets = [] if not self.availabilityZones else [subnet["SubnetId"] for subnet in self.availabilityZones]
        self.securityGroups = data.get('SecurityGroups', None)

    def __str__(self):
        return "<LoadBalancer({})>".format(self.name)

    def __repr__(self):
        return "<LoadBalancer({})>".format(self.name)

    def getConfiguration(self):
        return {
            "Name": self.name,
            # "Subnets": self.subnets,
             "Subnets": ['subnet-b4763a98'],
            # "SecurityGroups": self.securityGroups,
            "Scheme": self.scheme,
            "Tags": [
                {
                    'Key': 'name',
                    'Value': self.name
                },
            ],
            "IpAddressType": self.ipProtocol,
            "Type": self.type,
        }


class TargetGroup(object):
    def __init__(self, data={}):
        if 'TargetGroup' in data:
            data = data.get('TargetGroup')
        self.port = data.get('Port')
        self.name = data.get('TargetGroupName')
        self.loadBalancerArns = data.get('LoadBalancerArns')
        self.arn = data.get('TargetGroupArn')
        self.vpcId = data.get('VpcId')
        self.targetType = data.get('TargetType', 'instance')
        self.protocol = data.get('Protocol', 'TCP')
        self.healthCheckProtocol = data.get('HealthCheckProtocol', 'TCP')
        self.healthCheckPort = data.get('HealthCheckPort', 22)
        self.healthCheckTimeoutSeconds = data.get('HealthCheckTimeoutSeconds', 5)
        self.healthCheckIntervalSeconds = data.get('HealthCheckIntervalSeconds', 10)
        self.healthyThresholdCount = data.get('HealthyThresholdCount', 3)
        self.unhealthyThresholdCount = data.get('UnhealthyThresholdCount', 3)
        if self.healthCheckProtocol and self.healthCheckProtocol.startswith('HTTP'):
            self.healthCheckPath = data.get('HealthCheckPath', '')
            self.matcher = data.get('Matcher', {'HttpCode': 200})

    def __str__(self):
        return "<TargetGroup({})>".format(self.name)

    def __repr__(self):
        return "<TargetGroup({})>".format(self.name)

    def getConfiguration(self):
        conf = {
            "Name": self.name,
            "Protocol": self.protocol,
            "Port": self.port,
            "VpcId": self.vpcId,
            "HealthCheckProtocol": self.healthCheckProtocol,
            "HealthCheckPort": str(self.healthCheckPort),
            "HealthCheckIntervalSeconds": self.healthCheckIntervalSeconds,
            "HealthyThresholdCount": self.healthyThresholdCount,
            "UnhealthyThresholdCount": self.unhealthyThresholdCount,
        }
        if self.healthCheckProtocol == 'HTTP':
            # "TargetType": self.targetType,
            # "HealthCheckTimeoutSeconds": self.healthCheckTimeoutSeconds,
            conf["Matcher"] = getattr(self, "matcher", {'HttpCode': ''}),
            conf["HealthCheckPath"] = getattr(self, "healthCheckPath", '/')
        return conf

class Target(object):
    def __init__(self, data={}):
        self.healthCheckPort = data.get('HealthCheckPort')
        self.name = data.get("Target").get("Id")
        self.port = data.get("Target").get("Port")
        self.status = data.get('TargetHealth').get('State')

    def __str__(self):
        return "<Target({})>".format(self.name)

    def __repr__(self):
        return "<Target({})>".format(self.name)


class ELBClient(object):
    def __init__(self):
        self.client = Connection(resource=constants.ELB, service_resource=False)
        self.ec2client = Connection(resource=constants.EC2, service_resource=True)

    def listLoadBalancers(self):
        elbs = []
        paginator = self.client.get_paginator('describe_load_balancers')
        [elbs.extend([LoadBalancer(elb) for elb in page['LoadBalancers']])
            for page in paginator.paginate()
         ]
        return elbs

    def listTargetGroups(self):
        tgs = []
        paginator = self.client.get_paginator('describe_target_groups')
        [tgs.extend([TargetGroup(tg) for tg in page['TargetGroups']])
            for page in paginator.paginate()
         ]
        return tgs

    def listELBListeners(self, elb):
        listeners = []
        paginator = self.client.get_paginator('describe_listeners')
        [listeners.extend([Listener(lstn) for lstn in page['Listeners']])
            for page in paginator.paginate(LoadBalancerArn=elb.arn)
         ]
        return listeners

    def listTargets(self, tg):
        if not tg:
            return []
        targets = self.client.describe_target_health(TargetGroupArn=tg.arn)
        return [Target(t) for t in targets.get('TargetHealthDescriptions')]

    def findLoadBalancer(self, name=None, regex=None):
        elbs = self.listLoadBalancers()
        if name:
            elbs = list(filter(lambda elb: elb.name == name, elbs))
        elif regex:
            elbs = list(filter(lambda elb: re.search(regex, elb.name), elbs))
        return elbs.pop() if elbs else []

    def findTargetGroup(self, name=None, regex=None):
        tgs = self.listTargetGroups()
        if name:
            tgs = list(filter(lambda tg: tg.name == name, tgs))
        elif regex:
            tgs =  list(filter(lambda tg: re.search(regex, tg.name), tgs))
        return tgs.pop() if tgs else []

    def findListener(self, elb, port=None):
        listeners = self.listELBListeners(elb)
        if port:
            listeners = list(filter(lambda lstn: lstn.port == port, listeners))
        return listeners.pop() if listeners else []


    def get_or_create_security_group(self, target_group):
        elb_name = target_group.name.split('-')[0]
        try:
            sg = [sg for sg in list(self.ec2client.security_groups.all())
                  if sg.vpc_id == target_group.vpcId
                  and sg.group_name == elb_name].pop()
        except:
            sg = self.ec2client.create_security_group(
                Description="treadmill loadbalancer healthCheck",
                GroupName=elb_name,
                VpcId=target_group.vpcId)
        return sg

    def get_or_create_target_group(self, tg_name, vpc, targets, protocol, port):
        '''
        :param tg_name: target group name
        :param targets:
        :param protocol:
        :param port:
        :return:
        '''
        tg = self.findTargetGroup(name=tg_name)
        instances = list(self.ec2client.instances.filter(InstanceIds=[instance_id for instance_id, port in targets]))
        if not tg:
            tg = TargetGroup()
            tg.name = tg_name
            tg.vpcId = vpc
            tg.protocol = protocol
            tg.port = port
            self.client.create_target_group(**tg.getConfiguration())
            tg = self.findTargetGroup(tg.name)
            tg.subnets = [instance.subnet_id for instance in instances]
            _LOGGER.info("Added new target Group: {}".format(tg.name))
        return tg

    def get_or_create_load_balancer(self, elb_name, vpcId, security_groups=[]):
        elb = self.findLoadBalancer(name=elb_name)
        if not elb:
            elb = LoadBalancer()
            elb.name = elb_name
            vpc = list(self.ec2client.vpcs.filter(VpcIds=[vpcId])).pop()
            availabilityZones = {}
            for subnet in vpc.subnets.all():
                availabilityZones[subnet.availability_zone] = subnet.subnet_id
            elb.subnets = [availabilityZones[az] for az in availabilityZones]
            elb.securityGroups = security_groups
            self.client.create_load_balancer(**elb.getConfiguration())
            elb = self.findLoadBalancer(name=elb.name)
            _LOGGER.info("Added new ELB: {}".format(elb_name))
        return elb

    def get_or_create_elb_listener(self, elb, target_group):
        listener = self.findListener(elb, target_group.port)
        if not listener:
            listener = Listener()
            listener.loadBalancerArn = elb.arn
            listener.port = target_group.port
            listener.defaultActions = [
                {'Type': 'forward',
                'TargetGroupArn': target_group.arn}
            ]
            self.client.create_listener(**listener.getConfiguration())
            listener = self.findListener(elb, target_group.port)
            _LOGGER.info("Added new listener: {} for target group {}".format(listener.name, target_group.name))
        return listener

