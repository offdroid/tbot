"""
TBot selftests
--------------
"""
import tbot


@tbot.testcase
def selftest(tb: tbot.TBot) -> None:
    """ TBot self test """
    tbot.log.message("Testing shell functionality ...")
    tb.call("selftest_noenv_shell")
    tb.call("selftest_env_shell")
    tb.call("selftest_board_shell")
    tb.call("selftest_powercycle")
    tb.call("selftest_nested_boardshells")

    tbot.log.message("Testing testcase functionality ...")
    tb.call("selftest_testcase_calling")
    tb.call("selftest_test_failures")
    tb.call("selftest_wrong_parameter_type")

    tbot.log.message("Testing logger ...")
    tb.call("selftest_logger")

    tbot.log.message("Testing builtin testcases ...")
    tb.call("selftest_builtin_tests")
    tb.call("selftest_builtin_errors")

    tbot.log.message("Testing config ...")
    tb.call("selftest_config")

    tbot.log.message("Testing machines ...")
    tb.call("selftest_with_machine")

    tbot.log.message("Testing buildhost ...")
    tb.call("selftest_buildhost")
    tb.call("selftest_buildhost_bad_ssh")