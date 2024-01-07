"""Tests for the API module."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import httpx
import pytest

from .api import (
    fetch_homepage_html,
    fetch_video_list_html,
    is_online,
    update_actively_recording,
)
from .structures import MissingVideoError, Video

if TYPE_CHECKING:  # pragma: no cover
    from pytest_httpx import HTTPXMock


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
        "https://example.com/list/storage/emulated/0/Oculus/VideoShots/",
        "html",
    )


def test_fetch_homepage_html(httpx_mock: HTTPXMock) -> None:
    """fetch_homepage_html() calls the correct URL & returns the HTML."""
    httpx_mock.add_response(text="html")

    assert fetch_homepage_html() == "html"

    assert httpx_mock.get_requests()[0].url == "https://example.com/"


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
