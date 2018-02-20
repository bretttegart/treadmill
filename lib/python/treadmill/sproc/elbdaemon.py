"""Treadmill AWS ELB manager.

This system process watches Zookeeper's data on app endpoints
and creates/updates/destroys AWS Load Balancers when app endpoints change
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

import click
from twisted.internet import reactor

from treadmill import context
from treadmill.infra import connection
from treadmill import utils
from treadmill import zknamespace as z
from treadmill import zkutils
from treadmill.aws.elb import elbdaemon

_LOGGER = logging.getLogger(__name__)


def _do_watch(zkclient, endpointpath):
    """Watch proid endpoints for changes"""
    elb_daemon = elbdaemon.EndpointWatcher(endpointpath)

    @zkclient.ChildrenWatch(endpointpath)
    @utils.exit_on_unhandled
    def _endpoint_change(_children):
        _LOGGER.info(
            'Endpoints changed! Updating ELB configuration...'
        )
    elb_daemon.run()


def init():
    """Return top level command handler."""

    @click.command()
    @click.option('--no-lock', is_flag=True, default=False,
                  help='Run without lock.')
    @click.option('--proid', required=True,
                  help='System proid.')
    @click.option('--region', help='Region for the vpc')
    def run(no_lock, proid, region):
        """Run Treadmill DNS endpoint engine."""
        zkclient = context.GLOBAL.zk.conn
        endpointpath = z.join_zookeeper_path(z.ENDPOINTS, proid)
        zkclient.ensure_path(endpointpath)

        if region:
            connection.Connection.context.region_name = region        

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


