"""Tests for the download module."""
from __future__ import annotations

from datetime import datetime
from operator import itemgetter
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, ClassVar
from unittest.mock import mock_open

import pytest

from questdrive_syncer.download import (
    download_and_delete_video,
    download_and_delete_videos,
)
from questdrive_syncer.structures import Video

if TYPE_CHECKING:  # pragma: no cover
    from pytest_httpx import HTTPXMock
    from pytest_mock import MockerFixture


@pytest.fixture()
def assert_all_responses_were_requested() -> bool:
    """Assert that all responses were requested from the httpx mock."""
    return True


class TestDownloadAndDeleteVideo:
    """Tests for the download_and_delete_video() function."""

    @staticmethod
    def make_download_and_delete_video_mocks(
        mocker: MockerFixture,
        *desired: str,
        st_size: int = 0,
    ) -> Any:  # noqa: ANN401
        """Create mocks for download_and_delete_video()."""
        mocked_open = mocker.patch("pathlib.Path.open", mock_open())
        mock_stat = mocker.patch(
            "pathlib.Path.stat",
            return_value=SimpleNamespace(st_mode=33204, st_size=st_size),
        )
        mock_utime = mocker.patch("os.utime")
        if not desired:
            return None

        return itemgetter(*desired)(
            {
                "mocked_open": mocked_open,
                "mock_stat": mock_stat,
                "mock_utime": mock_utime,
            },
        )

    @staticmethod
    def test_requests_correct_url(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Calls the correct URL."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(mocker)
        httpx_mock.add_response()
        httpx_mock.add_response()

        list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        )

        request = httpx_mock.get_requests()[1]
        assert request
        assert str(request.url) == "https://example.com/download/full%2Fpathtofile.mp4"

    @staticmethod
    def test_writes_to_correct_path(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Writes to the correct path."""
        one_mb = b"0" * 1000000
        (
            mocked_open,
            mock_utime,
        ) = TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(
            mocker,
            "mocked_open",
            "mock_utime",
        )
        httpx_mock.add_response()
        httpx_mock.add_response(content=one_mb)

        list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        )

        mocked_open.assert_called_once_with("wb")
        file = mocked_open()
        file.write.assert_called_once_with(one_mb)
        mock_utime.assert_called_once_with(
            Path("output/filename-20240101-111213.mp4"),
            (
                datetime(2024, 1, 1, 11, 12, 13).timestamp(),
                datetime(2024, 1, 1, 12, 13, 14).timestamp(),
            ),
        )

    @staticmethod
    def test_calls_stat_on_written_file(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Calls stat() on the written file."""
        mock_stat = TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(
            mocker,
            "mock_stat",
        )
        httpx_mock.add_response()
        httpx_mock.add_response()

        list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        )

        # each httpx call additionally calls stat(), so 3 httpx calls + 1 my call
        assert mock_stat.call_count == 4  # noqa: PLR2004

    @staticmethod
    def test_calls_delete_url(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Calls the correct URL when deleting."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(mocker)
        httpx_mock.add_response()
        httpx_mock.add_response()
        httpx_mock.add_response()

        list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        )

        request = httpx_mock.get_requests()[2]
        assert request
        assert str(request.url) == "https://example.com/delete/full%2Fpathtofile.mp4"

    @staticmethod
    def test_does_not_delete_actively_recording(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Doesn't delete a video if it's actively recording."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(mocker)
        httpx_mock.add_response()
        httpx_mock.add_response()

        assert list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                    actively_recording=True,
                ),
            ),
        ) == [0.0, '"filename-20240101-111213.mp4" is actively recording, not deleting']
        assert len(httpx_mock.get_requests()) == 2  # noqa: PLR2004

    @staticmethod
    def test_does_not_delete_if_expecting_more_content(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Doesn't delete a video if it's expecting more content."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(mocker)
        httpx_mock.add_response()
        httpx_mock.add_response(headers={"Content-Length": "5"}, content=b"123")

        assert list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        ) == [
            5.0,
            3,
            'Received 2 bytes less than expected during the download of "filename-20240101-111213.mp4"',
        ]
        assert len(httpx_mock.get_requests()) == 2  # noqa: PLR2004

    @staticmethod
    def test_does_not_delete_if_received_more_content_then_expected(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Doesn't delete a video if it received more content than expected."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(mocker)
        httpx_mock.add_response()
        httpx_mock.add_response(headers={"Content-Length": "3"}, content=b"12345")

        assert list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        ) == [
            3.0,
            5,
            'Received 2 bytes more than expected during the download of "filename-20240101-111213.mp4"',
        ]
        assert len(httpx_mock.get_requests()) == 2  # noqa: PLR2004

    @staticmethod
    def test_does_not_delete_if_wrote_less_then_received(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Doesn't delete a video if it wrote less bytes than it received."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(
            mocker,
            st_size=7,
        )
        httpx_mock.add_response()
        httpx_mock.add_response(headers={"Content-Length": "5"}, content=b"12345")

        assert list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        ) == [
            5.0,
            5,
            'Wrote 2 bytes less than received during the download of "filename-20240101-111213.mp4"',
        ]
        assert len(httpx_mock.get_requests()) == 2  # noqa: PLR2004

    @staticmethod
    def test_does_not_delete_if_wrote_more_then_received(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Doesn't delete a video if it wrote more bytes than it received."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(
            mocker,
            st_size=3,
        )
        httpx_mock.add_response()
        httpx_mock.add_response(headers={"Content-Length": "5"}, content=b"12345")

        assert list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime(2024, 1, 1, 11, 12, 13),
                    datetime(2024, 1, 1, 12, 13, 14),
                    2345,
                ),
            ),
        ) == [
            5.0,
            5,
            'Wrote 2 bytes more than received during the download of "filename-20240101-111213.mp4"',
        ]
        assert len(httpx_mock.get_requests()) == 2  # noqa: PLR2004

    @staticmethod
    def test_does_not_delete_if_delete_is_false(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Doesn't delete a video if delete is False."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(mocker)
        httpx_mock.add_response()
        httpx_mock.add_response()

        list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime.now(),
                    datetime.now(),
                    2345,
                ),
                delete=False,
            ),
        )

        assert len(httpx_mock.get_requests()) == 2  # noqa: PLR2004

    @staticmethod
    def test_does_not_download_if_download_is_false(
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ) -> None:
        """Doesn't download a video if download is False."""
        TestDownloadAndDeleteVideo.make_download_and_delete_video_mocks(mocker)
        httpx_mock.add_response()
        httpx_mock.add_response()

        list(
            download_and_delete_video(
                Video(
                    "full%2Fpathtofile.mp4",
                    "filename-20240101-111213.mp4",
                    datetime.now(),
                    datetime.now(),
                    2345,
                ),
                download=False,
            ),
        )

        assert len(httpx_mock.get_requests()) == 2  # noqa: PLR2004


