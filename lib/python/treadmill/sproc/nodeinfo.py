"""Node info sproc module.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import socket

import click

from treadmill import appenv
from treadmill import cli
from treadmill import context
from treadmill import endpoints
from treadmill import rest
from treadmill import sysinfo
from treadmill import utils
from treadmill import zknamespace as z
from treadmill import zkutils
from treadmill.rest import api
from treadmill.rest import error_handlers  # pylint: disable=W0611


_LOGGER = logging.getLogger(__name__)

_SERVERS_ACL = zkutils.make_role_acl('servers', 'rwcda')


def init():
    """Top level command handler."""

    @click.command()
    @click.option('--approot', type=click.Path(exists=True),
                  envvar='TREADMILL_APPROOT', required=True)
    @click.option('-r', '--register', required=False, default=False,
                  is_flag=True, help='Register as /nodeinfo in Zookeeper.')
    @click.option('-p', '--port', required=False, default=0)
    @click.option('-a', '--auth', type=click.Choice(['spnego']))
    @click.option('-m', '--modules', help='API modules to load.',
                  required=False, type=cli.LIST)
    @click.option('-t', '--title', help='API Doc Title',
                  default='Treadmill Nodeinfo REST API')
    @click.option('-c', '--cors-origin', help='CORS origin REGEX')
    def server(approot, register, port, auth, modules, title, cors_origin):
        """Runs nodeinfo server."""
        if port == 0:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', 0))
            port = sock.getsockname()[1]
            sock.close()

        hostname = sysinfo.hostname()
        hostport = '%s:%s' % (hostname, port)

        if register:
            zkclient = context.GLOBAL.zk.conn
            zkclient.add_listener(zkutils.exit_on_lost)

            appname = 'root.%s#%010d' % (hostname, os.getpid())
            app_pattern = 'root.%s#*' % (hostname)
            path = z.path.endpoint(appname, 'tcp', 'nodeinfo')
            _LOGGER.info('register endpoint: %s %s', path, hostport)
            zkutils.create(zkclient, path, hostport,
                           acl=[_SERVERS_ACL],
                           ephemeral=True)

            # TODO: remove "legacy" endpoint registration once conversion is
            #       complete.
            tm_env = appenv.AppEnvironment(approot)
            # TODO: need to figure out how to handle windows.
            assert os.name != 'nt'
            endpoints_mgr = endpoints.EndpointsMgr(tm_env.endpoints_dir)
            endpoints_mgr.unlink_all(
                app_pattern, endpoint='nodeinfo', proto='tcp'
            )
            endpoints_mgr.create_spec(
                appname=appname,
                endpoint='nodeinfo',
                proto='tcp',
                real_port=port,
                pid=os.getpid(),
                port=port,
                owner='/proc/{}'.format(os.getpid()),
            )

        _LOGGER.info('Starting nodeinfo server on port: %s', port)

        utils.drop_privileges()

        api_paths = []
        if modules:
            api_paths = api.init(modules, title.replace('_', ' '), cors_origin)

        rest_server = rest.TcpRestServer(port, auth_type=auth,
                                         protect=api_paths)
        rest_server.run()

    return server
