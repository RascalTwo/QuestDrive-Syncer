"""Tests for the helpers module."""
import sys
import time
from types import SimpleNamespace
from unittest.mock import mock_open

import pytest
from pytest_mock import MockerFixture

from questdrive_syncer.helpers import LockError, has_enough_free_space, lock


class TestHasEnoughFreeSpace:
    """Tests for the has_enough_free_space() function."""

    @staticmethod
    def test_calls_mkdir(mocker: MockerFixture) -> None:
        """Returns True when there is enough free space."""
        mock_mkdir = mocker.patch("pathlib.Path.mkdir")

        has_enough_free_space(0)

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @staticmethod
    def test_enough(mocker: MockerFixture) -> None:
        """Returns True when there is enough free space."""
        mocker.patch(
            "os.statvfs",
            return_value=SimpleNamespace(f_frsize=1, f_bavail=1024**3 * 2),
        )

        assert has_enough_free_space(1024) is True

    @staticmethod
    def test_not_enough(mocker: MockerFixture) -> None:
        """Returns False when there is not enough free space."""
        mocker.patch(
            "os.statvfs",
            return_value=SimpleNamespace(f_frsize=1, f_bavail=1024**3 * 2),
        )

        assert has_enough_free_space(1025) is False


class TestLock:
    """Tests for the lock() decorator."""

    @staticmethod
    def test_creates_lock_file(mocker: MockerFixture) -> None:
        """Creates a lock file."""
        decorated = lock()(lambda: time.sleep(0.01))
        mocked_open = mocker.patch("pathlib.Path.open", mock_open())
        mocker.patch("pathlib.Path.unlink")

        decorated()

        mocked_open.assert_called_once_with("w")

    @staticmethod
    def test_deletes_lock_file(mocker: MockerFixture) -> None:
        """Deletes a lock file."""
        decorated = lock()(lambda: time.sleep(0.01))
        mocker.patch("pathlib.Path.open", mock_open())
        mock_unlink = mocker.patch("pathlib.Path.unlink")

        decorated()
        time.sleep(0.02)

        mock_unlink.assert_called_once()

    @staticmethod
    def test_deletes_lock_file_on_error(mocker: MockerFixture) -> None:
        """Deletes a lock file even if there's an error."""

        def raise_exception() -> None:
            raise Exception  # noqa: TRY002

        decorated = lock()(raise_exception)
        mocker.patch("pathlib.Path.open", mock_open())
        mock_unlink = mocker.patch("pathlib.Path.unlink")

        with pytest.raises(Exception):  # noqa: B017, PT011
            decorated()
        time.sleep(0.02)

        mock_unlink.assert_called_once()

    @staticmethod
    def test_deletes_lock_file_on_exit(mocker: MockerFixture) -> None:
        """Deletes a lock file even if the system exits."""

        def raise_exception() -> None:
            sys.exit()

        decorated = lock()(raise_exception)
        mocker.patch("pathlib.Path.open", mock_open())
        mock_unlink = mocker.patch("pathlib.Path.unlink")

        with pytest.raises(SystemExit):
            decorated()
        time.sleep(0.02)

        mock_unlink.assert_called_once()

    @staticmethod
    def test_makes_additional_calls_to_wait(mocker: MockerFixture) -> None:
        """Makes additional calls to wait."""
        decorated = lock(mode="wait")(lambda: time.sleep(0.01))
        mocker.patch("pathlib.Path.open", mock_open())
        mocker.patch("pathlib.Path.unlink")
        mocker.patch("pathlib.Path.exists", side_effect=[False, True, True, False])

        first_started = time.time()
        decorated()
        first_finished = time.time()
        second_started = time.time()
        decorated()
        second_finished = time.time()

        first_duration = first_finished - first_started
        assert first_duration < 0.015  # noqa: PLR2004
        second_duration = second_finished - second_started
        assert second_duration > 0.015  # noqa: PLR2004

    @staticmethod
    def test_makes_additional_calls_fail(mocker: MockerFixture) -> None:
        """Makes additional calls to fail."""
        decorated = lock(mode="fail")(lambda: time.sleep(0.01))
        mocker.patch("pathlib.Path.open", mock_open(read_data="123"))
        mocker.patch("pathlib.Path.unlink")
        mocker.patch(
            "pathlib.Path.exists",
            side_effect=[False, True],
        )

        decorated()
        with pytest.raises(LockError):
            decorated()
