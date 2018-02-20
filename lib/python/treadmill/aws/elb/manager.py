from socket import gethostbyname as nslookup
from treadmill.aws.elb.services import ELBClient
from time import sleep
from random import randrange
import os
import logging

_LOGGER = logging.getLogger(__name__)
getRandomPort = lambda x, y: randrange(x, y)


class ELBManager(ELBClient):
    def __init__(self, root_dir):
        ELBClient.__init__(self)
        self.root_dir = root_dir
        self.endpoint_dir = '{}/endpoints'.format(self.root_dir)
        self.app_groups_dir = '{}/app-groups'.format(self.root_dir)

    def register(self, elb_name, tg_name, endpoints):
        instances = list(self.ec2client.instances.filter(InstanceIds=[i for i, p in endpoints]))
        vpcId = set([instance.vpc_id for instance in instances]).pop()
        usedPorts = [tg.port for tg in self.listTargetGroups()]
        trafficPort = getRandomPort(8000, 8999)
        while trafficPort in usedPorts:
            trafficPort = getRandomPort(8000, 8999)
        tg = self.get_or_create_target_group(tg_name, vpcId, endpoints, 'TCP', trafficPort)
        elb = self.get_or_create_load_balancer(elb_name, vpcId)
        self.get_or_create_elb_listener(elb, tg)
        sg = self.get_or_create_security_group(tg)
        while True:
            try:
                elb_ip = nslookup(elb.dnsName)
                break
            except:
                sleep(3)
        self.update_security_rule(tg, 22)
        [self.update_security_rule(tg, port)
         for instance, port in endpoints]
        [self.attach_security_group(instance, sg) for instance in instances]

    def deregister(self, tg_name):
        tg = self.findTargetGroup(name=tg_name)
        elb = self.findLoadBalancer(name=tg.name.split('-')[0])
        listener = self.findListener(elb, tg.port)
        if listener:
            self.client.delete_listener(ListenerArn=listener.arn)
            _LOGGER.info("Listener {} has been removed".format(listener.name))
        if tg:
            self.client.delete_target_group(TargetGroupArn=tg.arn)
            _LOGGER.info("Target Group {} has been removed (no targets)".format(tg.name))
        if not self.findListener(elb):
            _LOGGER.info("ELB {} has been removed (no target groups)".format(elb.name))
            self.client.delete_load_balancer(LoadBalancerArn=elb.arn)


    def update_security_rule(self, tg, port, revoke=False):
        sg = self.get_or_create_security_group(tg)
        elb = self.findLoadBalancer(name=tg.name.split('-')[0])
        IpPermissions=[{
            "FromPort": port,
            "ToPort": port,
            "IpProtocol": 'tcp',
            "IpRanges": [{
                "CidrIp": "{}/32".format(nslookup(elb.dnsName)),
                "Description": "TG: {}".format(tg.name),
            }]
        }]
        try:
            if revoke:
                sg.revoke_ingress(IpPermissions=IpPermissions)
            else:
                sg.authorize_ingress(IpPermissions=IpPermissions)
        except:
            return

    def attach_security_group(self, instance, security_group):
        all_groups = list(set([s.get('GroupId') for s in instance.security_groups] + [security_group.id]))
        instance.modify_attribute(Groups=all_groups)

    def detach_security_group(self, instance, security_group):
        all_groups = list(set([s.get('GroupId') for s in instance.security_groups] + [security_group.id]))
        all_groups.remove(security_group)
        instance.modify_attribute(Groups=all_groups)

    def add_targets(self, target_group, targets):
        '''
        :param target_group: TargetGroup object
        :param targets: ((:type str instance-id, :type int port), )
        :return: None
        '''
        targetConf = []
        for instanceId, port in targets:
            targetConf.append({
                'Id': instanceId,
                'Port': port,
            })
        self.client.register_targets(TargetGroupArn=target_group.arn, Targets=targetConf)

    def remove_targets(self, target_group, targets):
        '''
        :param target_group: TargetGroup object
        :param targets: ((:type str instance-id, :type int port), )
        :return: None
        '''
        targetConf = []
        currentTargets = self.listTargets(target_group)
        elb_name = target_group.name.split('-')[0]
        elb = self.get_or_create_load_balancer(elb_name, target_group.vpcId)
        elb_ip = nslookup(elb.dnsName)
        for target in currentTargets:
            if (target.name, target.port) not in targets:
                targetConf.append({
                    'Id': target.name,
                    'Port': target.port,
                })
                # Detach security group if no more ports used on this instance
                proid_dir = '{}/{}'.format(self.endpoint_dir, elb_name)
                endpoint = "{}:{}".format(target.name, target.port)
                all_endpoints = [open("{}/{}".format(proid_dir, file)).read() for file in os.listdir(proid_dir)]
                if not endpoint in all_endpoints:
                    self.update_security_rule(target_group, target.port, revoke=True)
        self.client.deregister_targets(TargetGroupArn=target_group.arn, Targets=targetConf)
        if not self.listTargets(target_group):
            # if no more targets remove security_group
            security_group = self.get_or_create_security_group(target_group)
            security_group.delete()
        return targetConf

