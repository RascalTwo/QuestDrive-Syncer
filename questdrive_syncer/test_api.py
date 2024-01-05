"""Tests for the API module."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import mock_open, patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from .api import (
    download_and_delete_video,
    fetch_video_list_html,
    is_online,
    update_actively_recording,
)
from .structures import MissingVideoError, Video


@pytest.fixture()
def assert_all_responses_were_requested() -> bool:
    """Assert that all responses were requested from the httpx mock."""
    return True


def test_normal(httpx_mock: HTTPXMock) -> None:
    """is_online() returns True when the server is online."""
    httpx_mock.add_response()
    assert is_online() is True


def test_error(httpx_mock: HTTPXMock) -> None:
    """is_online() returns False when the server is offline."""
    httpx_mock.add_exception(httpx.ConnectError(""))
    assert is_online() is False


def test_non_200(httpx_mock: HTTPXMock) -> None:
    """is_online() returns False when the server responds with a non-200 status code."""
    httpx_mock.add_response(status_code=404)
    assert is_online() is False


def test_fetch_video_list_html(httpx_mock: HTTPXMock) -> None:
    """fetch_video_list_html() returns the URL & HTML."""
    httpx_mock.add_response(text="html")
    assert fetch_video_list_html() == (
        "http://192.168.254.75:7123/list/storage/emulated/0/Oculus/VideoShots/",
        "html",
    )


def test_update_actively_recording_handles_unchanged() -> None:
    """update_actively_recording() leaves unchanged videos alone."""
    video = Video(
        "full%2Fpathtofile.mp4",
        "filename-20240101-111213.mp4",
        datetime(2024, 1, 1, 11, 12, 13),
        datetime(2024, 1, 1, 12, 13, 14),
        2345,
        "from_url",
    )
    update_actively_recording(
        [video],
        [video],
    )
    assert video.actively_recording is False


def test_update_actively_recording_updates() -> None:
    """update_actively_recording() updates changed videos."""
    video = Video(
        "full%2Fpathtofile.mp4",
        "filename-20240101-111213.mp4",
        datetime(2024, 1, 1, 11, 12, 13),
        datetime(2024, 1, 1, 12, 13, 14),
        2345,
        "from_url",
    )
    update_actively_recording(
        [video],
        [
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 15),
                2345,
                "from_url",
            ),
        ],
    )
    assert video.actively_recording is True


def test_update_actively_recording_throws_if_video_missing() -> None:
    """update_actively_recording() throws if a video is missing."""
    video = Video(
        "full%2Fpathtofile.mp4",
        "filename-20240101-111213.mp4",
        datetime(2024, 1, 1, 11, 12, 13),
        datetime(2024, 1, 1, 12, 13, 14),
        2345,
        "from_url",
    )
    with pytest.raises(MissingVideoError) as exc_info:
        update_actively_recording([video], [])
    assert exc_info.value.args[0] == 'Video "full%2Fpathtofile.mp4" is missing.'


def test_download_and_delete_creates_output_directory(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() creates the output directory."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=0),
    ), patch(
        "pathlib.Path.mkdir",
    ) as mock_mkdir, patch(
        "builtins.open",
        mock_open(),
    ):
        httpx_mock.add_response()
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_download_and_delete_requests_correct_url(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() calls the correct URL."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=0),
    ), patch(
        "pathlib.Path.mkdir",
    ), patch(
        "pathlib.Path.open",
        mock_open(),
    ):
        httpx_mock.add_response()
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )

        request = httpx_mock.get_requests()[0]
        assert request
        assert (
            str(request.url)
            == "http://192.168.254.75:7123/download/full%2Fpathtofile.mp4"
        )


def test_download_and_delete_writes_to_correct_path(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() writes to the correct path."""
    with patch("os.utime") as mock_utime, patch(
        "pathlib.Path.open",
        mock_open(),
    ) as mocked_open, patch(
        "pathlib.Path.mkdir",
    ), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=0),
    ):
        one_mb = b"0" * 1000000
        httpx_mock.add_response(content=one_mb)
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )

        mocked_open.assert_called_once_with("wb")
        file = mocked_open()
        file.write.assert_called_once_with(one_mb)
        mock_utime.assert_called_once_with(
            "output/filename-20240101-111213.mp4",
            (
                datetime(2024, 1, 1, 11, 12, 13).timestamp(),
                datetime(2024, 1, 1, 12, 13, 14).timestamp(),
            ),
        )


def test_download_and_delete_calls_delete_url(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() calls the correct URL when deleting."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=0),
    ), patch(
        "pathlib.Path.mkdir",
    ), patch(
        "pathlib.Path.open",
        mock_open(),
    ):
        httpx_mock.add_response()
        httpx_mock.add_response()
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )

        request = httpx_mock.get_requests()[1]
        assert request
        assert (
            str(request.url)
            == "http://192.168.254.75:7123/delete/full%2Fpathtofile.mp4"
        )


def test_download_and_delete_doesnt_delete_actively_recording(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() doesn't delete a video if it's actively recording."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=0),
    ), patch(
        "pathlib.Path.mkdir",
    ), patch(
        "builtins.open",
        mock_open(),
    ), patch("builtins.print") as mock_print:
        httpx_mock.add_response()
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
                actively_recording=True,
            ),
        )
        mock_print.assert_called_once_with(
            '"filename-20240101-111213.mp4" is actively recording, not deleting',
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_expecting_more_content(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() doesn't delete a video if it's expecting more content."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=0),
    ), patch(
        "pathlib.Path.mkdir",
    ), patch(
        "builtins.open",
        mock_open(),
    ), patch("builtins.print") as mock_print:
        httpx_mock.add_response(headers={"Content-Length": "5"}, content=b"123")
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )
        mock_print.assert_called_once_with(
            'Received 2 bytes less than expected during the download of "filename-20240101-111213.mp4"',
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_received_more_content_then_expected(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() doesn't delete a video if it received more content than expected."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=0),
    ), patch(
        "pathlib.Path.mkdir",
    ), patch(
        "builtins.open",
        mock_open(),
    ), patch("builtins.print") as mock_print:
        httpx_mock.add_response(headers={"Content-Length": "3"}, content=b"12345")
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )
        mock_print.assert_called_once_with(
            'Received 2 bytes more than expected during the download of "filename-20240101-111213.mp4"',
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_wrote_less_then_received(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() doesn't delete a video if it wrote less bytes than it received."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=7),
    ), patch(
        "pathlib.Path.mkdir",
    ), patch(
        "builtins.open",
        mock_open(),
    ), patch("builtins.print") as mock_print:
        httpx_mock.add_response(headers={"Content-Length": "5"}, content=b"12345")
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )
        mock_print.assert_called_once_with(
            'Wrote 2 bytes less than received during the download of "filename-20240101-111213.mp4"',
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_wrote_more_then_received(
    httpx_mock: HTTPXMock,
) -> None:
    """download_and_delete_video() doesn't delete a video if it wrote more bytes than it received."""
    with patch("os.utime"), patch(
        "pathlib.Path.stat",
        return_value=SimpleNamespace(st_mode=33204, st_size=3),
    ), patch(
        "pathlib.Path.mkdir",
    ), patch(
        "builtins.open",
        mock_open(),
    ), patch("builtins.print") as mock_print:
        httpx_mock.add_response(headers={"Content-Length": "5"}, content=b"12345")
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            ),
        )
        mock_print.assert_called_once_with(
            'Wrote 2 bytes more than received during the download of "filename-20240101-111213.mp4"',
        )

        assert len(httpx_mock.get_requests()) == 1
