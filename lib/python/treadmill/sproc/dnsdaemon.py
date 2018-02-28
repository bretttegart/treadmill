""" Treadmill IPA DNS manager.

    This system process watches Zookeeper's data on app endpoints
    and creates/updates/destroys IPA DNS records when app endpoints change
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

import click
import os
from twisted.internet import reactor

from treadmill import context
from treadmill import utils
from treadmill import zknamespace as z
from treadmill import zkutils
from treadmill.infra import connection
from treadmill.aws.dns import dnsdaemon

_LOGGER = logging.getLogger(__name__)


def _do_watch(zkclient, endpointpath):
    """Watch proid endpoints for changes"""
    dns_daemon = dnsdaemon.EndpointWatcher(endpointpath)

    @zkclient.ChildrenWatch(endpointpath)
    @utils.exit_on_unhandled
    def _endpoint_change(_children):
        _LOGGER.info(
            'Endpoints changed! Updating DNS configuration...'
        )
    dns_daemon.run()


def init():
    """Return top level command handler."""

    @click.command()
    @click.option('--no-lock', is_flag=True, default=False,
                  help='Run without lock.')
    @click.option('--proid', required=True,
                  help='System proid to monitor')
    @click.option('--region',  required=True,
                  help='VPC region',
                  envvar='AWS_DEFAULT_REGION',)
    @click.option('--root', default='/tmp/zk2fs',
                  help='ZK2FS root directory')
    def run(no_lock, proid, region, root):
        """Run Treadmill DNS endpoint engine."""
        zkclient = context.GLOBAL.zk.conn

        zkendpointpath = z.join_zookeeper_path(z.ENDPOINTS, proid)
        zkclient.ensure_path(zkendpointpath)
        zk2fs_endpointpath = '{}{}'.format(root, zkendpointpath)

        if not os.path.isabs(zk2fs_endpointpath):
            _LOGGER.error('Invalid path: {}'.format(zk2fs_endpointpath))
            exit(1)

        if region:
            connection.Connection.context.region_name = region

        if no_lock:
            _do_watch(zkclient, zk2fs_endpointpath)
            reactor.run()
        else:
            lock = zkutils.make_lock(
                zkclient, z.path.election(__name__)
            )
            _LOGGER.info('Waiting for leader lock.')
            with lock:
                _do_watch(zkclient, zk2fs_endpointpath)
                reactor.run()

    return run

