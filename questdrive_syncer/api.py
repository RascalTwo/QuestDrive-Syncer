"""Interactions with QuestDrive."""
from __future__ import annotations

import os
from pathlib import Path

import httpx

from .config import CONFIG
from .constants import (
    VIDEO_SHOTS_PATH,
)
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


def download_and_delete_video(
    video: Video,
    *,
    dry: bool = False,
    delete: bool = True,
) -> None:
    """Download and delete the video."""
    url = CONFIG.questdrive_url + "download/" + video.filepath

    head_response = httpx.head(url)
    expected_byte_count = int(head_response.headers.get("Content-Length", 0))
    downloaded_byte_count = expected_byte_count
    if not dry:
        response = httpx.get(url)
        expected_byte_count = int(response.headers.get("Content-Length", 0))
        downloaded_byte_count = len(response.content)

        with Path(f"{CONFIG.output_path}{video.filename}").open("wb") as f:
            f.write(response.content)
        os.utime(
            f"{CONFIG.output_path}{video.filename}",
            (video.created_at.timestamp(), video.modified_at.timestamp()),
        )

    if video.actively_recording:
        print(f'"{video.filename}" is actively recording, not deleting')
        return

    content_length_diff = downloaded_byte_count - expected_byte_count
    if content_length_diff:
        if content_length_diff > 0:
            print(
                f'Received {content_length_diff} bytes more than expected during the download of "{video.filename}"',
            )
        else:
            print(
                f'Received {-content_length_diff} bytes less than expected during the download of "{video.filename}"',
            )
        return

    written_length = downloaded_byte_count
    if not dry:
        written_length = Path(f"{CONFIG.output_path}{video.filename}").stat().st_size

    written_length_diff = downloaded_byte_count - written_length
    if written_length_diff:
        if written_length_diff > 0:
            print(
                f'Wrote {written_length_diff} bytes more than received during the download of "{video.filename}"',
            )
        else:
            print(
                f'Wrote {-written_length_diff} bytes less than received during the download of "{video.filename}"',
            )
        return

    if delete and not dry:
        httpx.get(CONFIG.questdrive_url + "delete/" + video.filepath)
