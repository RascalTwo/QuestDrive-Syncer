"""Tests for the API module."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import httpx
import pytest

from questdrive_syncer.api import (
    fetch_homepage_html,
    fetch_video_list_html,
    is_online,
    update_actively_recording,
)
from questdrive_syncer.structures import MissingVideoError, Video

if TYPE_CHECKING:  # pragma: no cover
    from pytest_httpx import HTTPXMock


@pytest.fixture()
def assert_all_responses_were_requested() -> bool:
    """Assert that all responses were requested from the httpx mock."""
    return True


class TestIsOnline:
    """Tests for the is_online() function."""

    @staticmethod
    def test_normal(httpx_mock: HTTPXMock) -> None:
        """Returns True when the server is online."""
        httpx_mock.add_response()
        assert is_online() is True

    @staticmethod
    def test_error(httpx_mock: HTTPXMock) -> None:
        """Returns False when the server is offline."""
        httpx_mock.add_exception(httpx.ConnectError(""))
        assert is_online() is False

    @staticmethod
    def test_non_200(httpx_mock: HTTPXMock) -> None:
        """Returns False when the server responds with a non-200 status code."""
        httpx_mock.add_response(status_code=404)
        assert is_online() is False


class TestUpdateActivelyRecording:
    """Tests for the update_actively_recording() function."""

    @staticmethod
    def test_handles_unchanged() -> None:
        """Leaves unchanged videos alone."""
        video = Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2345,
        )
        update_actively_recording(
            [video],
            [video],
        )
        assert video.actively_recording is False

    @staticmethod
    def test_updates() -> None:
        """Updates changed videos."""
        video = Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2345,
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
                ),
            ],
        )
        assert video.actively_recording is True

    @staticmethod
    def test_throws_if_video_missing() -> None:
        """Throws if a video is missing."""
        video = Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2345,
        )
        with pytest.raises(MissingVideoError) as exc_info:
            update_actively_recording([video], [])
        assert exc_info.value.args[0] == 'Video "full%2Fpathtofile.mp4" is missing.'


def test_fetch_video_list_html(httpx_mock: HTTPXMock) -> None:
    """fetch_video_list_html() returns the URL & HTML."""
    httpx_mock.add_response(text="html")

    assert fetch_video_list_html() == "html"


def test_fetch_homepage_html(httpx_mock: HTTPXMock) -> None:
    """fetch_homepage_html() calls the correct URL & returns the HTML."""
    httpx_mock.add_response(text="html")

    assert fetch_homepage_html() == "html"

    assert httpx_mock.get_requests()[0].url == "https://example.com/"
