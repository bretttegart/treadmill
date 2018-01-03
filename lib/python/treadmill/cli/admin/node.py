"""Implementation of treadmill admin node CLI plugin
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import shutil
import click

from treadmill import diskbenchmark
from treadmill import localdiskutils
from treadmill import subproc

from treadmill.fs import linux as fs_linux

_LOGGER = logging.getLogger(__name__)

_ALIAS_ERROR_MESSAGE = 'Required commands not found, ' \
                       'set proper command aliases with --aliases-path ' \
                       'or TREADMILL_ALIASES_PATH env var'


def lvm_group(parent):
    """Set up LVM on node"""

    ctx = {}

    @parent.group()
    @click.option('--vg-name', required=False,
                  default=localdiskutils.TREADMILL_VG,
                  help='Set up LVM on this volume group')
    def lvm(vg_name):
        """Set up LVM on node"""
        ctx['vg_name'] = vg_name

    @lvm.command()
    @click.option('--device-name', required=True,
                  type=click.Path(exists=True),
                  help='Set up LVM this device')
    def device(device_name):
        """Set up LVM on device"""
        try:
            localdiskutils.setup_device_lvm(device_name, ctx['vg_name'])
        except subproc.CommandAliasError:
            _LOGGER.error(_ALIAS_ERROR_MESSAGE)

    @lvm.command()
    @click.option('--image-path', required=True,
                  type=click.Path(exists=True, writable=True),
                  help='Set up LVM on an image file under this path')
    @click.option('--image-size', required=True,
                  help='Image file size')
    @click.option('--image-name', required=False,
                  default=localdiskutils.TREADMILL_IMG,
                  help='Image file name')
    def image(image_path, image_size, image_name):
        """Set up LVM on image file"""
        try:
            localdiskutils.setup_image_lvm(
                image_name,
                image_path,
                image_size,
                ctx['vg_name']
            )
        except subproc.CommandAliasError:
            _LOGGER.error(_ALIAS_ERROR_MESSAGE)

    del device
    del image


def benchmark_group(parent):
    """Benchmark node IO performance"""

    @parent.command()
    @click.option('--benchmark-publish-file', required=True,
                  type=click.Path(),
                  help='File for benchmark process to publish result')
    @click.option('--vg-name', required=False,
                  default=localdiskutils.TREADMILL_VG,
                  help='Benchmark this volume group')
    @click.option('--underlying-device-name', required=False,
                  type=click.Path(exists=True),
                  help='Underlying device name of the vg')
    @click.option('--underlying-image-path', required=False,
                  type=click.Path(exists=True),
                  help='Underlying image path of the vg')
    @click.option('--benchmark-volume', required=False,
                  default=diskbenchmark.BENCHMARK_VOLUME,
                  help='Benchmark file size, fio size')
    @click.option('--rw-type', required=False,
                  default=diskbenchmark.BENCHMARK_RW_TYPE,
                  help='Benchmark r/w type, fio rw')
    @click.option('--job-number', required=False,
                  default=diskbenchmark.BENCHMARK_JOB_NUMBER,
                  help='Benchmark process number, fio numjobs')
    @click.option('--thread-number', required=False,
                  default=diskbenchmark.BENCHMARK_THREAD_NUMBER,
                  help='Benchmark thread number each process, fio iodepth')
    @click.option('--iops-block-size', required=False,
                  default=diskbenchmark.BENCHMARK_IOPS_BLOCK_SIZE,
                  help='small block size to find max iops, fio bs')
    @click.option('--bps-block-size', required=False,
                  default=diskbenchmark.BENCHMARK_BPS_BLOCK_SIZE,
                  help='large block size to find max bps, fio bs')
    @click.option('--max-seconds', required=False,
                  default=diskbenchmark.BENCHMARK_MAX_SECONDS,
                  help='Benchmark max run time in seconds, fio runtime')
    def benchmark(benchmark_publish_file, vg_name, underlying_device_name,
                  underlying_image_path, benchmark_volume, rw_type,
                  job_number, thread_number, iops_block_size, bps_block_size,
                  max_seconds):
        """Benchmark node IO performance"""
        try:
            if underlying_device_name is not None:
                # LVM is based on physical device,
                # benchmark VG directly
                underlying_device_uuid = fs_linux.blk_uuid(
                    underlying_device_name
                )
                max_iops_result = diskbenchmark.benchmark_vg(
                    vg_name,
                    benchmark_volume,
                    rw_type,
                    job_number,
                    thread_number,
                    iops_block_size,
                    max_seconds
                )
                max_bps_result = diskbenchmark.benchmark_vg(
                    vg_name,
                    benchmark_volume,
                    rw_type,
                    job_number,
                    thread_number,
                    bps_block_size,
                    max_seconds
                )
            elif underlying_image_path is not None:
                # LVM is based on loop device,
                # benchmark underlying physical device of image file
                underlying_device_uuid = fs_linux.blk_uuid(
                    fs_linux.maj_min_to_blk(
                        *fs_linux.maj_min_from_path(underlying_image_path)
                    )
                )
                benchmark_path = os.path.join(
                    underlying_image_path,
                    'benchmark'
                )
                max_iops_result = diskbenchmark.benchmark(
                    benchmark_path,
                    benchmark_volume,
                    rw_type,
                    job_number,
                    thread_number,
                    iops_block_size,
                    max_seconds
                )
                max_bps_result = diskbenchmark.benchmark(
                    benchmark_path,
                    benchmark_volume,
                    rw_type,
                    job_number,
                    thread_number,
                    bps_block_size,
                    max_seconds
                )
                if os.path.isdir(benchmark_path):
                    shutil.rmtree(benchmark_path)
            else:
                _LOGGER.error('No underlying device, please specify '
                              '--underlying-device-name/'
                              '--underlying-image-path')
                return

            diskbenchmark.write(
                benchmark_publish_file,
                {underlying_device_uuid: {
                    'read_bps': max_bps_result['read_bps'],
                    'write_bps': max_bps_result['write_bps'],
                    'read_iops': max_iops_result['read_iops'],
                    'write_iops': max_iops_result['write_iops']
                }}
            )
        except subproc.CommandAliasError:
            _LOGGER.error(_ALIAS_ERROR_MESSAGE)

    del benchmark


def init():
    """Return top level command handler."""

    @click.group()
    @click.option('--aliases-path', required=False,
                  envvar='TREADMILL_ALIASES_PATH',
                  help='Colon separated command alias paths')
    def node_group(aliases_path):
        """Manage Treadmill node data"""
        if aliases_path:
            os.environ['TREADMILL_ALIASES_PATH'] = aliases_path

    lvm_group(node_group)
    benchmark_group(node_group)

    return node_group
