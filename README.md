# PyTest Plus Plugin :: extends pytest functionality

[![PyPI version](https://img.shields.io/pypi/v/pytest-plus.svg)](https://pypi.org/project/pytest-plus)
[![Python versions](https://img.shields.io/pypi/pyversions/pytest-plus.svg)](https://pypi.org/project/pytest-plus)
![CI](https://github.com/pytest-dev/pytest-plus/workflows/tox/badge.svg)
[![Python Black Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

This plugin aims to be used to host multiple basic pytest extensions that meet
the following criteria:

- Downgrade gracefully, meaning that if the plugin is removed, you will still
  be able to run pytest

## PYTEST_REQPASS

If you define environment variable `PYTEST_REQPASS=123` and at the end of the
testing the number of passed tests is
not exactly 123, pytest will return exit code 1.

This feature is aimed for CI usage in order to prevent accidental skipping of
some tests. We do expect users to define this variable within their own CI job
definitions. The number of tests executed is likely to be dependent on the CI
job.

We discourage defining this inside places like `tox.ini` because when a
developer runs tests, they are likely to endup running a different number of
tests. Also, this feature makes no sense if you try to mention a specific test.

## Avoiding duplicate test function names

While pytest allows users to have the same test function names in different
files, that makes it harder to identify and copy/paste the test name in order
to reproduce the failure locally. That is why this plugin forces its users to
avoid having the same function name anywhere in the tested project.

You can disable this check by defining `PYTEST_CHECK_TEST_DUPLICATE=0`.

## Avoiding problematic test identifiers

This plugin will raise errors when it encounters test IDs that are either too
long or that contain unsafe characters. While pytest is very flexible in allowing
a wide range of test IDs, using these does make development harder as it prevents
people from doing a copy/paste with failed test and pasting in in their terminal
to reproduce the failed test locally.

You can disable regex check by defining `PYTEST_CHECK_TEST_ID_REGEX=0`.

You can disable the length check by defining `PYTEST_MAX_TEST_ID_LENGTH=0`.

## Release process

Releases are triggered from [GitHub Releases](https://github.com/pytest-dev/pytest-plus/releases)
page.

## Links

- [MIT](http://opensource.org/licenses/MIT)
- [file an issue](https://github.com/pytest-dev/pytest-plus/issues)
- [pytest](https://github.com/pytest-dev/pytest)
- [tox](https://tox.readthedocs.io/en/latest/)
- [pip](https://pypi.org/project/pip/)
- [PyPI](https://pypi.org/project)
