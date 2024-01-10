"""Tests."""
import os

import pytest

pytest_plugins = ["pytester"]


def test_duplicate_test_name(pytester: pytest.Pytester) -> None:
    """Validates that we can detect duplicate test names."""
    p1 = pytester.makepyfile(
        test_one="""
            def test_a():
                assert True
            """,
    )
    p2 = pytester.makepyfile(
        test_two="""
            def test_a():
                assert True
            """,
    )

    result = pytester.runpytest_inprocess(p1, p2)
    assert (
        result.errlines[0]
        == "ERROR: Failed run due to following issues being identified:"
    )
    assert (
        result.errlines[1]
        == "Duplicate test name 'test_a', found at test_two.py:0 and test_one.py:0"
    )
    assert result.ret == pytest.ExitCode.USAGE_ERROR


@pytest.mark.parametrize(
    ("rc", "disable"),
    [
        pytest.param(pytest.ExitCode.USAGE_ERROR, False, id="0"),
        pytest.param(pytest.ExitCode.OK, True, id="1"),
    ],
)
def test_check_test_id(pytester: pytest.Pytester, rc: int, *, disable: bool) -> None:
    """Validates that we can detect duplicate test names."""
    if disable:
        os.environ["PYTEST_CHECK_TEST_ID_REGEX"] = "0"
    p1 = pytester.makepyfile(
        test_one="""
            import pytest

            @pytest.mark.parametrize(
                "some",
                (pytest.param("", id="invalid name"),),
            )
            def test_a(some: str):
                assert True
            """,
    )

    result = pytester.runpytest_inprocess("--collect-only", p1)
    if not disable:
        assert (
            "Test <Function test_a[invalid name]> has an id that does not match our safe pattern '^[\\w_\\-\\.:]+$' for use with a terminal."
            in result.stderr.lines
        )
    assert result.ret == rc


def test_check_test_id_length(pytester: pytest.Pytester) -> None:
    """Validates that we can detect duplicate test names."""
    p1 = pytester.makepyfile(
        test_one="""
            import pytest

            @pytest.mark.parametrize(
                "some",
                (pytest.param("", id="this-is-too-long-for-our-taste-so-we-ask-you-to-make-it-shorter"),),
            )
            def test_a(some: str):
                assert True
            """,
    )

    result = pytester.runpytest_inprocess("--collect-only", p1)
    assert (
        "<Function test_a[this-is-too-long-for-our-taste-so-we-ask-you-to-make-it-shorter]> has an id that looks above 60 characters."
        in result.stderr.lines
    )
    assert result.ret == pytest.ExitCode.USAGE_ERROR
