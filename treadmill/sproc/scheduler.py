"""Treadmill master scheduler."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import click

from treadmill import context
from treadmill import master
from treadmill import scheduler


def init():
    """Return top level command handler."""

    @click.command()
    @click.argument('events-dir', type=click.Path(exists=True))
    def run(events_dir):
        """Run Treadmill master scheduler."""
        scheduler.DIMENSION_COUNT = 3
        cell_master = master.Master(context.GLOBAL.zk.conn,
                                    context.GLOBAL.cell,
                                    events_dir)
        cell_master.run()

    return run
