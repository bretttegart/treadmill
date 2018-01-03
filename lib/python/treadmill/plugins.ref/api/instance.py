"""Instance plugin.

Adds proid and environment attributes based on request context.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def add_attributes(rsrc_id, manifest):
    """Add additional attributes to the manifest."""
    proid = rsrc_id[0:rsrc_id.find('.')]
    environment = 'prod'
    updated = {
        'proid': proid,
        'environment': environment
    }
    updated.update(manifest)
    return updated


def remove_attributes(manifest):
    """Removes extra attributes from the manifest."""
    if 'proid' in manifest:
        del manifest['proid']
    if 'environment' in manifest:
        del manifest['environment']

    return manifest
