"""Forward Kerberos tickets to the cell ticket locker.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import socket
import sys

import click

from treadmill import cli
from treadmill import context
from treadmill import dnsutils
from treadmill import exc
from treadmill import restclient
from treadmill import subproc

_LOGGER = logging.getLogger(__name__)

_ON_EXCEPTIONS = cli.handle_exceptions([
    (exc.InvalidInputError, None),
])


def _run(command):
    """Run command."""
    success = False
    try:
        output = subproc.check_output(
            command,
        )
        _LOGGER.info('Success.')
        success = True

    except subproc.CalledProcessError as err:
        output = str(err)
        _LOGGER.error('Failure.')
        cli.out(output)

    return success


def _run_tkt_sender(cells):
    """Actually run ticket sender"""
    dns_domain = context.GLOBAL.dns_domain

    first = True
    tktfwd_spn = None
    if os.name == 'nt':
        tktfwd_spn = _tktfwd_spn(dns_domain)
        _LOGGER.debug('Using tktfwd SPN: %s', tktfwd_spn)

    success = True
    for cellname in cells:

        endpoints_v2 = _check_cell(cellname, 'tickets-v2', dns_domain)
        if not endpoints_v2:
            _LOGGER.error('Ticket locker is down for cell: %s', cellname)
            success = False

        for idx, hostport in enumerate(endpoints_v2):
            host, port = hostport
            _LOGGER.info(
                'Forwarding tickets to cell: %s/%d - %s:%s',
                cellname,
                idx,
                host,
                port
            )
            host, port = hostport
            if os.name == 'nt' and first:
                first = False
                tkt_cmd = [
                    'tkt_send_v2',
                    '-h{}'.format(host),
                    '-p{}'.format(port),
                    '--purge',
                ]
            else:
                tkt_cmd = [
                    'tkt_send_v2',
                    '-h{}'.format(host),
                    '-p{}'.format(port),
                ]

            if tktfwd_spn:
                tkt_cmd.append('--service={}'.format(tktfwd_spn))

            success = _run(tkt_cmd) and success

    return success


def _get_cells():
    """Get all cell names"""
    restapi = context.GLOBAL.admin_api()
    cells = restclient.get(restapi, '/cell/').json()

    return [cell['_id'] for cell in cells]


def _check_cell(cellname, appname, dns_domain):
    """Return active endpoint for the locker given cell name."""
    srvrec = '_tickets._tcp.{}.{}.cell.{}'.format(appname,
                                                  cellname,
                                                  dns_domain)
    result = dnsutils.srv(srvrec, context.GLOBAL.dns_server)

    active = []
    for host, port, _, _ in result:
        sock = None
        try:
            sock = socket.create_connection((host, port), 1)
            active.append((host, port))
        except socket.error:
            _LOGGER.warning('Ticket endpoint [%s] is down: %s:%s',
                            cellname, host, port)
        finally:
            if sock:
                sock.close()

    active.sort()
    return active


def _tktfwd_spn(dns_domain):
    """Return tktfwd SPN for given dns domain."""
    tktfwd_rec = dnsutils.txt(
        'tktfwd.%s' % (dns_domain),
        context.GLOBAL.dns_server
    )

    if tktfwd_rec:
        return tktfwd_rec[0]
    else:
        return None


def init():
    """Return top level command handler"""

    @click.command()
    @click.option('--cell', help='List of cells',
                  type=cli.LIST)
    @_ON_EXCEPTIONS
    def forward(cell):
        """Forward Kerberos tickets to the cell ticket locker."""
        _LOGGER.setLevel(logging.INFO)
        cells = cell
        if not cell:
            cells = _get_cells()

        rc = _run_tkt_sender(cells)
        # TODO: it seems like returning from click callback with non-0 does not
        #       set the $? correctly.
        sys.exit(0 if rc else 1)

    return forward
