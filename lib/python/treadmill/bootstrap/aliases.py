"""Default aliases."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os


_LINUX_ALIASES = {
    'awk': '/usr/bin/awk',
    'backtick': '/opt/s6/bin/backtick',
    'basename': '/bin/basename',
    'bc': '/usr/bin/bc',
    'blkid': '/sbin/blkid',
    'brctl': '/usr/sbin/brctl',
    'cat': '/bin/cat',
    'cd': '/opt/s6/bin/cd',
    'chmod': '/bin/chmod',
    'chown': '/bin/chown',
    'chroot': '/usr/sbin/chroot',
    'conntrack': '/usr/sbin/conntrack',
    'cp': '/bin/cp',
    'cut': '/usr/bin/cut',
    'date': '/bin/date',
    'define': '/opt/s6/bin/define',
    'dirname': '/usr/bin/dirname',
    'dmesg': '/bin/dmesg',
    'dnscache': None,
    'docker': '/usr/bin/docker',
    'dockerd': '/usr/bin/dockerd',
    'docker_runtime': '/usr/libexec/docker/docker-runc-current',
    'dumpe2fs': '/sbin/dumpe2fs',
    'echo': '/bin/echo',
    'elglob': '/opt/s6/bin/elglob',
    'emptyenv': '/opt/s6/bin/emptyenv',
    'execlineb': '/opt/s6/bin/execlineb',
    'exit': '/opt/s6/bin/exit',
    'expr': '/usr/bin/expr',
    'fdmove': '/opt/s6/bin/fdmove',
    'find': '/usr/bin/find',
    'fio': None,
    'foreground': '/opt/s6/bin/foreground',
    'grep': '/bin/grep',
    'gzip': '/usr/bin/gzip',
    'haproxy': None,
    'head': '/usr/bin/head',
    'heredoc': '/opt/s6/bin/heredoc',
    'hostname': '/bin/hostname',
    'if': '/opt/s6/bin/if',
    'ifconfig': '/sbin/ifconfig',
    'ifelse': '/opt/s6/bin/ifelse',
    'import': '/opt/s6/bin/import',
    'importas': '/opt/s6/bin/importas',
    'ionice': '/usr/bin/ionice',
    'ip': '/sbin/ip',
    'ipa': '/bin/ipa',
    'ipset': '/usr/sbin/ipset',
    'iptables': '/sbin/iptables',
    'iptables_restore': '/sbin/iptables-restore',
    'java_home': None,
    'kafka_run_class': None,
    'kafka_server_start': None,
    'kill': '/usr/bin/kill',
    'kinit': '/usr/bin/kinit',
    'klist': '/usr/bin/klist',
    'kt_add': '/usr/bin/kt_add',
    'kt_split': '/usr/bin/kt_split',
    'last': '/usr/bin/last',
    'ln': '/bin/ln',
    'logrotate': '/usr/sbin/logrotate',
    'logstash-forwarder': None,
    'loopwhilex': None,
    'losetup': '/sbin/losetup',
    'ls': '/bin/ls',
    'lssubsys': '/bin/lssubsys',
    'lvm': '/sbin/lvm',
    'mkdir': '/bin/mkdir',
    'mke2fs': '/sbin/mke2fs',
    'mkfifo': '/usr/bin/mkfifo',
    'mknod': '/bin/mknod',
    'mktemp': '/bin/mktemp',
    'modulecmd': None,
    'mount': '/bin/mount',
    'mv': '/bin/mv',
    'named': '/usr/sbin/named',
    'openldap': None,
    'pid1': '/opt/treadmill-pid1/bin/pid1',
    'pipeline': '/opt/s6/bin/pipeline',
    'printf': '/usr/bin/printf',
    'ps': '/bin/ps',
    'pvremove': '/sbin/pvremove',
    'pvs': '/sbin/pvs',
    'pwd': '/bin/pwd',
    'readlink': '/bin/readlink',
    'redirfd': '/opt/s6/bin/redirfd',
    'rm': '/bin/rm',
    'route': '/sbin/route',
    'rrdcached': '/bin/rrdcached',
    'rrdtool': '/bin/rrdtool',
    's6': '/opt/s6',
    's6_envdir': '/opt/s6/bin/s6-envdir',
    's6_envuidgid':  '/opt/s6/bin/s6-envuidgid',
    's6_fghack':  '/opt/s6/bin/s6-fghack',
    's6_log':  '/opt/s6/bin/s6-log',
    's6_ipcclient': '/opt/s6/bin/s6-ipcclient',
    's6_ipcserver': '/opt/s6/bin/s6-ipcserver',
    's6_ipcserver_access': '/opt/s6/bin/s6-ipcserver-access',
    's6_setuidgid':  '/opt/s6/bin/s6-setuidgid',
    's6_svc':  '/opt/s6/bin/s6-svc',
    's6_svok':  '/opt/s6/bin/s6-svok',
    's6_svscan':  '/opt/s6/bin/s6-svscan',
    's6_svscanctl':  '/opt/s6/bin/s6-svscanctl',
    's6_svwait':  '/opt/s6/bin/s6-svwait',
    'sed': '/bin/sed',
    'slapadd': '/usr/sbin/slapadd',
    'slapd': '/usr/sbin/slapd',
    'sleep': '/bin/sleep',
    'sshd': '/usr/sbin/sshd',
    'stat': '/usr/bin/stat',
    'sysctl': '/sbin/sysctl',
    'tail': '/usr/bin/tail',
    'tar': '/bin/tar',
    'tkt_recv': None,
    'tkt_send': None,
    'touch': '/bin/touch',
    'treadmill_bin': '/opt/treadmill/bin/treadmill',
    'treadmill_bind_preload.so': '/etc/treadmill_bind_preload.so',
    'treadmill_spawn': None,
    'treadmill_spawn_finish': None,
    'treadmill_spawn_run': None,
    'tune2fs': '/sbin/tune2fs',
    'umask': '/opt/s6/bin/umask',
    'umount': '/bin/umount',
    'unshare': '/usr/bin/unshare',
    'vgchange': '/sbin/vgchange',
    'vgremove': '/sbin/vgremove',
    'wc': '/bin/wc',
    'watchdog': '/sbin/watchdog',
    'withstdinas': '/opt/s6/bin/withstdinas',
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
