from unittest.mock import patch, Mock


@patch("builtins.print")
def test_main(mock_print: Mock) -> None:
    import questdrive_syncer.__main__  # noqa: F401

    mock_print.assert_called_once_with(10)
