import dns.resolver
import logging
from os import environ
from random import choice
import requests
from requests_kerberos import HTTPKerberosAuth

_LOGGER = logging.getLogger(__name__)
_KERBEROS_AUTH = HTTPKerberosAuth()

DEFAULT_WEIGHT = 10
DEFAULT_PRIORITY = 10
API_VERSION = '2.28'


class DNSClient():
    ''' Updates IPA DNS with ZK mirror on disk '''

    def __init__(self):
        self.cell_name = environ.get('TREADMILL_CELL')
        self.domain = environ.get('TREADMILL_DNS_DOMAIN')
        self.ipa_cert_location = '/etc/ipa/ca.crt'

        # Strip trailing period as it breaks SSL
        self.ipa_server_hostn = self.get_ipa_server_from_dns(self.domain)[:-1]
        self.ipa_srv_address = 'https://{}/ipa'.format(self.ipa_server_hostn)
        self.ipa_srv_api_address = '{}/session/json'.format(
            self.ipa_srv_address)
        self.referer = {'referer': self.ipa_srv_address}

    def get_ipa_server_from_dns(self, tm_dns_domain):
        ''' Looks up random IPA server from DNS SRV records '''
        raw_results = [result.to_text() for result in
                       dns.resolver.query(
                            '_kerberos._tcp.{}'.format(tm_dns_domain),
                            "SRV")
                       ]
        return choice(raw_results).split()[-1]

    def _post(self, payload=None, auth=_KERBEROS_AUTH):
        ''' Submits formatted JSON to IPA server DNS.
            Uses requests_kerberos module for Kerberos authentication with IPA.
        '''
        response = requests.post(self.ipa_srv_api_address,
                                 json=payload,
                                 auth=auth,
                                 headers=self.referer,
                                 verify=self.ipa_cert_location)
        return response

    def add_srv_dns(self, record_name, record_value):
        ''' Add new DNS record to IPA server DNS '''
        payload = {'method': 'dnsrecord_add',
                   'params': [[self.domain, record_name],
                              {'srvrecord': record_value,
                               'version': API_VERSION}
                              ],
                   'id': 0}
        r = self._post(payload)
        try:
            return r.json()
        except Exception as e:
            _LOGGER.error(r, str(e))

    def del_srv_dns(self, record_name, record_value):
        ''' Delete DNS record from IPA server DNS '''
        payload = {'method': 'dnsrecord_del',
                   'params': [[self.domain, record_name],
                              {'srvrecord': record_value,
                               'version': API_VERSION}
                              ],
                   'id': 0}
        r = self._post(payload)
        try:
            return r.json()
        except Exception as e:
            _LOGGER.error(r, str(e))
            return None

    def get_cell_dns(self):
        ''' Retrieve all DNS records from IPA server DNS '''
        payload = {'method': 'dnsrecord_find',
                   'params': [[self.domain],
                              {'version': API_VERSION}
                              ],
                   'id': 0}
        r = self._post(payload)
        try:
            return r.json()
        except Exception as e:
            _LOGGER.error(r, str(e))
            return None

    def get_app_dns(self, idnsname):
        ''' Retrieve matching DNS record from server '''
        payload = {'method': 'dnsrecord_find',
                   'params': [[self.domain, idnsname],
                              {'version': API_VERSION},
                              ],
                   'id': 0}
        r = self._post(payload)
        try:
            _LOGGER.info('Retrieved DNS: {}'.format(r.text))
            return r.json()
        except Exception as e:
            _LOGGER.error(r, str(e))
            return None

    def generate_srv_record(self, proid, server,
                            app_name, protocol, endpoints):
        _LOGGER.debug('Generating DNS record from: {} {} {} {} {}'.format(
            proid, server, app_name, protocol, endpoints[0]))

        host, port = endpoints[0]
        idnsname = '_{}._{}.{}.{}'.format(server,
                                          protocol,
                                          app_name,
                                          self.cell_name)

        record = '{} {} {} {}.'.format(DEFAULT_WEIGHT,
                                       DEFAULT_PRIORITY,
                                       port,
                                       host)

        dns_record = {'type': 'srvrecord',
                      'idnsname': idnsname,
                      'record': record}

        _LOGGER.debug('Generated DNS record: {}'.format(dns_record))
        return dns_record

    def format_raw_srv_records(self, raw_records):
        ipa_dns_records = []

        # Get SRV records
        fmt_records = [rec for rec
                       in raw_records['result']['result']
                       if 'srvrecord' in rec
                       ]

        # Extract individual entries from SRV record
        for record in [f_rec for f_rec in fmt_records
                       if self.cell_name in f_rec['idnsname'][0]
                       ]:
            for srvrecord in record['srvrecord']:
                ipa_dns_records.append({'type': 'srvrecord',
                                        'dn': record['dn'],
                                        'idnsname': record['idnsname'][0],
                                        'record': srvrecord
                                        }
                                       )
        return ipa_dns_records

    def find_app_dns(self, server, protocol, app_name):
        ''' This function gets a returns a list of SRV records in dictionary
            format sourced from IPA DNS matching app_name.
        '''
        idnsname = '_{}._{}.{}.{}'.format(server,
                                          protocol,
                                          app_name,
                                          self.cell_name)

        _LOGGER.debug('Generated idnsname: {}'.format(idnsname))

        raw_records = self.get_app_dns(idnsname)
        return self.format_raw_srv_records(raw_records)

    def find_cell_dns(self):
        ''' This function gets a returns a list of SRV records in dictionary
            format sourced from IPA DNS.
        '''
        raw_records = self.get_cell_dns()
        return self.format_raw_srv_records(raw_records)

    def mirror_zookeeper(self, zk_records):
        ''' This function gets a list of records from Zookeeper and from IPA
            DNS, generates an index of each record list, then adds any new
            records & deletes any old records by comparing each list against
            the other's index.
        '''
        ipa_records = self.find_cell_dns()
        zk_record_list = [z['record'] for z in zk_records]
        ipa_record_list = [i['record'] for i in ipa_records]

        # Add new records from Zookeeper
        for z_rec in zk_records:
            if z_rec['record'] not in ipa_record_list:
                _LOGGER.info('Add record: {}'.format(z_rec))
                self.add_srv_dns(z_rec['idnsname'], z_rec['record'])

        # Delete bad records in IPA DNS
        for i_rec in ipa_records:
            if i_rec['record'] not in zk_record_list:
                _LOGGER.info('Delete record: {}'.format(i_rec))
                self.del_srv_dns(i_rec['idnsname'], i_rec['record'])