class TestDownloadAndDeleteVideos:
    """Tests for the download_and_delete_videos() function."""

    videos: ClassVar[list[Video]] = [
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime.now(),
            datetime.now(),
            100,
        ),
        Video(
            "full%2Fpathtofile2.mp4",
            "filename-20240101-111214.mp4",
            datetime.now(),
            datetime.now(),
            200,
        ),
    ]

    @staticmethod
    def make_download_and_delete_videos_mocks(
        mocker: MockerFixture,
        video_count: int,
        *desired: str,
        has_enough_free_space: bool = True,
        download_and_delete_video: None | list[list[float | int | str]] = None,
    ) -> Any:  # noqa: ANN401
        """Create mocks for download_and_delete_videos()."""
        tasks = [
            *(SimpleNamespace() for _ in range(video_count)),
            SimpleNamespace(),
        ]
        mock_add_task = mocker.Mock(side_effect=tasks)
        mock_update = mocker.Mock()
        mock_progress = mocker.patch("rich.progress.Progress")
        mock_progress.return_value.__enter__.return_value = SimpleNamespace(
            add_task=mock_add_task,
            update=mock_update,
        )
        mocker.patch(
            "questdrive_syncer.download.has_enough_free_space",
            return_value=has_enough_free_space,
        )
        mock_print = mocker.patch("builtins.print")
        mock_download_and_delete_video = mocker.patch(
            "questdrive_syncer.download.download_and_delete_video",
            side_effect=download_and_delete_video or [[] for _ in range(video_count)],
        )

        return itemgetter(*desired)(
            {
                "tasks": tasks,
                "mock_add_task": mock_add_task,
                "mock_update": mock_update,
                "mock_print": mock_print,
                "mock_progress": mock_progress,
                "mock_download_and_delete_video": mock_download_and_delete_video,
            },
        )

    @staticmethod
    def test_simple_output(mocker: MockerFixture) -> None:
        """Prints simple output if simple_output is True."""
        (
            mock_print,
            mock_download_and_delete_video,
        ) = TestDownloadAndDeleteVideos.make_download_and_delete_videos_mocks(
            mocker,
            len(TestDownloadAndDeleteVideos.videos),
            "mock_print",
            "mock_download_and_delete_video",
            has_enough_free_space=True,
            download_and_delete_video=[["bad thing happened"], [90000000, 110000000]],
        )

        download_and_delete_videos(
            TestDownloadAndDeleteVideos.videos,
            simple_output=True,
        )

        for video in TestDownloadAndDeleteVideos.videos:
            mock_print.assert_any_call("Starting", video, "...")
            mock_download_and_delete_video.assert_any_call(
                video,
                delete=True,
                download=True,
            )
            mock_print.assert_any_call("Finished", video)

        mock_print.assert_any_call("bad thing happened")

    @staticmethod
    def test_creates_initial_tasks(
        mocker: MockerFixture,
    ) -> None:
        """Creates initial tasks with correct size & filenames."""
        (
            mock_progress,
            mock_add_task,
        ) = TestDownloadAndDeleteVideos.make_download_and_delete_videos_mocks(
            mocker,
            len(TestDownloadAndDeleteVideos.videos),
            "mock_progress",
            "mock_add_task",
            has_enough_free_space=True,
        )

        download_and_delete_videos(TestDownloadAndDeleteVideos.videos)

        assert mock_progress.call_count == 1
        mock_add_task.assert_any_call(
            "Download",
            total=100000000,
            filename="filename-20240101-111213.mp4",
        )
        mock_add_task.assert_any_call(
            "Download",
            total=200000000,
            filename="filename-20240101-111214.mp4",
        )
        mock_add_task.assert_called_with("Total", total=300000000, filename="Total")

    @staticmethod
    def test_does_not_download_if_not_enough_free_space(
        mocker: MockerFixture,
    ) -> None:
        """Doesn't download if there is not enough free space."""
        (
            mock_print,
            mock_download_and_delete_video,
        ) = TestDownloadAndDeleteVideos.make_download_and_delete_videos_mocks(
            mocker,
            len(TestDownloadAndDeleteVideos.videos),
            "mock_print",
            "mock_download_and_delete_video",
            has_enough_free_space=False,
        )

        download_and_delete_videos(TestDownloadAndDeleteVideos.videos)

        mock_print.assert_any_call(
            'Skipping download of "filename-20240101-111213.mp4" because there is not enough free space',
        )
        mock_print.assert_any_call(
            'Skipping download of "filename-20240101-111214.mp4" because there is not enough free space',
        )
        mock_download_and_delete_video.assert_not_called()

    @staticmethod
    def test_progresses_when_not_downloading(
        mocker: MockerFixture,
    ) -> None:
        """Progresses when not downloading."""
        (
            mock_update,
            tasks,
        ) = TestDownloadAndDeleteVideos.make_download_and_delete_videos_mocks(
            mocker,
            len(TestDownloadAndDeleteVideos.videos),
            "mock_update",
            "tasks",
            has_enough_free_space=False,
        )

        download_and_delete_videos(TestDownloadAndDeleteVideos.videos)

        mock_update.assert_any_call(tasks[0], advance=100000000)
        mock_update.assert_any_call(tasks[1], advance=200000000)
        mock_update.assert_any_call(tasks[2], advance=100000000)
        mock_update.assert_any_call(tasks[2], advance=200000000)

    @staticmethod
    def test_updates_total_with_float(
        mocker: MockerFixture,
    ) -> None:
        """Updates total with floats returned from download_and_delete_video()."""
        (
            mock_update,
            tasks,
        ) = TestDownloadAndDeleteVideos.make_download_and_delete_videos_mocks(
            mocker,
            len(TestDownloadAndDeleteVideos.videos),
            "mock_update",
            "tasks",
            download_and_delete_video=[[110000000.0], [220000000.0]],
        )

        download_and_delete_videos(TestDownloadAndDeleteVideos.videos)

        mock_update.assert_any_call(tasks[0], total=110000000)
        mock_update.assert_any_call(tasks[2], total=310000000)
        mock_update.assert_any_call(tasks[1], total=220000000)
        mock_update.assert_any_call(tasks[2], total=330000000)

    @staticmethod
    def test_advanced_by_ints(
        mocker: MockerFixture,
    ) -> None:
        """Advances by ints returned from download_and_delete_video()."""
        (
            mock_update,
            tasks,
        ) = TestDownloadAndDeleteVideos.make_download_and_delete_videos_mocks(
            mocker,
            len(TestDownloadAndDeleteVideos.videos),
            "mock_update",
            "tasks",
            download_and_delete_video=[[100000000], [90000000, 110000000]],
        )

        download_and_delete_videos(TestDownloadAndDeleteVideos.videos)

        mock_update.assert_any_call(tasks[0], advance=100000000)
        mock_update.assert_any_call(tasks[2], advance=100000000)
        mock_update.assert_any_call(tasks[1], advance=90000000)
        mock_update.assert_any_call(tasks[2], advance=90000000)
        mock_update.assert_any_call(tasks[1], advance=110000000)
        mock_update.assert_any_call(tasks[2], advance=110000000)

    @staticmethod
    def test_prints_strs(
        mocker: MockerFixture,
    ) -> None:
        """Prints strs returned from download_and_delete_video()."""
        (
            mock_print,
            mock_update,
            tasks,
        ) = TestDownloadAndDeleteVideos.make_download_and_delete_videos_mocks(
            mocker,
            len(TestDownloadAndDeleteVideos.videos),
            "mock_print",
            "mock_update",
            "tasks",
            download_and_delete_video=[
                ["bad thing happened"],
                [90000000, 110000000],
            ],
        )

        download_and_delete_videos(TestDownloadAndDeleteVideos.videos)

        mock_print.assert_any_call("bad thing happened")
        mock_update.assert_any_call(tasks[1], advance=90000000)
        mock_update.assert_any_call(tasks[2], advance=90000000)
        mock_update.assert_any_call(tasks[1], advance=110000000)
        mock_update.assert_any_call(tasks[2], advance=110000000)
