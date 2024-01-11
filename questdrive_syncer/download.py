"""Download and delete videos from QuestDrive."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

import httpx
import rich.progress

from questdrive_syncer.config import CONFIG
from questdrive_syncer.helpers import has_enough_free_space

if TYPE_CHECKING:  # pragma: no cover
    from questdrive_syncer.structures import Video


def download_and_delete_videos(
    videos: list[Video],
    *,
    simple_output: bool = False,
    delete: bool = True,
    download: bool = True,
) -> None:
    """Download and delete the videos."""
    if simple_output:
        for video in videos:
            print("Starting", video, "...")
            for value in download_and_delete_video(
                video,
                delete=delete,
                download=download,
            ):
                if isinstance(value, str):
                    print(value)
            print("Finished", video)
        return

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
    delete: bool = True,
    download: bool = True,
) -> Iterator[float | int | str]:
    """Download and delete the video."""
    download_url = httpx.URL(CONFIG.questdrive_url).join(
        str(Path("download") / video.filepath),
    )
    video_output_filepath = Path(CONFIG.output_path) / video.filename

    head_response = httpx.head(download_url)
    expected_byte_count = int(head_response.headers.get("Content-Length", 0))
    downloaded_byte_count = expected_byte_count
    if download:
        with httpx.stream("GET", download_url) as response, Path(
            video_output_filepath,
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
            video_output_filepath,
            (video.created_at.timestamp(), video.modified_at.timestamp()),
        )

    if video.actively_recording:
        yield f'"{video.filename}" is actively recording, not deleting'
        return

    if content_length_diff := downloaded_byte_count - expected_byte_count:
        if content_length_diff > 0:
            yield f'Received {content_length_diff} bytes more than expected during the download of "{video.filename}"'

        else:
            yield f'Received {-content_length_diff} bytes less than expected during the download of "{video.filename}"'

        return

    written_length = downloaded_byte_count
    if download:
        written_length = Path(video_output_filepath).stat().st_size

    if written_length_diff := downloaded_byte_count - written_length:
        if written_length_diff > 0:
            yield f'Wrote {written_length_diff} bytes more than received during the download of "{video.filename}"'

        else:
            yield f'Wrote {-written_length_diff} bytes less than received during the download of "{video.filename}"'

        return

    if delete:
        httpx.get(
            httpx.URL(CONFIG.questdrive_url).join(
                str(Path("delete") / video.filepath),
            ),
        )
