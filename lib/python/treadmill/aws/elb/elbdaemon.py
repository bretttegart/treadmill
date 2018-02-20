'''Run in background:
    elbManagerDaemon = EndpointWatcher(ZKFS_DIR)
    elbManagerDaemon.start()

or in the foreground:
    elbManagerDaemon.run()
'''
from treadmill.aws.elb.manager import ELBManager
from treadmill.dirwatch import DirWatcher
from types import SimpleNamespace
import os
import re
import logging
from threading import Event, Thread

ZKFS_DIR = '/tmp/zkfs-test'
_LOGGER = logging.getLogger(__name__)


class EndpointWatcherThread(Thread):
    def __init__(self, target, name="ELB Manager Watchdog"):
        self._stop_event = Event()
        Thread.__init__(self, target=target, name=name, daemon=True)

    def stop(self):
        self._stop_event.set()
        Thread.join(self, timeout=0)
        print("{} has stopped".format(self.name))

    def start(self):
        print("{} has started".format(self.name))
        Thread.start(self)


class EndpointWatcher(ELBManager):
    def __init__(self, zkfs_dir):
        ELBManager.__init__(self, zkfs_dir)
        self.on_created = self._on_created
        self.on_deleted = self._on_deleted
        self.thread = None
        
    def get_context(self, path):
        c = SimpleNamespace()
        c.proid, c.fileName = path.split('/')[-2:]
        try:
            c.app, c.cell, c.protocol = re.search('([a-z0-9-]+)\.([a-z0-9-]+)#\d*:\w+:(\w+)', c.fileName).groups()
        except:
            return None
        c.tg_name = "{}-{}-{}-{}".format(c.proid, c.app, c.cell, c.protocol)
        c.fileRegex = '{}.{}#\d+:.*:{}'.format(c.app, c.cell, c.protocol)
        c.proid_dir = '{}/{}'.format(self.endpoint_dir, c.proid)
        return c

    def getTargetFromFile(self, path):
        instanceId, port = open(path).read().split(':')
        return instanceId, int(port)

    def getEndPoints(self, path):
        context = self.get_context(path)
        files = ["{}/{}".format(context.proid_dir, fileName) for fileName in os.listdir(context.proid_dir)
                 if re.match(context.fileRegex, fileName)
                 ]
        return [self.getTargetFromFile(file) for file in files if os.path.exists(file)]

    def _on_created(self, path):
        context = self.get_context(path)
        print("Found new endpoint {}/{}".format(context.proid_dir, context.fileName))
        targets = [self.getTargetFromFile(path)]
        self.register(context.proid, context.tg_name, targets)
        tg = self.findTargetGroup(name=context.tg_name)
        if tg:
            self.add_targets(tg, targets)
            self.update_app_groups(path, tg)
        print("Processed adding of endpoint {}".format(targets))

    def _on_deleted(self, path):
        context = self.get_context(path)
        if not context:
            return
        print("Deleted endpoint {}/{}".format(context.proid_dir, context.fileName))
        leftTargets = self.getEndPoints(path)
        tg = self.findTargetGroup(name=context.tg_name)
        if not tg:
            return
        targets = self.remove_targets(tg, leftTargets)
        print("Processed removing of endpoint {}".format(targets))
        if not leftTargets:
            self.deregister(context.tg_name)
        self.update_app_groups(path, tg)


    def update_app_groups(self, path, target_group):
        context = self.get_context(path)
        elb = self.findLoadBalancer(name=context.proid)
        elb_dns = elb.dnsName if elb else '<load_balancer_not_found>'
        with open('{}/{}.{}.{}'.format(self.app_groups_dir, context.proid, context.app, context.cell), 'w') as app_group:
            app_group.write('''cells: [{c.cell}]
            \rdata: ['virtuals={dns}.{t.port}',
            \r  environment=dev, 'vips={dns}',
            \r  port={t.port}]
            \rendpoints: [{c.protocol}]
            \rgroup-type: lbendpoint
            \rpattern: {c.proid}.{c.app}'''.format(c=context, t=target_group, dns=elb_dns))

    def run(self):
        """Use "start" to run it as a background daemon or "run" to run it in the foreground"""
        watch = DirWatcher()
        watch.on_created = self._on_created
        watch.on_deleted = self._on_deleted
        # watch.on_modified = self._on_modified
        while True:
            watch._watches = {}
            [watch.add_dir("/".join((self.endpoint_dir, app))) for app in os.listdir(self.endpoint_dir)]
            if watch.wait_for_events(5):
                watch.process_events()

    def start(self):
        """Use "start" to run it as a background daemon or "run" to run it in the foreground"""
        self.thread = EndpointWatcherThread(target=self.run)
        self.thread.start()

    def stop(self):
        """Use "stop" to kill the background daemon"""
        if self.thread:
            self.thread.stop()
        self.thread = None


    
