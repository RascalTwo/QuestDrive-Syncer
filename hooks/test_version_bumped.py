import pytest
from typing import Tuple
from types import SimpleNamespace
from .version_bumped import is_version_bumped, check, get_old_and_new_versions
from unittest.mock import patch, Mock


@pytest.mark.parametrize(
    "versions, expected",
    [
        [([0, 1, 2], [0, 1, 3]), True],
        [([0, 1, 2], [0, 1, 2]), False],
        [([0, 1, 2], [0, 1, 1]), False],
        [([0, 1, 2], [0, 2, 1]), True],
        [([0, 1, 2], [1, 1, 2]), True],
    ],
)
def test_is_version_bumped(
    versions: Tuple[list[int], list[int]], expected: bool
) -> None:
    assert is_version_bumped(*versions) == expected


@patch("hooks.version_bumped.get_old_and_new_versions", return_value=None)
@patch("builtins.print")
def test_check_fails_if_no_versions(
    mock_print: Mock, mock_get_old_and_new_versions: Mock
) -> None:
    with pytest.raises(SystemExit) as e:
        check()
    mock_print.assert_called_once_with(
        "You must bump the version in pyproject.toml before committing."
    )
    assert e.value.code == 1


@patch(
    "hooks.version_bumped.get_old_and_new_versions", return_value=([0, 1, 2], [0, 1, 2])
)
@patch("hooks.version_bumped.is_version_bumped", return_value=False)
@patch("builtins.print")
def test_check_fails_if_versions_not_bumped(
    mock_print: Mock, mock_is_version_bumped: Mock, mock_get_old_and_new_versions: Mock
) -> None:
    with pytest.raises(SystemExit) as e:
        check()
    mock_print.assert_called_once_with(
        "You must bump the version in pyproject.toml before committing."
    )
    assert e.value.code == 1


@patch(
    "hooks.version_bumped.get_old_and_new_versions", return_value=([0, 1, 2], [0, 1, 3])
)
@patch("hooks.version_bumped.is_version_bumped", return_value=True)
@patch("builtins.print")
def test_check_prints_version_changes_if_successful(
    mock_print: Mock, mock_is_version_bumped: Mock, mock_get_old_and_new_versions: Mock
) -> None:
    check()
    mock_print.assert_called_once_with("Version bumped from 0.1.2 to 0.1.3.")


@patch("subprocess.run", return_value=SimpleNamespace(stdout='+version = "0.1.2"'))
def test_get_old_and_new_versions_require_old_version(mock_run: Mock) -> None:
    assert get_old_and_new_versions() is None


@patch("subprocess.run", return_value=SimpleNamespace(stdout='-version = "0.1.2"'))
def test_get_old_and_new_versions_require_new_version(mock_run: Mock) -> None:
    assert get_old_and_new_versions() is None


@patch(
    "subprocess.run",
    return_value=SimpleNamespace(stdout='-version = "0.1.2"\n+version = "0.1.3"'),
)
def test_get_old_and_new_versions_require_both_version(mock_run: Mock) -> None:
    assert get_old_and_new_versions() == ([0, 1, 2], [0, 1, 3])
