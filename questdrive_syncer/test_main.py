"""Test the main function."""
import dataclasses
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from .constants import FAILURE_EXIT_CODE
from .main import main
from .structures import Video


@patch("questdrive_syncer.main.is_online", return_value=False)
@patch("builtins.print")
@patch("time.sleep")
def test_message_if_not_online(
    mock_sleep: Mock,
    mock_print: Mock,
    mock_is_online: Mock,
) -> None:
    """main() prints a message if QuestDrive is not online."""
    with pytest.raises(SystemExit):
        main()
    mock_print.assert_called_once_with(
        'QuestDrive not found at "http://192.168.254.75:7123/"',
    )


@patch("questdrive_syncer.main.is_online", return_value=False)
@patch("time.sleep")
def test_failed_status_code(mock_sleep: Mock, mock_is_online: Mock) -> None:
    """main() exits with status code 3 if QuestDrive is not online."""
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == FAILURE_EXIT_CODE


video = Video("filepath", "filename", datetime.now(), datetime.now(), 1.23, "url")
second_video = dataclasses.replace(video)
second_video.mb_size = 2.34


@patch("builtins.print")
@patch(
    "questdrive_syncer.main.fetch_video_list_html",
    return_value=("url", "<tbody></tbody>"),
)
@patch("questdrive_syncer.main.update_actively_recording")
@patch("questdrive_syncer.main.is_online", return_value=True)
@patch("time.sleep")
def test_print_when_successful(
    mock_sleep: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    """main() prints when successful."""
    main()
    mock_print.assert_any_call(
        "QuestDrive found running at http://192.168.254.75:7123/",
    )


@patch("builtins.print")
@patch(
    "questdrive_syncer.main.parse_video_list_html",
    return_value=[],
)
@patch("questdrive_syncer.main.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.main.update_actively_recording")
@patch("questdrive_syncer.main.is_online", return_value=True)
@patch("time.sleep")
def test_calls_fetch_video_list_html_and_parse_video_list_html(
    mock_sleep: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    """main() calls fetch_video_list_html and parse_video_list_html twice."""
    main()
    assert mock_fetch_video_list_html.call_count == 2  # noqa: PLR2004
    mock_parse_video_list_html.assert_called_with("url", "html")


@patch("builtins.print")
@patch(
    "questdrive_syncer.main.parse_video_list_html",
    return_value=[video],
)
@patch("questdrive_syncer.main.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.main.update_actively_recording")
@patch("questdrive_syncer.main.is_online", return_value=True)
@patch("questdrive_syncer.main.download_and_delete_video")
@patch("time.sleep")
def test_proper_grammar_with_one_video(
    mock_sleep: Mock,
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    """main() prints "video" if there is only one video."""
    main()
    mock_print.assert_any_call("Found 1 video:")


@patch("builtins.print")
@patch(
    "questdrive_syncer.main.parse_video_list_html",
    return_value=[video],
)
@patch("questdrive_syncer.main.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.main.update_actively_recording")
@patch("questdrive_syncer.main.is_online", return_value=True)
@patch("questdrive_syncer.main.download_and_delete_video")
@patch("time.sleep")
def test_calls_update_actively_recording(
    mock_sleep: Mock,
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    """main() calls update_actively_recording with both video lists."""
    main()
    mock_update_actively_recording.assert_called_with([video], [video])


@patch("builtins.print")
@patch(
    "questdrive_syncer.main.parse_video_list_html",
    return_value=[video, second_video],
)
@patch("questdrive_syncer.main.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.main.update_actively_recording")
@patch("questdrive_syncer.main.is_online", return_value=True)
@patch("questdrive_syncer.main.download_and_delete_video")
@patch("time.sleep")
def test_prints_and_downloads_each_video_from_smallest_to_largest(
    mock_sleep: Mock,
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    """main() prints and downloads each video from smallest to largest."""
    main()
    mock_print.assert_any_call(video)
    mock_print.assert_called_with(second_video)
    mock_download_and_delete_video.assert_any_call(video)
    mock_download_and_delete_video.assert_called_with(second_video)


@patch("builtins.print")
@patch(
    "questdrive_syncer.main.parse_video_list_html",
    return_value=[video],
)
@patch("questdrive_syncer.main.fetch_video_list_html", return_value=("url", "html"))
@patch("questdrive_syncer.main.update_actively_recording")
@patch("questdrive_syncer.main.is_online", return_value=True)
@patch("questdrive_syncer.main.download_and_delete_video", return_value=False)
@patch("questdrive_syncer.main.has_enough_free_space", return_value=False)
@patch("time.sleep")
def test_doesnt_download_video_if_not_enough_space(
    mock_sleep: Mock,
    mock_has_enough_free_space: Mock,
    mock_download_and_delete_video: Mock,
    mock_is_online: Mock,
    mock_update_actively_recording: Mock,
    mock_fetch_video_list_html: Mock,
    mock_parse_video_list_html: Mock,
    mock_print: Mock,
) -> None:
    """main() doesn't download a video if there is not enough space."""
    main()
    mock_print.assert_called_with(
        'Skipping download of "filename" because there is not enough free space',
    )
    mock_download_and_delete_video.assert_not_called()
