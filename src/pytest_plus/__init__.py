"""PyTest Config File."""

from __future__ import annotations

import logging
import os
import re
import shutil

import pytest
from _pytest.terminal import TerminalReporter

_logger = logging.getLogger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ini options."""
    parser.addini(
        "check_test_duplicate",
        help="Warn when the same test function name appears in more than one file.",
        type="bool",
        default=True,
    )
    parser.addini(
        "check_test_id_regex",
        help="Warn when a test id contains characters that are awkward to paste in a terminal.",
        type="bool",
        default=True,
    )
    parser.addini(
        "max_test_id_length",
        help="Warn when a test id is longer than this many characters. Set to 0 to disable.",
        default="60",
    )
    parser.addini(
        "reqpass",
        help="If set to a number greater than 0, fail the session unless exactly that many tests passed.",
        default="0",
    )


def _env_or_ini_int(config: pytest.Config, env_name: str, ini_name: str) -> int:
    if env_name in os.environ:
        return int(os.environ[env_name])
    return int(config.getini(ini_name))


def _env_or_ini_bool(config: pytest.Config, env_name: str, ini_name: str) -> bool:
    if env_name in os.environ:
        return bool(int(os.environ[env_name]))
    return bool(config.getini(ini_name))


def get_max_test_id_length(config: pytest.Config) -> int:
    """Return max test id length."""
    return _env_or_ini_int(config, "PYTEST_MAX_TEST_ID_LENGTH", "max_test_id_length")


def get_test_id_regex(config: pytest.Config) -> re.Pattern[str] | None:
    """Return regex to use for checking test ids."""
    if _env_or_ini_bool(config, "PYTEST_CHECK_TEST_ID_REGEX", "check_test_id_regex"):
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
    req_passed = _env_or_ini_int(session.config, "PYTEST_REQPASS", "reqpass")
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

    # If running under CI (Github Actions included) and inside a venv, do
    # copy all pytest own logs inside $VIRTUAL_ENV/log, for collection.
    venv = os.environ.get("VIRTUAL_ENV", "")
    if os.environ.get("CI", "0") != "0" and venv:
        # Copy can fail if the source folder was already removed, but we
        # should not fail due to this.
        try:
            shutil.copytree(
                src=session.config._tmp_path_factory.getbasetemp(),  # type: ignore[attr-defined] # noqa: SLF001
                dst=venv + "/log",
                dirs_exist_ok=True,
            )
        except OSError as e:
            _logger.warning("Failed to copy pytest logs to $VIRTUAL_ENV/log: %s", e)


@pytest.hookimpl(tryfirst=True)  # type: ignore[misc,unused-ignore]
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Ensure testing fails if tests have duplicate names."""
    messages = []
    names = {}
    max_test_id_length = get_max_test_id_length(config)
    test_id_regex = get_test_id_regex(config)
    check_duplicate = _env_or_ini_bool(
        config,
        "PYTEST_CHECK_TEST_DUPLICATE",
        "check_test_duplicate",
    )
    for item in items:
        base_name = item.name.split("[")[0]
        if base_name not in names:
            names[base_name] = item.location
        elif item.location[:2] != names[base_name][:2] and check_duplicate:
            msg = f"Duplicate test name '{base_name}', found at {item.location[0]}:{item.location[1]} and {names[base_name][0]}:{names[base_name][1]}"
            if msg not in messages:
                messages.append(msg)
        if hasattr(item, "callspec"):
            test_id = item.callspec.id
            if max_test_id_length and len(test_id) > max_test_id_length:
                messages.append(
                    f"{item} has an id that looks above {max_test_id_length} characters.",
                )
            elif test_id_regex and not test_id_regex.match(test_id):
                messages.append(
                    f"Test {item} has an id that does not match our safe pattern '{test_id_regex.pattern}' for use with a terminal.",
                )
    for msg in messages:
        _logger.warning(msg)
