"""Test the main function."""
from __future__ import annotations

import dataclasses
import sys
from datetime import datetime
from operator import itemgetter
from typing import TYPE_CHECKING, Any

import pytest

from .constants import ACTIVELY_RECORDING_EXIT_CODE, FAILURE_EXIT_CODE
from .main import main
from .structures import Video

if TYPE_CHECKING:  # pragma: no cover
    from pytest_mock import MockerFixture


def make_main_mocks(
    mocker: MockerFixture,
    *desired: str,
    is_online: bool | list[bool] = True,
    fetch_video_list_html: tuple[str, str] = ("url", "html"),
    parse_video_list_html: None | list[Video] = None,
    has_enough_free_space: bool = True,
    args: tuple[str, ...] = (),
) -> Any:  # noqa: ANN401
    """Create mocks for main()."""
    sys.argv = ["", "--questdrive-url=url", *args]
    mock_print = mocker.patch("builtins.print")
    mock_is_online = mocker.patch(
        "questdrive_syncer.main.is_online",
        side_effect=is_online if isinstance(is_online, list) else [is_online],
    )
    mock_sleep = mocker.patch("time.sleep")
    mock_fetch_video_list_html = mocker.patch(
        "questdrive_syncer.main.fetch_video_list_html",
        return_value=fetch_video_list_html,
    )
    mock_parse_video_list_html = mocker.patch(
        "questdrive_syncer.main.parse_video_list_html",
        return_value=parse_video_list_html or [],
    )
    mock_update_actively_recording = mocker.patch(
        "questdrive_syncer.main.update_actively_recording",
    )
    mock_has_enough_free_space = mocker.patch(
        "questdrive_syncer.main.has_enough_free_space",
        return_value=has_enough_free_space,
    )

    mock_download_and_delete_video = mocker.patch(
        "questdrive_syncer.main.download_and_delete_video",
    )

    if not desired:
        return None

    return itemgetter(*desired)(
        {
            "mock_is_online": mock_is_online,
            "mock_sleep": mock_sleep,
            "mock_print": mock_print,
            "mock_fetch_video_list_html": mock_fetch_video_list_html,
            "mock_parse_video_list_html": mock_parse_video_list_html,
            "mock_update_actively_recording": mock_update_actively_recording,
            "mock_has_enough_free_space": mock_has_enough_free_space,
            "mock_download_and_delete_video": mock_download_and_delete_video,
        },
    )


def test_prints_when_in_dry_mode(mocker: MockerFixture) -> None:
    """main() prints when in dry mode."""
    mock_print = make_main_mocks(mocker, "mock_print", args=("--dry",))

    main()

    mock_print.assert_any_call("Dry run enabled, no actions will be performed.")


def test_message_if_not_online(mocker: MockerFixture) -> None:
    """main() prints a message if QuestDrive is not online."""
    mock_print = make_main_mocks(mocker, "mock_print", is_online=False)

    with pytest.raises(SystemExit):
        main()

    mock_print.assert_called_once_with(
        'QuestDrive not found at "url/"',
    )


def test_failed_status_code(mocker: MockerFixture) -> None:
    """main() exits with status code 3 if QuestDrive is not online."""
    make_main_mocks(mocker, is_online=False)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == FAILURE_EXIT_CODE


def test_waits_for_questdrive_if_wait_for_questdrive(mocker: MockerFixture) -> None:
    """main() waits for QuestDrive if wait_for_questdrive is True."""
    mock_is_online, mock_print, mock_sleep = make_main_mocks(
        mocker,
        "mock_is_online",
        "mock_print",
        "mock_sleep",
        is_online=[False, True],
        args=("--wait-for-questdrive",),
    )

    main()

    mock_print.assert_any_call(
        'Waiting for QuestDrive at "url/"...',
    )
    assert mock_is_online.call_count == 2  # noqa: PLR2004
    mock_sleep.assert_any_call(5 * 60)


video = Video("filepath", "filename", datetime.now(), datetime.now(), 1.23, "url")
second_video = dataclasses.replace(video)
second_video.mb_size = 2.34


def test_print_when_successful(mocker: MockerFixture) -> None:
    """main() prints when successful."""
    mock_print = make_main_mocks(mocker, "mock_print")

    main()

    mock_print.assert_any_call(
        'QuestDrive found running at "url/"',
    )


def test_calls_fetch_video_list_html_and_parse_video_list_html(
    mocker: MockerFixture,
) -> None:
    """main() calls fetch_video_list_html and parse_video_list_html twice."""
    mock_fetch_video_list_html, mock_parse_video_list_html = make_main_mocks(
        mocker,
        "mock_fetch_video_list_html",
        "mock_parse_video_list_html",
    )

    main()

    assert mock_fetch_video_list_html.call_count == 2  # noqa: PLR2004
    mock_parse_video_list_html.assert_called_with("url", "html")


def test_proper_grammar_with_one_video(mocker: MockerFixture) -> None:
    """main() prints "video" if there is only one video."""
    mock_print = make_main_mocks(mocker, "mock_print", parse_video_list_html=[video])

    main()

    mock_print.assert_any_call("Found 1 video:")


def test_calls_update_actively_recording(mocker: MockerFixture) -> None:
    """main() calls update_actively_recording with both video lists."""
    mock_update_actively_recording = make_main_mocks(
        mocker,
        "mock_update_actively_recording",
        parse_video_list_html=[video],
    )

    main()

    mock_update_actively_recording.assert_called_with([video], [video])


def test_dont_continue_if_actively_recording_and_configured(
    mocker: MockerFixture,
) -> None:
    """main() doesn't continue if the Quest is actively recording when the configuration is set accordingly."""
    active_video = dataclasses.replace(video)
    active_video.actively_recording = True
    mock_print, mock_has_enough_free_space = make_main_mocks(
        mocker,
        "mock_print",
        "mock_has_enough_free_space",
        parse_video_list_html=[active_video],
        args=("--dont-run-while-actively-recording",),
    )

    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == ACTIVELY_RECORDING_EXIT_CODE
    mock_print.assert_called_with(
        "Quest is actively recording, exiting.",
    )
    mock_has_enough_free_space.assert_not_called()


def test_prints_and_downloads_each_video_from_smallest_to_largest(
    mocker: MockerFixture,
) -> None:
    """main() prints and downloads each video from smallest to largest."""
    mock_print, mock_download_and_delete_video = make_main_mocks(
        mocker,
        "mock_print",
        "mock_download_and_delete_video",
        parse_video_list_html=[video, second_video],
    )

    main()

    mock_print.assert_any_call(video)
    mock_print.assert_called_with(second_video)
    mock_download_and_delete_video.assert_any_call(
        video,
        dry=False,
        delete=True,
        download=True,
    )
    mock_download_and_delete_video.assert_called_with(
        second_video,
        dry=False,
        delete=True,
        download=True,
    )


def test_doesnt_call_download_video_if_not_enough_space(mocker: MockerFixture) -> None:
    """main() doesn't call for the downloading & deleting of a video if there is not enough space."""
    (
        mock_print,
        mock_has_enough_free_space,
        mock_download_and_delete_video,
    ) = make_main_mocks(
        mocker,
        "mock_print",
        "mock_has_enough_free_space",
        "mock_download_and_delete_video",
        parse_video_list_html=[video],
        has_enough_free_space=False,
    )

    main()

    mock_print.assert_called_with(
        'Skipping download of "filename" because there is not enough free space',
    )

    mock_download_and_delete_video.assert_not_called()
