"""Treadmill DNS manager.

This system process watches Zookeeper's data on app endpoints
and refreshes the cell DNS servers when app endpoints change
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

import click
from twisted.internet import reactor

from treadmill import context
from treadmill import dnsmanager
from treadmill import utils
from treadmill import zknamespace as z
from treadmill import zkutils

_LOGGER = logging.getLogger(__name__)


def _do_watch(zkclient, endpointpath):
    """Watch proid endpoints for changes"""
    dns_manager = dnsmanager.get_manager(zkclient, endpointpath)

    @zkclient.ChildrenWatch(endpointpath)
    @utils.exit_on_unhandled
    def _endpoint_change(_children):
        _LOGGER.info(
            'Endpoints changed! Refreshing DNS...'
        )
    dns_manager.scan()


def init():
    """Return top level command handler."""

    @click.command()
    @click.option('--no-lock', is_flag=True, default=False,
                  help='Run without lock.')
    @click.option('--proid', required=True,
                  help='System proid.')
    def run(no_lock, proid):
        """Run Treadmill DNS endpoint engine."""
        zkclient = context.GLOBAL.zk.conn
        endpointpath = z.join_zookeeper_path(z.ENDPOINTS, proid)
        zkclient.ensure_path(endpointpath)

        if no_lock:
            _do_watch(zkclient, endpointpath)
            reactor.run()
        else:
            lock = zkutils.make_lock(
                zkclient, z.path.election(__name__)
            )
            _LOGGER.info('Waiting for leader lock.')
            with lock:
                _do_watch(zkclient, endpointpath)
                reactor.run()

    return run

