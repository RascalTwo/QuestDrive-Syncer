"""Tests for the helpers module."""
from types import SimpleNamespace

from pytest_mock import MockerFixture

from .helpers import has_enough_free_space


def test_has_enough_free_space_calls_mkdir(mocker: MockerFixture) -> None:
    """has_enough_free_space() returns True when there is enough free space."""
    mock_mkdir = mocker.patch("pathlib.Path.mkdir")

    has_enough_free_space(0)

    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_has_enough_free_space_enough(mocker: MockerFixture) -> None:
    """has_enough_free_space() returns True when there is enough free space."""
    mocker.patch(
        "os.statvfs",
        return_value=SimpleNamespace(f_frsize=1, f_bavail=1024**3 * 2),
    )

    assert has_enough_free_space(1024) is True


def test_has_enough_free_space_not_enough(mocker: MockerFixture) -> None:
    """has_enough_free_space() returns False when there is not enough free space."""
    mocker.patch(
        "os.statvfs",
        return_value=SimpleNamespace(f_frsize=1, f_bavail=1024**3 * 2),
    )

    assert has_enough_free_space(1025) is False
