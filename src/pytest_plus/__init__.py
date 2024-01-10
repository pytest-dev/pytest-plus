"""PyTest Config File."""
from __future__ import annotations

import os
import re

import pytest
from _pytest.terminal import TerminalReporter

PYTEST_CHECK_TEST_DUPLICATE = int(os.environ.get("PYTEST_CHECK_TEST_DUPLICATE", "1"))


def get_max_test_id_length() -> int:
    """Return max test id length."""
    return int(os.environ.get("PYTEST_MAX_TEST_ID_LENGTH", "60"))


def get_test_id_regex() -> None | re.Pattern[str]:
    """Return regex to use for checking test ids."""
    if int(os.environ.get("PYTEST_CHECK_TEST_ID_REGEX", "1")):
        return re.compile(r"^[\w_\-\.:]+$")
    return None


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Assure passed test match PYTEST_REQPASS value.

    Assures that pytest returns an error code when the number of expected passed
    tests does not match the PYTEST_REQPASS value.  When not defined or zero
    that functionality is ignored.
    """
    terminalreporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if not isinstance(terminalreporter, TerminalReporter):
        raise TypeError  # pragma: no cover
    req_passed = int(os.environ.get("PYTEST_REQPASS", "0"))
    if req_passed and not session.config.option.collectonly:
        passed = 0
        for x in terminalreporter.stats.get("passed", []):
            if x.when == "call" and x.outcome == "passed":
                passed += 1
        if passed != req_passed:
            terminalreporter.write_line(
                f"ERROR: {passed} passed test but expected number was {req_passed}. "
                " If that is expected please update PYTEST_REQPASS value for the failed job.",
            )
            session.exitstatus = 1


@pytest.hookimpl(tryfirst=True)  # type: ignore[misc,unused-ignore]
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Ensure testing fails if tests have duplicate names."""
    errors = []
    names = {}
    max_test_id_length = get_max_test_id_length()
    test_id_regex = get_test_id_regex()
    for item in items:
        base_name = item.name.split("[")[0]
        if base_name not in names:
            names[base_name] = item.location
        elif item.location[:2] != names[base_name][:2] and PYTEST_CHECK_TEST_DUPLICATE:
            error = f"Duplicate test name '{base_name}', found at {item.location[0]}:{item.location[1]} and {names[base_name][0]}:{names[base_name][1]}"
            if error not in errors:
                errors.append(error)
        if hasattr(item, "callspec"):
            test_id = item.callspec.id
            if max_test_id_length and len(test_id) > max_test_id_length:
                errors.append(
                    f"{item} has an id that looks above {max_test_id_length} characters.",
                )
            elif test_id_regex and not test_id_regex.match(test_id):
                errors.append(
                    f"Test {item} has an id that does not match our safe pattern '{test_id_regex.pattern}' for use with a terminal.",
                )
    if errors:
        msg = f"Failed run due to following issues being identified:\n{os.linesep.join(errors)}"
        raise pytest.UsageError(
            msg,
        )
