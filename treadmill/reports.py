"""Handles reports over scheduler data."""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import time
import datetime
import itertools
import logging
import fnmatch

import numpy as np
import pandas as pd

import six

_LOGGER = logging.getLogger(__name__)


def servers(cell):
    """Prepare DataFrame with server information."""

    # Hard-code order of columns
    columns = [
        'name', 'location', 'partition', 'traits',
        'state', 'valid_until',
        'mem', 'cpu', 'disk',
        'mem_free', 'cpu_free', 'disk_free'
    ]

    def _server_location(node):
        """Recursively yield the node's parents."""
        while node:
            yield node.name
            node = node.parent

    def _server_row(server):
        """Transform server into a DataFrame-ready dict."""
        partition = list(server.labels)[0]
        row = {
            'name': server.name,
            'location': '/'.join(reversed(list(
                _server_location(server.parent)
            ))),
            'partition': partition if partition else '-',
            'traits': server.traits.traits,
            'state': server.state.value,
            'valid_until': server.valid_until,
            'mem': server.init_capacity[0],
            'cpu': server.init_capacity[1],
            'disk': server.init_capacity[2],
            'mem_free': server.free_capacity[0],
            'cpu_free': server.free_capacity[1],
            'disk_free': server.free_capacity[2]
        }

        return row

    frame = pd.DataFrame.from_dict([
        _server_row(server)
        for server in cell.members().values()
    ]).astype({
        'mem': 'int',
        'cpu': 'int',
        'disk': 'int',
        'mem_free': 'int',
        'cpu_free': 'int',
        'disk_free': 'int'
    })

    if frame.empty:
        frame = pd.DataFrame(columns=columns)

    return frame[columns].set_index('name').sort_index()


def iterate_allocations(path, alloc):
    """Generate (path, alloc) tuples for the leaves of the allocation tree."""
    if not alloc.sub_allocations:
        return iter([('/'.join(path), alloc)])
    else:
        def _chain(acc, item):
            """Chains allocation iterators."""
            name, suballoc = item
            return itertools.chain(
                acc,
                iterate_allocations(path + [name], suballoc)
            )

        return six.moves.reduce(
            _chain, six.iteritems(alloc.sub_allocations), []
        )


def allocations(cell):
    """Prepare DataFrame with allocation information."""

    # Hard-code order of columns
    columns = [
        'partition', 'name', 'mem', 'cpu', 'disk',
        'rank', 'rank_adj', 'traits', 'max_util'
    ]

    def _alloc_row(partition, name, alloc):
        """Transform allocation into a DataFrame-ready dict."""
        if not name:
            name = 'root'
        if not partition:
            partition = '-'

        return {
            'partition': partition,
            'name': name,
            'mem': alloc.reserved[0],
            'cpu': alloc.reserved[1],
            'disk': alloc.reserved[2],
            'rank': alloc.rank,
            'rank_adj': alloc.rank_adjustment,
            'traits': alloc.traits,
            'max_util': alloc.max_utilization,
        }

    frame = pd.DataFrame.from_dict([
        _alloc_row(label, name, alloc)
        for label, partition in six.iteritems(cell.partitions)
        for name, alloc in iterate_allocations([], partition.allocation)
    ])
    if frame.empty:
        frame = pd.DataFrame(columns=columns)

    return frame[columns].astype({
        'mem': 'int',
        'cpu': 'int',
        'disk': 'int'
    }).set_index(['partition', 'name']).sort_index()


def apps(cell):
    """Prepare DataFrame with app and queue information."""

    # Hard-code order of columns
    columns = [
        'instance', 'allocation', 'rank', 'affinity', 'partition',
        'identity_group', 'identity',
        'order', 'lease', 'expires', 'data_retention',
        'pending', 'server', 'util',
        'mem', 'cpu', 'disk'
    ]

    def _app_row(item):
        """Transform app into a DataFrame-ready dict."""
        rank, util, pending, order, app = item
        return {
            'instance': app.name,
            'affinity': app.affinity.name,
            'allocation': app.allocation.name,
            'rank': rank,
            'partition': app.allocation.label or '-',
            'util': util,
            'pending': pending,
            'order': order,
            'identity_group': app.identity_group,
            'identity': app.identity,
            'mem': app.demand[0],
            'cpu': app.demand[1],
            'disk': app.demand[2],
            'lease': app.lease,
            'expires': app.placement_expiry,
            'data_retention': app.data_retention_timeout,
            'server': app.server
        }

    queue = []
    for partition in cell.partitions.values():
        allocation = partition.allocation
        queue += allocation.utilization_queue(cell.size(allocation.label))

    frame = pd.DataFrame.from_dict([_app_row(item) for item in queue]).fillna({
        'expires': -1,
        'identity': -1,
        'data_retention': -1
    })
    if frame.empty:
        frame = pd.DataFrame(columns=columns)

    return frame[columns].astype({
        'mem': 'int',
        'cpu': 'int',
        'disk': 'int',
        'order': 'int',
        'expires': 'int',
        'data_retention': 'int',
        'identity': 'int'
    }).set_index('instance').sort_index()


