import pytest
from unittest.mock import patch, Mock
from questdrive_syncer.app import main
from questdrive_syncer.api import Video
from datetime import datetime
import dataclasses


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


video = Video("filepath", "filename", datetime.now(), datetime.now(), 1.23, "url")
second_video = dataclasses.replace(video)
second_video.mb_size = 2.34


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.fetch_video_list_html",
    return_value=("url", "<tbody></tbody>"),
)
def test_print_when_successful(
    mock_fetch_video_list_html: Mock, mock_print: Mock
) -> None:
    main()
    mock_print.assert_any_call(
        "QuestDrive found running at http://192.168.254.75:7123/"
    )


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.parse_video_list_html",
    return_value=[],
)
@patch("questdrive_syncer.app.fetch_video_list_html", return_value=("url", "html"))
def test_calls_fetch_video_list_html_and_parse_video_list_html(
    mock_fetch_video_list_html: Mock, mock_parse_video_list_html: Mock, mock_print: Mock
) -> None:
    main()
    mock_fetch_video_list_html.assert_called_once()
    mock_parse_video_list_html.assert_called_once_with("url", "html")


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.parse_video_list_html",
    return_value=[video],
)
@patch("questdrive_syncer.app.fetch_video_list_html", return_value=("url", "html"))
def test_proper_grammer_with_one_video(
    mock_fetch_video_list_html: Mock, mock_parse_video_list_html: Mock, mock_print: Mock
) -> None:
    main()
    mock_print.assert_any_call("Found 1 video:")


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.parse_video_list_html",
    return_value=[video, second_video],
)
@patch("questdrive_syncer.app.fetch_video_list_html", return_value=("url", "html"))
def test_prints_each_video(
    mock_fetch_video_list_html: Mock, mock_parse_video_list_html: Mock, mock_print: Mock
) -> None:
    main()
    mock_print.assert_any_call(video)
    mock_print.assert_called_with(second_video)
