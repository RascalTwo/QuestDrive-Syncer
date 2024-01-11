"""Tests for the version_bumped hook."""
from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from hooks.version_bumped import check, get_old_and_new_versions, is_version_bumped

if TYPE_CHECKING:  # pragma: no cover
    from unittest.mock import Mock

    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    ("versions", "expected"),
    [
        (([0, 1, 2], [0, 1, 3]), True),
        (([0, 1, 2], [0, 1, 2]), False),
        (([0, 1, 2], [0, 1, 1]), False),
        (([0, 1, 2], [0, 2, 1]), True),
        (([0, 1, 2], [1, 1, 2]), True),
        (([0, 1, 2], [1, 1, 32]), True),
    ],
)
def test_is_version_bumped(
    versions: tuple[list[int], list[int]],
    expected: bool,  # noqa: FBT001
) -> None:
    """is_version_bumped() returns the expected boolean."""
    assert is_version_bumped(*versions) == expected


class TestCheck:
    """Tests for check()."""

    @staticmethod
    def make_check_mocks(
        mocker: MockerFixture,
        get_old_and_new_versions: None | tuple[list[int], list[int]],
        *,
        is_version_bumped: bool = True,
    ) -> Mock:
        """Create mocks for check()."""
        mocker.patch(
            "hooks.version_bumped.get_old_and_new_versions",
            return_value=get_old_and_new_versions,
        )
        mocker.patch(
            "hooks.version_bumped.is_version_bumped",
            return_value=is_version_bumped,
        )
        return mocker.patch("builtins.print")

    @staticmethod
    def test_fails_if_no_versions(mocker: MockerFixture) -> None:
        """Fails if there are no versions."""
        mock_print = TestCheck.make_check_mocks(mocker, None, is_version_bumped=True)

        with pytest.raises(SystemExit) as e:
            check()

        mock_print.assert_called_once_with(
            "You must bump the version in pyproject.toml before committing.",
        )
        assert e.value.code == 1

    @staticmethod
    def test_fails_if_versions_not_bumped(
        mocker: MockerFixture,
    ) -> None:
        """Fails if the versions are not bumped."""
        mock_print = TestCheck.make_check_mocks(
            mocker,
            ([0, 1, 2], [0, 1, 2]),
            is_version_bumped=False,
        )

        with pytest.raises(SystemExit) as e:
            check()

        mock_print.assert_called_once_with(
            "You must bump the version in pyproject.toml before committing.",
        )
        assert e.value.code == 1

    @staticmethod
    def test_prints_version_changes_if_successful(mocker: MockerFixture) -> None:
        """Prints the two versions if successful."""
        mock_print = TestCheck.make_check_mocks(
            mocker,
            ([0, 1, 2], [0, 1, 3]),
            is_version_bumped=True,
        )

        check()

        mock_print.assert_called_once_with("Version bumped from 0.1.2 to 0.1.3.")


class TestGetOldAndNewVersions:
    """Tests for get_old_and_new_versions()."""

    @staticmethod
    def test_require_old_version(mocker: MockerFixture) -> None:
        """Requires the old version."""
        mocker.patch(
            "subprocess.run",
            return_value=SimpleNamespace(stdout='+version = "0.1.2"'),
        )

        assert get_old_and_new_versions() is None

    @staticmethod
    def test_require_new_version(mocker: MockerFixture) -> None:
        """Requires the new version."""
        mocker.patch(
            "subprocess.run",
            return_value=SimpleNamespace(stdout='-version = "0.1.2"'),
        )

        assert get_old_and_new_versions() is None

    @staticmethod
    def test_require_both_version(mocker: MockerFixture) -> None:
        """Requires both versions."""
        mocker.patch(
            "subprocess.run",
            return_value=SimpleNamespace(
                stdout='-version = "0.1.2"\n+version = "0.1.3"',
            ),
        )

        assert get_old_and_new_versions() == ([0, 1, 2], [0, 1, 3])
