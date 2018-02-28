import logging
import os
import re
from types import SimpleNamespace
from treadmill.aws.dns.manager import DNSManager
from treadmill.dirwatch import DirWatcher

_LOGGER = logging.getLogger(__name__)


class EndpointWatcher(DNSManager):
    def __init__(self, zkfs_dir):
        _LOGGER.info('Montoring directory: {}'.format(zkfs_dir))
        DNSManager.__init__(self)
        self.endpoint_dir = zkfs_dir
        self.on_created = self._on_created
        self.on_deleted = self._on_deleted

    def get_filesystem_context(self, path):
        c = SimpleNamespace()
        c.proid, c.fileName = path.split('/')[-2:]
        try:
            c.app, c.server, c.protocol = re.search(
                '([a-z0-9-]+)#\d*:(\w+):(\w+)',
                c.fileName
                ).groups()
            c.cell = os.environ.get('TREADMILL_CELL')
        except Exception as e:
            _LOGGER.error(str(e))
            return None
        c.proid_dir = '{}/{}'.format(self.endpoint_dir, c.proid)
        return c

    def getTargetFromFile(self, path):
        hostname, port = open(path).read().split(':')
        return hostname, int(port)

    def getEndPoints(self, path):
        context = self.get_filesystem_context(path)
        files = ["{}/{}".format(context.proid_dir, fileName)
                 for fileName in os.listdir(context.proid_dir)
                 if re.match(context.fileRegex, fileName)
                 ]
        return [self.getTargetFromFile(file)
                for file in files
                if os.path.exists(file)
                ]

    def _on_created(self, path):
        context = self.get_filesystem_context(path)
        _LOGGER.info("Found new endpoint {}/{}".format(
            context.proid_dir, context.fileName))

        # Get list of endpoints from new ZK entry
        endpoints = [self.getTargetFromFile(path)]

        # Create DNS entries for new endpoints
        self.registerDNS(context.proid,
                         context.server,
                         context.app,
                         context.protocol,
                         endpoints)

        _LOGGER.info("Record added: {}".format(path))

    def _on_modified(self, path):
        _LOGGER.debug("Record modified: {}".format(path))
        self.sync()

    def _on_deleted(self, path):
        _LOGGER.debug("Record deleted: {}".format(path))
        self.sync()

    def run(self):
        watch = DirWatcher()
        # on_modified triggers for both new and modified files
        #watch.on_created = self._on_created
        watch.on_modified = self._on_modified
        watch.on_deleted = self._on_deleted
        watch.add_dir(self.endpoint_dir)

        # Run an initial sync when daemon starts
        self.sync()

        # Main loop
        while True:
            watch._watches = {}

            if watch.wait_for_events(5):
                watch.process_events()

    def sync(self):
        ''' Sync current ZK state to IPA DNS'''
        app_full_paths = ['{}/{}'.format(self.endpoint_dir, app)
                          for app in os.listdir(self.endpoint_dir)
                          ]

        zk_context = []
        for path in app_full_paths:
            c = self.get_filesystem_context(path)
            e = [self.getTargetFromFile(path)]
            if c and e:
                zk_context.append({'context': c,
                                   'endpoints': e})

        self.syncDNS(zk_context)

