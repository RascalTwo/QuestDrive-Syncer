import dataclasses
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from questdrive_syncer.api import Video
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


video = Video("filepath", "filename", datetime.now(), datetime.now(), 1.23, "url")
second_video = dataclasses.replace(video)
second_video.mb_size = 2.34


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.fetch_video_list_html",
    return_value=("url", "<tbody></tbody>"),
)
@patch("questdrive_syncer.app.update_actively_recording")
@patch("questdrive_syncer.app.is_online", return_value=True)
def test_print_when_successful(
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_print: Mock,
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
@patch("questdrive_syncer.app.update_actively_recording")
@patch("questdrive_syncer.app.is_online", return_value=True)
def test_calls_fetch_video_list_html_and_parse_video_list_html(
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
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
@patch("questdrive_syncer.app.update_actively_recording")
@patch("questdrive_syncer.app.is_online", return_value=True)
@patch("questdrive_syncer.app.download_and_delete_video")
def test_proper_grammer_with_one_video(
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    main()
    mock_print.assert_any_call("Found 1 video:")


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.parse_video_list_html",
    return_value=[video],
)
@patch("questdrive_syncer.app.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.app.update_actively_recording")
@patch("questdrive_syncer.app.is_online", return_value=True)
@patch("questdrive_syncer.app.download_and_delete_video")
def test_calls_update_actively_recording(
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    main()
    mock_update_actively_recording.assert_called()


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.parse_video_list_html",
    return_value=[video, second_video],
)
@patch("questdrive_syncer.app.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.app.update_actively_recording")
@patch("questdrive_syncer.app.is_online", return_value=True)
@patch("questdrive_syncer.app.download_and_delete_video")
def test_prints_and_downloads_each_video_from_smallest_to_largest(
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    main()
    mock_print.assert_any_call(video)
    mock_print.assert_called_with(second_video)
    mock_download_and_delete_video.assert_any_call(video)
    mock_download_and_delete_video.assert_called_with(second_video)


@patch("builtins.print")
@patch(
    "questdrive_syncer.app.parse_video_list_html",
    return_value=[video],
)
@patch("questdrive_syncer.app.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.app.update_actively_recording")
@patch("questdrive_syncer.app.is_online", return_value=True)
@patch("questdrive_syncer.app.download_and_delete_video", return_value=False)
@patch("questdrive_syncer.app.has_enough_free_space", return_value=False)
def test_doesnt_download_video_if_not_enough_space(
    mock_has_enough_free_space: Mock,
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    main()
    mock_print.assert_called_with(
        'Skipping download of "filename" because there is not enough free space'
    )
    mock_download_and_delete_video.assert_not_called()
