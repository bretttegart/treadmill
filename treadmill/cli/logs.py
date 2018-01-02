"""Trace treadmill application events.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import urllib.request
import urllib.parse
import urllib.error

import click

from treadmill import cli
from treadmill import context
from treadmill import websocketutils as wsu
from treadmill import restclient
from treadmill.websocket import client as wsclient

_LOGGER = logging.getLogger(__name__)


def _find_endpoints(pattern, proto, endpoint, api=None):
    """Return all the matching endpoints in the cell.

    The return value is a dict with host-endpoint assigments as key-value
    pairs.
    """
    apis = context.GLOBAL.state_api(api)

    url = '/endpoint/{}/{}/{}'.format(pattern, proto, endpoint)

    endpoints = restclient.get(apis, url).json()
    if not endpoints:
        cli.bad_exit("Nodeinfo API couldn't be found")

    return endpoints


def init():
    """Return top level command handler."""

    @click.command()
    @click.option('--api',
                  envvar='TREADMILL_STATEAPI',
                  help='State API url to use.',
                  metavar='URL',
                  required=False)
    @click.argument('app-or-svc')
    @click.option('--cell',
                  callback=cli.handle_context_opt,
                  envvar='TREADMILL_CELL',
                  expose_value=False,
                  required=True)
    @click.option('--host',
                  help='Hostname where to look for the logs',
                  required=False)
    @click.option('--service',
                  help='The name of the service for which the logs are '
                       'to be retreived',
                  required=False)
    @click.option('--uniq',
                  default='running',
                  help="The container id. Specify this if you look for a "
                       "not-running (terminated) application's log",
                  required=False)
    @click.option('--ws-api',
                  help='Websocket API url to use.',
                  metavar='URL',
                  required=False)
    @cli.handle_exceptions(
        restclient.CLI_REST_EXCEPTIONS + wsclient.CLI_WS_EXCEPTIONS)
    def logs(api, app_or_svc, host, service, uniq, ws_api):
        """View application's service logs.

        Arguments are expected to be specified a) either as one string or b)
        parts defined one-by-one ie.:

        a) <appname>/<uniq or running>/service/<servicename>

        b) <appname> --uniq <uniq> --service <servicename>

        Eg.:

        a) proid.foo#1234/xz9474as8/service/my-echo

        b) proid.foo#1234 --uniq xz9474as8 --service my-echo

        For the latest log simply omit 'uniq':

        proid.foo#1234 --service my-echo
        """
        try:
            app, uniq, logtype, logname = app_or_svc.split('/', 3)
        except ValueError:
            app, uniq, logtype, logname = app_or_svc, uniq, 'service', service

        if logname is None:
            cli.bad_exit("Please specify the 'service' parameter.")

        if host is None:
            instance = None
            if uniq == 'running':
                instance = wsu.find_running_instance(app, ws_api)

            if not instance:
                instance = wsu.find_uniq_instance(app, uniq, ws_api)

            if not instance:
                cli.bad_exit('No {}instance could be found.'.format(
                    'running ' if uniq == 'running' else ''))

            _LOGGER.debug('Found instance: %s', instance)

            host = instance['host']
            uniq = instance['uniq']

        try:
            endpoint, = (
                ep
                for ep in _find_endpoints(
                    urllib.parse.quote('root.*'), 'tcp', 'nodeinfo', api
                )
                if ep['host'] == host
            )
        except ValueError as err:
            _LOGGER.exception(err)
            cli.bad_exit('No endpoint found on %s', host)

        api = 'http://{0}:{1}'.format(endpoint['host'], endpoint['port'])
        logurl = '/local-app/%s/%s/%s/%s' % (
            urllib.quote(app),
            urllib.quote(uniq),
            logtype,
            urllib.quote(logname)
        )

        log = restclient.get(api, logurl)
        click.echo(log.text)

    return logs
