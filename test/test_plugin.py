"""Tests."""
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
