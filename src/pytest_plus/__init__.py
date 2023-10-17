"""PyTest Config File."""

from __future__ import print_function
import os
from typing import List

import pytest


def pytest_sessionfinish(session, exitstatus):
    """Assure passed test match PYTEST_REQPASS value.

    Assures that pytest returns an error code when the number of expected passed
    tests does not match the PYTEST_REQPASS value.  When not defined or zero
    that functionality is ignored.
    """
    terminalreporter = session.config.pluginmanager.get_plugin("terminalreporter")
    req_passed = int(os.environ.get("PYTEST_REQPASS", "0"))
    if req_passed and not session.config.option.collectonly:
        passed = 0
        for x in terminalreporter.stats.get("passed", []):
            if x.when == "call" and x.outcome == "passed":
                passed += 1
        if passed != req_passed:
            terminalreporter.write_line(
                "ERROR: {} passed test but expected number was {}. "
                " If that is expected please update PYTEST_REQPASS value for the failed job.".format(
                    passed, req_passed
                )
            )
            session.exitstatus = 1


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    errors = []
    names = {}
    for item in items:
        base_name = item.name.split("[")[0]
        if base_name not in names:
            names[base_name] = item.location
        elif item.location[:2] != names[base_name][:2]:
            error = f"Duplicate test name '{base_name}', found at {item.location[0]}:{item.location[1]} and {names[base_name][0]}:{names[base_name][1]}"
            if error not in errors:
                errors.append(error)
    if errors:
        raise pytest.UsageError(
            f"Failed run due to following issues being identified:\n{os.linesep.join(errors)}"
        )
