"""PyTest Config File."""

from __future__ import print_function
import os
import pytest
import sys


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Assure passed test match PYTEST_REQPASS value.

    Assures that pytest returns an error code when the number of expected passed
    tests does not match the PYTEST_REQPASS value.  When not defined or zero
    that functionality is ignored.
    """
    yield
    req_passed = int(os.environ.get("PYTEST_REQPASS", "0"))
    if req_passed and not config.option.collectonly:
        passed = 0
        for x in terminalreporter.stats.get("passed", []):
            if x.when == "call" and x.outcome == "passed":
                passed += 1
        if passed != req_passed:
            terminalreporter.write_line(
                "ERROR: {} passed test but expected number was {}. "
                " If that is expected please update PYTEST_REQPASS value for the failed job in zuul.d/layout.yaml file.".format(
                    passed, req_passed
                )
            )
            sys.exit(1)