def utilization(prev_utilization, apps_df):
    """Returns dataseries describing cell utilization.

    prev_utilization - utilization dataframe before current.
    apps - app queue dataframe.
    """
    # Passed by ref.
    row = apps_df.reset_index()
    if row.empty:
        return row

    row['count'] = 1
    row['name'] = row['instance'].apply(lambda x: x.split('#')[0])
    row = row.groupby('name').agg({'cpu': np.sum,
                                   'mem': np.sum,
                                   'disk': np.sum,
                                   'count': np.sum,
                                   'util': np.max})
    row = row.stack()
    dt_now = datetime.datetime.fromtimestamp(time.time())
    current = pd.DataFrame([row], index=pd.DatetimeIndex([dt_now]))

    if prev_utilization is None:
        return current
    else:
        return prev_utilization.append(current)


def reboots(cell):
    """Prepare dataframe with server reboot info."""

    # Hard-code order of columns
    columns = [
        'server', 'valid-until', 'days-left',
    ]

    def _reboot_row(server, now):
        valid_until = datetime.datetime.fromtimestamp(server.valid_until)
        return {
            'server': server.name,
            'valid-until': valid_until,
            'days-left': (valid_until - now).days,
        }

    now = datetime.datetime.now()

    frame = pd.DataFrame.from_dict([
        _reboot_row(server, now)
        for server in cell.members().values()
    ])

    return frame[columns].set_index('server').sort_index()


class ExplainVisitor(object):
    """Scheduler visitor"""

    def __init__(self):
        """Initialize result"""
        self.result = []

    def add(self, alloc, entry):
        """Add new row to result"""
        rank, util, _pending, _order, app = entry

        alloc_name = '/'.join(alloc.path)
        server = app.server if app.server else '-'

        self.result.append({
            'alloc': alloc_name,
            'rank': rank,
            'util': util if alloc_name else '',
            'name': app.name,
            'server': server if not alloc_name else '',
        })

    def finish(self):
        """Post-process result array"""
        def _sort_order(entry):
            return (entry['alloc'], entry['util'])

        result = sorted(self.result, key=_sort_order)

        # annotate with position in alloc queue
        pos = 1
        alloc = ''
        for row in result:
            if row['alloc'] != alloc:
                alloc = row['alloc']
                pos = 1
            row['pos'] = pos
            pos = pos + 1

        self.result = result

    def filter(self, pattern):
        """Filter result to rows with matching app instances"""
        self.result = [row for row in self.result
                       if fnmatch.fnmatch(row['name'], pattern)]


def explain_queue(cell, partition, pattern=None):
    """Compute dataframe for explaining app queue"""
    alloc = cell.partitions[partition].allocation
    size = cell.size(partition)
    visitor = ExplainVisitor()
    queue = alloc.utilization_queue(size, visitor.add)

    # we run the generator to completion, and this builds up the
    # visitor as a side-effect
    for _ in queue:
        pass

    visitor.finish()

    if pattern:
        visitor.filter(pattern)

    # set columns explicitly to control order
    columns = ['pos', 'alloc', 'name', 'rank', 'util', 'server']
    return pd.DataFrame(visitor.result, columns=columns)


def _preorder_walk(node, _app=None):
    """Walk the tree in preorder"""
    return itertools.chain(
        [node],
        *[_preorder_walk(child) for child in node.children]
    )


def _servers_walk(cell, _app):
    """Return servers only"""
    return cell.members().values()


def _limited_walk(node, app):
    """Walk the tree like preorder, but only expand nodes when they are
feasible for placement"""
    if node.check_app_constraints(app):
        return itertools.chain(
            [node],
            *[_limited_walk(child, app) for child in node.children]
        )
    else:
        return [node]


WALKS = {
    'servers': _servers_walk,
    'full': _preorder_walk,
    'default': _limited_walk,
}


def explain_placement(cell, app, mode):
    """Explain placement for app"""
    result = []
    for node in WALKS[mode](cell, app):
        capacity = node.free_capacity > app.demand
        result.append({
            'name': node.name,
            'affinity': node.check_app_affinity_limit(app),
            'traits': node.traits.has(app.traits),
            'partition': app.allocation.label in node.labels,
            'feasible': node.check_app_constraints(app),
            'memory': capacity[0],
            'cpu': capacity[1],
            'disk': capacity[2],
        })

    # Hard-code order of columns
    columns = [
        'partition', 'traits', 'affinity',
        'memory', 'cpu', 'disk', 'name'
    ]
    df = pd.DataFrame(result, columns=columns)
    df.replace(True, '.', inplace=True)
    df.replace(False, 'x', inplace=True)
    return df
