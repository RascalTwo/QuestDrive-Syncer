"""Interactions with QuestDrive."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import httpx
import rich.progress

from .config import CONFIG
from .constants import (
    VIDEO_SHOTS_PATH,
)
from .helpers import has_enough_free_space
from .structures import MissingVideoError, Video


def is_online() -> bool:
    """Check if QuestDrive is online."""
    try:
        response = httpx.get(CONFIG.questdrive_url)
    except httpx.ConnectError:
        return False
    else:
        return response.status_code == httpx.codes.OK


def fetch_video_list_html() -> tuple[str, str]:
    """Fetch the URL and HTML of the video list."""
    url = CONFIG.questdrive_url + VIDEO_SHOTS_PATH
    response = httpx.get(url)
    return url, response.text


def update_actively_recording(videos: list[Video], latest_videos: list[Video]) -> None:
    """Update the actively_recording attribute of the videos if the modified_at has changed."""
    for video in videos:
        latest_video = next(
            (
                latest_video
                for latest_video in latest_videos
                if latest_video.filepath == video.filepath
            ),
            None,
        )

        if latest_video is None:
            raise MissingVideoError(video.filepath)

        if latest_video.modified_at != video.modified_at:
            video.actively_recording = True


def download_and_delete_videos(
    videos: list[Video],
    *,
    dry: bool = False,
    delete: bool = True,
    download: bool = True,
) -> None:
    """Download and delete the videos."""
    sizes = [video.mb_size * 1000**2 for video in videos]
    total_size = sum(sizes)
    with rich.progress.Progress(
        rich.progress.TextColumn(
            "[bold blue]{task.fields[filename]}",
            justify="right",
        ),
        "[progress.percentage]{task.percentage:>3.0f}%",
        rich.progress.BarColumn(bar_width=None),
        rich.progress.DownloadColumn(),
        rich.progress.TransferSpeedColumn(),
        rich.progress.TimeRemainingColumn(),
    ) as progress:
        tasks = [
            *(
                progress.add_task(
                    "Download",
                    total=video.mb_size * 1000**2,
                    filename=video.filename,
                )
                for video in videos
            ),
            progress.add_task(
                "Total",
                total=total_size,
                filename="Total",
            ),
        ]

        for i, video in enumerate(videos):
            if not has_enough_free_space(video.mb_size):
                print(
                    f'Skipping download of "{video.filename}" because there is not enough free space',
                )
                progress.update(tasks[i], advance=sizes[i])
                progress.update(tasks[-1], advance=sizes[i])
                continue

            for value in download_and_delete_video(
                video,
                dry=dry,
                delete=delete,
                download=download,
            ):
                if isinstance(value, float):
                    progress.update(tasks[i], total=value)
                    sizes[i] = value
                    total_size = sum(sizes)
                    progress.update(tasks[-1], total=total_size)
                elif isinstance(value, int):
                    progress.update(tasks[i], advance=value)
                    progress.update(tasks[-1], advance=value)
                else:
                    print(value)


def download_and_delete_video(
    video: Video,
    *,
    dry: bool = False,
    delete: bool = True,
    download: bool = True,
) -> Iterator[float | int | str]:
    """Download and delete the video."""
    url = CONFIG.questdrive_url + "download/" + video.filepath

    head_response = httpx.head(url)
    expected_byte_count = int(head_response.headers.get("Content-Length", 0))
    downloaded_byte_count = expected_byte_count
    if download and not dry:
        with httpx.stream("GET", url) as response, Path(
            f"{CONFIG.output_path}{video.filename}",
        ).open("wb") as file:
            expected_byte_count = int(response.headers.get("Content-Length", 0))
            yield float(expected_byte_count)

            downloaded_byte_count = 0
            for chunk in response.iter_bytes():
                file.write(chunk)
                chunk_length = len(chunk)
                downloaded_byte_count += chunk_length
                yield chunk_length

        os.utime(
            f"{CONFIG.output_path}{video.filename}",
            (video.created_at.timestamp(), video.modified_at.timestamp()),
        )

    if video.actively_recording:
        yield f'"{video.filename}" is actively recording, not deleting'
        return

    content_length_diff = downloaded_byte_count - expected_byte_count
    if content_length_diff:
        if content_length_diff > 0:
            yield f'Received {content_length_diff} bytes more than expected during the download of "{video.filename}"'

        else:
            yield f'Received {-content_length_diff} bytes less than expected during the download of "{video.filename}"'

        return

    written_length = downloaded_byte_count
    if not dry:
        written_length = Path(f"{CONFIG.output_path}{video.filename}").stat().st_size

    written_length_diff = downloaded_byte_count - written_length
    if written_length_diff:
        if written_length_diff > 0:
            yield f'Wrote {written_length_diff} bytes more than received during the download of "{video.filename}"'

        else:
            yield f'Wrote {-written_length_diff} bytes less than received during the download of "{video.filename}"'

        return

    if delete and not dry:
        httpx.get(CONFIG.questdrive_url + "delete/" + video.filepath)
