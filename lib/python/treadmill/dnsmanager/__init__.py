
"""High level dns API.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from ipalib import api as ipaapi
import pprint

_LOGGER = logging.getLogger(__name__)

_MANAGER = None


def get_manager(zkclient, zkpath):
    """Get dns manager"""
    global _MANAGER  # pylint: disable=W0603

    if not _MANAGER:
        # Initialize and connect IPA API client
        ipaapi.bootstrap_with_global_options()
        ipaapi.finalize()
        ipaapi.Backend.rpcclient.connect()
        _MANAGER = ipaapi

    return _MANAGER

def scan():
    return {}

def get_dns():
    dummy_dns = {}
    return dummy_dns

def set_dns():
    return {}

