import logging
from os import path
from treadmill.aws.dns.services import DNSClient
_LOGGER = logging.getLogger(__name__)


class DNSManager():
    def __init__(self):
        self.dnsclient = DNSClient()

    def registerDNS(self, proid, server, app_name, protocol, endpoints):
        dns_record = self.dnsclient.generate_srv_record(proid,
                                                        server,
                                                        app_name,
                                                        protocol,
                                                        endpoints)
        self.dnsclient.add_srv_dns(dns_record['idnsname'],
                                   dns_record['record'])

    def syncDNS(self, zk_contexts):
        mirror_list = []

        for app in zk_contexts:
            rec = self.dnsclient.generate_srv_record(app['context'].proid,
                                                     app['context'].server,
                                                     app['context'].app,
                                                     app['context'].protocol,
                                                     app['endpoints'])
            if rec:
                mirror_list.append(rec)

        self.dnsclient.mirror_zookeeper(mirror_list)

