"""
Run U-Boot tests on real hardware
---------------------------------
"""
import pathlib
import typing
import tbot
from tbot import tc


@tbot.testcase
def just_uboot_tests(tb: tbot.TBot, *, buildhost: typing.Optional[str] = None) -> None:
    """
    Run U-Boot tests on the currently existing (possibly dirty) U-Boot tree.

    :param str buildhost: The buildhost where U-Boot can be build AND tested.
                      Usually this is a 'local' buildhost, which means,
                      U-Boot is built on the labhost.
    """
    buildhost = buildhost or tb.config["build.local"]

    uboot_dir = tb.call("uboot_checkout", clean=False, buildhost=buildhost)
    toolchain = tb.call("toolchain_get", buildhost=buildhost)

    tb.call("uboot_tests", builddir=uboot_dir, toolchain=toolchain)


@tbot.testcase
def uboot_tests(
    tb: tbot.TBot,
    *,
    buildhost: typing.Optional[str] = None,
    builddir: tc.UBootRepository,
    toolchain: tc.Toolchain,
    test_config: typing.Optional[pathlib.PurePosixPath] = None,
    test_hooks: typing.Optional[pathlib.PurePosixPath] = None,
    test_boardname: typing.Optional[str] = None,
    test_maxfail: typing.Optional[int] = None,
) -> None:
    """
    Run U-Boot tests on real hardware

    :param str buildhost: The buildhost where U-Boot can be build AND tested.
                      Usually this is a 'local' buildhost, which means,
                      U-Boot is built on the labhost.
    :param UBootRepository builddir: The U-Boot checkout that should be tested. Must be a
                     UBootRepository meta object
    :param Toolchain toolchain: What toolchain to use (The testsuite rebuilds the
                      U-Boot binary)
    :param pathlib.PurePosixPath test_config: An optional config file for the testsuite,
                        defaults to ``tb.config["uboot.test.config"]``
    :param pathlib.PurePosixPath test_hooks: Path to the U-Boot python testsuite hooks for the
                       currently selected board, defaults to
                       ``tb.config["uboot.test.hooks"]``
    :param str test_boardname: Name of the board, usually the name of the defconfig minus
                           the ``"_defconfig"``, defaults to
                           ``tb.config["uboot.test.boardname"]``
    :param int test_maxfail: Maximum number of failed tests before aborting, defaults
                         to ``tb.config["uboot.test.maxfail"]``
    """
    buildhost = buildhost or tb.config["build.local"]
    test_config = test_config or tb.config["uboot.test.config", None]
    test_hooks = test_hooks or tb.config["uboot.test.hooks"]
    test_boardname = test_boardname or tb.config["uboot.test.boardname"]
    test_maxfail = test_maxfail or tb.config["uboot.test.maxfail", None]

    tbot.log.doc(
        """
## Run U-Boot tests ##
U-Boot contains a python test suite that can be run on the host and on the target. \
Here we will run it on the target. Make sure all dependencies are met.  Refer to \
<http://git.denx.de/?p=u-boot.git;a=blob;f=test/py/README.md> for a list.
"""
    )

    if test_config is not None:
        tbot.log.doc(
            """To ensure that the testcases work properly, we need a \
configuration file for the testsuite. Copy the config file into `test/py` inside \
the U-Boot tree:
"""
        )

        tbot.log.debug(f"Using '{test_config}' for the U-Boot test suite")
        filename = test_config.name
        target = builddir / "test" / "py" / filename
        tb.shell.exec0(f"cp {test_config} {target}")

        tbot.log.doc("The config file can be found in the appendix of this document.\n")
        cfg_file_content = tb.shell.exec0(f"cat {test_config}", log_show=False)
        tbot.log.doc_appendix(
            f"U-Boot test config: {filename}",
            f"""```python
{cfg_file_content}
```""",
        )

    def run_tests(tb: tbot.TBot) -> None:
        """ Actually run the testsuite """
        tbot.log.doc(
            """Clean the workdir because the U-Boot testsuite won't \
recompile if it is dirty.
"""
        )

        tb.shell.exec0(f"make mrproper", log_show_stdout=False)

        tbot.log.doc(
            "Install the necessary hooks and start the \
testsuite using the following commands:\n"
        )
        tb.shell.exec0(f"export PATH={test_hooks}:$PATH")

        with tb.machine(tbot.machine.MachineBoardDummy(turn_on=False)) as tb:
            max_fail_param = (
                f"--maxfail={test_maxfail}" if test_maxfail is not None else ""
            )
            tb.shell.exec0(
                f"\
./test/py/test.py --bd {test_boardname} --build {max_fail_param}"
            )

            tbot.log.doc(
                "The U-Boot testsuite, which has hopefully finished \
successfully by now, is not capable of turning off the board itself. \
You have to do that manually:\n"
            )

    has_venv = tb.config["uboot.test.use_venv", True]
    tbot.log.debug(f"Virtualenv availability: {has_venv}")
    if has_venv:
        tbot.log.doc("Create a virtualenv and install pytest inside it:\n")

        # Setup python
        tb.shell.exec0(f"cd {builddir}; virtualenv-2.7 venv", log_show_stdout=False)

        tbot.log.doc(
            """The testsuite will rebuild the U-Boot binary. For doing so, \
it needs the correct toolchain enabled.
"""
        )

        @tb.call_then("toolchain_env", toolchain=toolchain)
        def setup_venv(tb: tbot.TBot) -> None:  # pylint: disable=unused-variable
            """ Actual test run """
            tb.shell.exec0(f"cd {builddir}")
            tb.shell.exec0(
                f"VIRTUAL_ENV_DISABLE_PROMPT=1 source venv/bin/activate",
                log_show_stdout=False,
            )
            tb.shell.exec0(f"pip install pytest", log_show_stdout=False)

            tb.call(run_tests)

    else:
        tbot.log.doc(
            """Here we do not use virtualenv because our build host \
does not have it installed, but it is recommended to do so.
"""
        )

        tbot.log.doc(
            """The testsuite will rebuild the U-Boot binary. For doing so, \
it needs the correct toolchain enabled.
"""
        )

        @tb.call_then("toolchain_env", toolchain=toolchain)
        def setup_no_venv(tb: tbot.TBot) -> None:  # pylint: disable=unused-variable
            """ Actual test run """
            tb.shell.exec0(f"cd {builddir}")

            tb.call(run_tests)