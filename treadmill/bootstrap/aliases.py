"""Default aliases."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os


_LINUX_ALIASES = {
    'awk': '/usr/bin/awk',
    'backtick': None,
    'basename': '/bin/basename',
    'blkid': '/sbin/blkid',
    'brctl': '/usr/sbin/brctl',
    'cat': '/bin/cat',
    'cd': None,
    'chmod': '/bin/chmod',
    'chown': '/bin/chown',
    'chroot': '/usr/sbin/chroot',
    'conntrack': '/usr/sbin/conntrack',
    'cp': '/bin/cp',
    'date': '/bin/date',
    'dirname': '/usr/bin/dirname',
    'dmesg': '/bin/dmesg',
    'dnscache': None,
    'dumpe2fs': '/sbin/dumpe2fs',
    'echo': '/bin/echo',
    'elglob': None,
    'emptyenv': None,
    'execlineb': None,
    'fdmove': None,
    'find': '/usr/bin/find',
    'fio': None,
    'grep': '/bin/grep',
    'gzip': '/usr/bin/gzip',
    'hostname': '/bin/hostname',
    'haproxy': None,
    'if': None,
    'ifconfig': '/sbin/ifconfig',
    'import': None,
    'importas': None,
    'ionice': '/usr/bin/ionice',
    'ip': '/sbin/ip',
    'ipset': '/usr/sbin/ipset',
    'iptables': '/sbin/iptables',
    'iptables_restore': '/sbin/iptables-restore',
    'java_home': None,
    'kafka_run_class': None,
    'kafka_server_start': None,
    'kill': '/usr/bin/kill',
    'kinit': None,
    'klist': None,
    'kt-add': None,
    'kt-split': None,
    'last': '/usr/bin/last',
    'ln': '/bin/ln',
    'logrotate': '/usr/sbin/logrotate',
    'logstash-forwarder': None,
    'losetup': '/sbin/losetup',
    'ls': '/bin/ls',
    'lssubsys': '/bin/lssubsys',
    'lvm': '/sbin/lvm',
    'mkdir': '/bin/mkdir',
    'mke2fs': '/sbin/mke2fs',
    'mkfifo': '/usr/bin/mkfifo',
    'mknod': '/bin/mknod',
    'modulecmd': None,
    'mount': '/bin/mount',
    'mv': '/bin/mv',
    'named': '/usr/sbin/named',
    'openldap': None,
    'pid1': None,
    'printf': '/usr/bin/printf',
    'pvremove': '/sbin/pvremove',
    'pwd': '/bin/pwd',
    'readlink': '/bin/readlink',
    'redirfd': None,
    'rm': '/bin/rm',
    'route': '/sbin/route',
    'rrdcached': '/bin/rrdcached',
    'rrdtool': '/bin/rrdtool',
    's6': None,
    's6_envdir': None,
    's6_envuidgid': None,
    's6_log': None,
    's6_setuidgid': None,
    's6_svc': None,
    's6_svok': None,
    's6_svscan': None,
    's6_svscanctl': None,
    's6_svwait': None,
    'slapadd': None,
    'slapd': None,
    'sleep': '/bin/sleep',
    'sshd': '/usr/sbin/sshd',
    'sysctl': '/sbin/sysctl',
    'tail': '/usr/bin/tail',
    'tar': '/bin/tar',
    'tkt-recv': None,
    'tkt-send': None,
    'touch': '/bin/touch',
    'treadmill_bind_preload.so': None,
    'treadmill_spawn': None,
    'treadmill_spawn_finish': None,
    'treadmill_spawn_run': None,
    'tune2fs': '/sbin/tune2fs',
    'umask': None,
    'umount': '/bin/umount',
    'unshare': '/usr/bin/unshare',
    'vgchange': '/sbin/vgchange',
    'vgremove': '/sbin/vgremove',
    'ipa': '/bin/ipa'
}

_WINDOWS_ALIASES = {
    'winss': None,
    'winss_log': None,
    'winss_svc': None,
    'winss_svok': None,
    'winss_svscan': None,
    'winss_svscanctl': None,
    'winss_svwait': None,
    'powershell': 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\'
                  'powershell.exe',
}

if os.name == 'nt':
    ALIASES = _WINDOWS_ALIASES
else:
    ALIASES = _LINUX_ALIASES
