from types import SimpleNamespace
from unittest.mock import Mock, patch

from .helpers import has_enough_free_space


@patch("os.statvfs", return_value=SimpleNamespace(f_frsize=1, f_bavail=1024**3 * 2))
def test_has_enough_free_space_enough(mock_statvfs: Mock) -> None:
    assert has_enough_free_space(1024) is True


@patch("os.statvfs", return_value=SimpleNamespace(f_frsize=1, f_bavail=1024**3 * 2))
def test_has_enough_free_space_not_enough(mock_statvfs: Mock) -> None:
    assert has_enough_free_space(1025) is False
