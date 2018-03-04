"""Treadmill node bootstrap.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from .. import aliases

if os.name == 'nt':
    _DEFAULT_RUNTIME = 'docker'
else:
    _DEFAULT_RUNTIME = 'linux'

_DEFAULT_TREADMILL_VG = 'treadmill'
_DEFAULT_HOST_TICKET = '{{ dir }}/spool/tickets/krb5cc_host'

DEFAULTS = {
    'treadmill_runtime': _DEFAULT_RUNTIME,
    'treadmill_host_ticket': _DEFAULT_HOST_TICKET,
    'treadmill_core_cpu_shares': '1%',
    'treadmill_cpu_shares': '90%',
    'system_cpuset_cores': '0',
    'treadmill_core_cpuset_cpus': '-',
    'treadmill_apps_cpuset_cpus': '-',
    'treadmill_mem': '-2G',
    'treadmill_core_mem': '-',
    'localdisk_img_location': '/var/tmp/treadmill-node/',
    'localdisk_img_size': '-2G',
    'localdisk_block_dev': None,
    'localdisk_vg_name': _DEFAULT_TREADMILL_VG,
    'block_dev_configuration': None,
    'block_dev_read_bps': 50000000,
    'block_dev_write_bps': 12000000,
    'block_dev_read_iops': 2000,
    'block_dev_write_iops': 500,
    'localdisk_default_read_bps': '20M',
    'localdisk_default_write_bps': '20M',
    'localdisk_default_read_iops': 100,
    'localdisk_default_write_iops': 100,
    'runtime_linux_host_mounts': (
        '/,/dev*,/proc*,/sys*,/run*,/mnt*,'
    ),
    'docker_network': 'nat',
}

ALIASES = aliases.ALIASES
