"""Perform local port scan of container endpoints and publish results."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

import click

from treadmill import appenv
from treadmill import context
from treadmill import endpoints


_LOGGER = logging.getLogger(__name__)

_SCAN_INTERVAL = 30


def init():
    """Top level command handler."""

    @click.command()
    @click.option('--approot', type=click.Path(exists=True),
                  envvar='TREADMILL_APPROOT', required=True)
    @click.option('--scan-interval', type=int, required=True,
                  default=_SCAN_INTERVAL)
    @click.option('--instance', help='Publisher instance.')
    def run(approot, scan_interval, instance):
        """Starts portscan process."""
        _LOGGER.info('Staring portscan: scan interval: %d',
                     scan_interval)

        tm_env = appenv.AppEnvironment(approot)
        scanner = endpoints.PortScanner(tm_env.endpoints_dir,
                                        context.GLOBAL.zk.conn,
                                        scan_interval=scan_interval,
                                        instance=instance)
        scanner.run()

    return run
