import logging
import re

from avocado.utils import process
from virttest import error_context


@error_context.context_aware
def run(test, params, env):
    """
    Test virtiofsd info.
    Steps:
        1. Check if virtiofsd version is the same with qemu-kvm.
        2. Check if copyright expired.

    :param test: QEMU test object.
    :param params: Dictionary with the test parameters.
    :param env: Dictionary with test environment.
    """
    cmd_get_vfsd_ver = params.get("cmd_get_vfsd_ver")
    cmd_get_qemu_ver = params.get("cmd_get_qemu_ver")
    error_context.context("Check virtiofsd info", logging.info)
    vfsd_info = process.system_output(cmd_get_vfsd_ver, shell=True).strip()
    pattern_ver = r'version.*(\d+.\d+.\d+)'.encode()
    vfsd_ver = re.findall(pattern_ver, vfsd_info, re.I)[0]
    qemu_kvm_info = process.system_output(cmd_get_qemu_ver, shell=True).strip()
    qemu_ver = re.findall(pattern_ver, qemu_kvm_info, re.I)[0]
    if vfsd_ver != qemu_ver:
        test.fail("virtiofsd version is %s which is wrong,"
                  "it should be %s" % (vfsd_ver, qemu_ver))
