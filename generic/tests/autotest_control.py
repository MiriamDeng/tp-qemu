import logging
import os
import sys

from autotest.client.shared import error
from virttest import utils_test


def run(test, params, env):
    """
    Run an autotest test inside a guest.

    :param test: QEMU test object.
    :param params: Dictionary with test parameters.
    :param env: Dictionary with the test environment.
    """
    vm = env.get_vm(params["main_vm"])
    vm.verify_alive()
    timeout = int(params.get("login_timeout", 360))
    session = vm.wait_for_login(timeout=timeout)

    # Collect test parameters
    timeout = int(params.get("test_timeout", 300))
    control_args = params.get("control_args")
    control_path = os.path.join(
        test.virtdir, "control", params.get("test_control_file")
    )
    ignore_sess_terminated = params.get("ignore_session_terminated") == "yes"
    outputdir = test.outputdir

    utils_test.run_autotest(
        vm,
        session,
        control_path,
        timeout,
        outputdir,
        params,
        control_args=control_args,
        ignore_session_terminated=ignore_sess_terminated,
    )


def run_autotest_control_background(test, params, env, test_control_file="control"):
    """
    Wrapper of run() and make it run in the background through
    fork() and let it run in the child process.
    1) Flush the stdio.
    2) Build test params which is received from arguments and used by
       run()
    3) Fork the process and let the run() run in the child
    4) Catch the exception raise by run() and exit the child with
       non-zero return code.
    5) If no exception catched, return 0

    :param test: QEMU test object
    :param params: Dictionary with the test parameters
    :param env: Dictionary with test environment.
    :param test_control_file: The control file of autotest running in the guest
    """

    def flush():
        sys.stdout.flush()
        sys.stderr.flush()

    logging.info("Running autotest background ...")
    flush()
    pid = os.fork()
    if pid:
        # Parent process
        return pid

    flag_fname = "/tmp/autotest-flag-file-pid-" + str(os.getpid())
    open(flag_fname, "w").close()
    try:
        params["test_control_file"] = test_control_file
        # Launch autotest
        run(test, params, env)
        os.remove(flag_fname)
    except error.TestFail as message_fail:
        logging.info("[Autotest Background FAIL] %s", message_fail)
        os.remove(flag_fname)
        os._exit(1)
    except error.TestError as message_error:
        logging.info("[Autotest Background ERROR] %s", message_error)
        os.remove(flag_fname)
        os._exit(2)
    logging.info("[Auototest Background GOOD]")
    os._exit(0)


def wait_autotest_background(pid):
    """
    Wait for background autotest finish.

    :param pid: Pid of the child process executing background autotest
    """
    logging.info("Waiting for background autotest to finish ...")

    (pid, s) = os.waitpid(pid, 0)
    status = os.WEXITSTATUS(s)
    if status != 0:
        return False
    return True
