from questdrive_syncer.api import (
    is_online,
    fetch_video_list_html,
    parse_video_list_html,
    Video,
)
import httpx
from pytest_httpx import HTTPXMock
import pytest
from datetime import datetime


@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    return True


def test_normal(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200)
    assert is_online() is True


def test_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError(""))
    assert is_online() is False


def test_non_200(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404)
    assert is_online() is False


def test_fetch_video_list_html(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, text="html")
    assert fetch_video_list_html() == (
        "http://192.168.254.75:7123/list/storage/emulated/0/Oculus/VideoShots/",
        "html",
    )


html_expected_mappings = {
    "normal": [
        """
                <tr>
                    <td><a></a>&nbsp; filename-20240101-111213.mp4</td>
                    <td>01/01/2024 12:13:14</td>
                    <td>2.345 MB</td>
                    <td>
                        <a href='/download/full%2Fpathtofile.mp4'></a>
                    </td>
                </tr>
        """,
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2.345,
            "from_url",
        ),
    ],
    "gb": [
        """
                <tr>
                    <td><a></a>&nbsp; filename-20240101-111213.mp4</td>
                    <td>01/01/2024 12:13:14</td>
                    <td>2.345 GB</td>
                    <td>
                        <a href='/download/full%2Fpathtofile.mp4'></a>
                    </td>
                </tr>""",
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2345,
            "from_url",
        ),
    ],
}


@pytest.mark.parametrize(
    "html, expected",
    [
        [
            """
            <tbody>
                <tr></tr>
            </tbody>
        """,
            [],
        ],
        [
            f"""
            <tbody>
                <tr></tr>
                {html_expected_mappings["normal"][0]}
            </tbody>
        """,
            [html_expected_mappings["normal"][1]],
        ],
        [
            f"""
            <tbody>
                <tr></tr>
                {html_expected_mappings["normal"][0]}
                {html_expected_mappings["normal"][0]}
            </tbody>
        """,
            [
                html_expected_mappings["normal"][1],
                html_expected_mappings["normal"][1],
            ],
        ],
        [
            f"""
            <tbody>
                <tr></tr>
                {html_expected_mappings["gb"][0]}
            </tbody>
        """,
            [html_expected_mappings["gb"][1]],
        ],
    ],
)
def test_parse_video_list_html(
    html: str,
    expected: list[Video],
) -> None:
    assert (
        parse_video_list_html(
            "from_url",
            html,
        )
        == expected
    )
