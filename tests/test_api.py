from datetime import datetime
from unittest.mock import Mock, mock_open, patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from questdrive_syncer.api import (
    MissingVideo,
    Video,
    download_and_delete_video,
    fetch_video_list_html,
    is_online,
    parse_video_list_html,
    update_actively_recording,
)


@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    return True


def test_normal(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response()
    assert is_online() is True


def test_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError(""))
    assert is_online() is False


def test_non_200(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404)
    assert is_online() is False


def test_fetch_video_list_html(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(text="html")
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


@patch(
    "questdrive_syncer.api.parse_video_list_html",
    return_value=[
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2345,
            "from_url",
        )
    ],
)
@patch("questdrive_syncer.api.fetch_video_list_html", return_value=("url", "html"))
def test_update_actively_recording_handles_unchanged(
    mock_fetch_video_list_html: Mock, mock_parse_video_list_html: Mock
) -> None:
    video = Video(
        "full%2Fpathtofile.mp4",
        "filename-20240101-111213.mp4",
        datetime(2024, 1, 1, 11, 12, 13),
        datetime(2024, 1, 1, 12, 13, 14),
        2345,
        "from_url",
    )
    update_actively_recording([video])
    assert video.actively_recording is False


@patch(
    "questdrive_syncer.api.parse_video_list_html",
    return_value=[
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 15),
            2345,
            "from_url",
        )
    ],
)
@patch("questdrive_syncer.api.fetch_video_list_html", return_value=("url", "html"))
def test_update_actively_recording_updates(
    mock_fetch_video_list_html: Mock, mock_parse_video_list_html: Mock
) -> None:
    video = Video(
        "full%2Fpathtofile.mp4",
        "filename-20240101-111213.mp4",
        datetime(2024, 1, 1, 11, 12, 13),
        datetime(2024, 1, 1, 12, 13, 14),
        2345,
        "from_url",
    )
    update_actively_recording([video])
    assert video.actively_recording is True


@patch(
    "questdrive_syncer.api.parse_video_list_html",
    return_value=[],
)
@patch("questdrive_syncer.api.fetch_video_list_html", return_value=("url", "html"))
def test_throws_if_video_missing(
    mock_fetch_video_list_html: Mock, mock_parse_video_list_html: Mock
) -> None:
    video = Video(
        "full%2Fpathtofile.mp4",
        "filename-20240101-111213.mp4",
        datetime(2024, 1, 1, 11, 12, 13),
        datetime(2024, 1, 1, 12, 13, 14),
        2345,
        "from_url",
    )
    with pytest.raises(MissingVideo) as exc_info:
        update_actively_recording([video])
    assert (
        exc_info.value.args[0]
        == 'Video "full%2Fpathtofile.mp4" no longer found in list'
    )


def test_video_string() -> None:
    assert (
        str(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            )
        )
        == "filename-20240101-111213.mp4 at 2345 MB - 2024-01-01 11:12:13 -> 2024-01-01 12:13:14"
    )


def test_video_string_includes_actively_recording() -> None:
    assert "(actively recording)" in str(
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2345,
            "from_url",
            True,
        )
    )


def test_download_and_delete_creates_output_if_missing(
    httpx_mock: HTTPXMock,
) -> None:
    with patch("os.utime"), patch("os.path.getsize", return_value=0), patch(
        "os.mkdir"
    ) as mock_mkdir, patch("os.path.exists", return_value=False) as mock_exists, patch(
        "builtins.open", mock_open()
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
            )
        )
        mock_exists.assert_called_once_with("output")
        mock_mkdir.assert_called_once_with("output")


def test_download_and_delete_requests_correct_url(
    httpx_mock: HTTPXMock,
) -> None:
    with patch("os.utime"), patch("os.path.getsize", return_value=0), patch(
        "os.mkdir"
    ), patch("os.path.exists", return_value=False), patch("builtins.open", mock_open()):
        httpx_mock.add_response()
        download_and_delete_video(
            Video(
                "full%2Fpathtofile.mp4",
                "filename-20240101-111213.mp4",
                datetime(2024, 1, 1, 11, 12, 13),
                datetime(2024, 1, 1, 12, 13, 14),
                2345,
                "from_url",
            )
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
    with patch("os.utime") as mock_utime, patch(
        "os.path.getsize", return_value=0
    ), patch("os.mkdir"), patch("os.path.exists", return_value=False), patch(
        "builtins.open", mock_open()
    ) as mocked_open:
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
            )
        )

        mocked_open.assert_called_once_with("output/filename-20240101-111213.mp4", "wb")
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
    with patch("os.utime"), patch("os.path.getsize", return_value=0), patch(
        "os.mkdir"
    ), patch("os.path.exists", return_value=False), patch("builtins.open", mock_open()):
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
            )
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
    with patch("os.utime"), patch("os.path.getsize", return_value=0), patch(
        "os.mkdir"
    ), patch("os.path.exists", return_value=False), patch(
        "builtins.open", mock_open()
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
                True,
            )
        )
        mock_print.assert_called_once_with(
            '"filename-20240101-111213.mp4" is actively recording, not deleting'
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_expecting_more_content(
    httpx_mock: HTTPXMock,
) -> None:
    with patch("os.utime"), patch("os.path.getsize", return_value=0), patch(
        "os.mkdir"
    ), patch("os.path.exists", return_value=False), patch(
        "builtins.open", mock_open()
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
            )
        )
        mock_print.assert_called_once_with(
            'Received 2 bytes less than expected during the download of "filename-20240101-111213.mp4"'
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_received_more_content_then_expected(
    httpx_mock: HTTPXMock,
) -> None:
    with patch("os.utime"), patch("os.path.getsize", return_value=0), patch(
        "os.mkdir"
    ), patch("os.path.exists", return_value=False), patch(
        "builtins.open", mock_open()
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
            )
        )
        mock_print.assert_called_once_with(
            'Received 2 bytes more than expected during the download of "filename-20240101-111213.mp4"'
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_wrote_less_then_received(
    httpx_mock: HTTPXMock,
) -> None:
    with patch("os.utime"), patch("os.path.getsize", return_value=7), patch(
        "os.mkdir"
    ), patch("os.path.exists", return_value=False), patch(
        "builtins.open", mock_open()
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
            )
        )
        mock_print.assert_called_once_with(
            'Wrote 2 bytes less than received during the download of "filename-20240101-111213.mp4"'
        )

        assert len(httpx_mock.get_requests()) == 1


def test_download_and_delete_doesnt_delete_if_wrote_more_then_received(
    httpx_mock: HTTPXMock,
) -> None:
    with patch("os.utime"), patch("os.path.getsize", return_value=3), patch(
        "os.mkdir"
    ), patch("os.path.exists", return_value=False), patch(
        "builtins.open", mock_open()
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
            )
        )
        mock_print.assert_called_once_with(
            'Wrote 2 bytes more than received during the download of "filename-20240101-111213.mp4"'
        )

        assert len(httpx_mock.get_requests()) == 1
