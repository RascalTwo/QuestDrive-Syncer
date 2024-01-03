import pytest
from unittest.mock import patch, Mock
from questdrive_syncer.app import main


@patch("questdrive_syncer.app.is_online", return_value=False)
@patch("builtins.print")
def test_message_if_not_online(mock_print: Mock, mock_is_online: Mock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_print.assert_called_once_with(
        'QuestDrive not found at "http://192.168.254.75:7123/"'
    )


@patch("questdrive_syncer.app.is_online", return_value=False)
def test_failed_status_code(mock_is_online: Mock) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 3


@patch("questdrive_syncer.app.is_online", return_value=True)
@patch("builtins.print")
def test_successful(mock_print: Mock, mock_is_online: Mock) -> None:
    mock_print.assert_not_called()
