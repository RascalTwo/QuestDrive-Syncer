from datetime import datetime

from .structures import Video


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
