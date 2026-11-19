"""Tests."""

import logging
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]


def _write_config(pytester: pytest.Pytester, kind: str, source: str) -> None:
    if kind == "toml":
        pytester.makepyprojecttoml(source)
    else:
        pytester.makeini(source)


def test_duplicate_test_name(
    pytester: pytest.Pytester,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validates that we can detect duplicate test names."""
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    monkeypatch.delenv("PYTEST_CHECK_TEST_DUPLICATE", raising=False)
    caplog.set_level(logging.INFO)
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
        "Duplicate test name 'test_a', found at test_two.py:0 and test_one.py:0"
        in caplog.text
    )
    assert result.ret == 0, result.stdout.lines


@pytest.mark.parametrize(
    ("rc", "disable"),
    [
        pytest.param(pytest.ExitCode.OK, False, id="0"),
        pytest.param(pytest.ExitCode.OK, True, id="1"),
    ],
)
def test_check_test_id(
    pytester: pytest.Pytester,
    rc: int,
    *,
    disable: bool,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validates that we can detect duplicate test names."""
    caplog.set_level(logging.WARNING)
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    if disable:
        monkeypatch.setenv("PYTEST_CHECK_TEST_ID_REGEX", "0")
    else:
        monkeypatch.delenv("PYTEST_CHECK_TEST_ID_REGEX", raising=False)
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
            in caplog.text
        )
    assert result.ret == rc


def test_check_test_id_length(
    pytester: pytest.Pytester,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validates that we can detect duplicate test names."""
    caplog.set_level(logging.WARNING)
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    monkeypatch.delenv("PYTEST_MAX_TEST_ID_LENGTH", raising=False)
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
        in caplog.text
    )
    assert result.ret == pytest.ExitCode.OK


@pytest.mark.parametrize(
    ("kind", "source"),
    [
        (
            "toml",
            """
            [tool.pytest.ini_options]
            check_test_duplicate = false
            """,
        ),
        (
            "ini",
            """
            [pytest]
            check_test_duplicate = false
            """,
        ),
    ],
    ids=("toml", "ini"),
)
def test_check_test_duplicate_from_config(
    pytester: pytest.Pytester,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    source: str,
) -> None:
    """Ini config can disable the duplicate test name check."""
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    monkeypatch.delenv("PYTEST_CHECK_TEST_DUPLICATE", raising=False)
    caplog.set_level(logging.INFO)
    _write_config(pytester, kind, source)
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
    assert "Duplicate test name" not in caplog.text
    assert result.ret == 0, result.stdout.lines


@pytest.mark.parametrize(
    ("kind", "source"),
    [
        (
            "toml",
            """
            [tool.pytest.ini_options]
            check_test_id_regex = false
            """,
        ),
        (
            "ini",
            """
            [pytest]
            check_test_id_regex = false
            """,
        ),
    ],
    ids=("toml", "ini"),
)
def test_check_test_id_regex_from_config(
    pytester: pytest.Pytester,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    source: str,
) -> None:
    """Ini config can disable the test id regex check."""
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    monkeypatch.delenv("PYTEST_CHECK_TEST_ID_REGEX", raising=False)
    caplog.set_level(logging.WARNING)
    _write_config(pytester, kind, source)
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
    assert "does not match our safe pattern" not in caplog.text
    assert result.ret == pytest.ExitCode.OK


@pytest.mark.parametrize(
    ("kind", "source"),
    [
        (
            "toml",
            """
            [tool.pytest.ini_options]
            max_test_id_length = "0"
            """,
        ),
        (
            "ini",
            """
            [pytest]
            max_test_id_length = 0
            """,
        ),
    ],
    ids=("toml", "ini"),
)
def test_max_test_id_length_from_config(
    pytester: pytest.Pytester,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    source: str,
) -> None:
    """Ini config can disable the test id length check."""
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    monkeypatch.delenv("PYTEST_MAX_TEST_ID_LENGTH", raising=False)
    caplog.set_level(logging.WARNING)
    _write_config(pytester, kind, source)
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
    assert "has an id that looks above" not in caplog.text
    assert result.ret == pytest.ExitCode.OK


def test_env_var_overrides_ini(
    pytester: pytest.Pytester,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables win over ini, including when set to 0."""
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("PYTEST_CHECK_TEST_DUPLICATE", "0")
    monkeypatch.setenv("PYTEST_CHECK_TEST_ID_REGEX", "0")
    monkeypatch.setenv("PYTEST_MAX_TEST_ID_LENGTH", "0")
    monkeypatch.setenv("PYTEST_REQPASS", "0")
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        check_test_duplicate = true
        check_test_id_regex = true
        max_test_id_length = "5"
        reqpass = "9"
        """,
    )
    p1 = pytester.makepyfile(
        test_one="""
            import pytest

            @pytest.mark.parametrize(
                "some",
                (pytest.param("", id="bad id that is way too long"),),
            )
            def test_a(some: str):
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
    assert "Duplicate test name" not in caplog.text
    assert "does not match our safe pattern" not in caplog.text
    assert "has an id that looks above" not in caplog.text
    result.assert_outcomes(passed=2)
    assert result.ret == 0, result.stdout.lines


def test_reqpass_from_pyproject(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A matching reqpass ini value passes and CI logs are copied."""
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    venv = tmp_path / "venv"
    venv.mkdir()
    monkeypatch.setenv("VIRTUAL_ENV", str(venv))
    monkeypatch.setenv("CI", "true")
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        reqpass = "1"
        """,
    )
    pytester.makepyfile(
        test_one="""
            def test_a():
                assert True
            """,
    )

    result = pytester.runpytest_inprocess()
    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.OK, result.stdout.lines
    assert (venv / "log").is_dir()


def test_reqpass_from_pytest_ini(
    pytester: pytest.Pytester,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A mismatched reqpass ini value fails and log copy errors warn."""
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    caplog.set_level(logging.WARNING)
    venv = tmp_path / "venv"
    venv.write_text("not-a-directory")
    monkeypatch.setenv("VIRTUAL_ENV", str(venv))
    monkeypatch.setenv("CI", "true")
    pytester.makeini(
        """
        [pytest]
        reqpass = 3
        """,
    )
    pytester.makepyfile(
        test_one="""
            def test_a():
                assert True
            """,
    )

    result = pytester.runpytest_inprocess()
    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.TESTS_FAILED, result.stdout.lines
    assert any("expected number was 3" in line for line in result.stdout.lines)
    assert "Failed to copy pytest logs to $VIRTUAL_ENV/log" in caplog.text


def test_reqpass_collect_only(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reqpass is ignored when only collecting tests."""
    monkeypatch.delenv("PYTEST_REQPASS", raising=False)
    pytester.makeini(
        """
        [pytest]
        reqpass = 50
        """,
    )
    pytester.makepyfile(
        test_one="""
            def test_a():
                assert True
            """,
    )

    result = pytester.runpytest_inprocess("--collect-only")
    assert result.ret == pytest.ExitCode.OK, result.stdout.lines
    assert not any("expected number was" in line for line in result.stdout.lines)
