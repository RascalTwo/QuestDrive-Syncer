"""Interactions with QuestDrive."""
from __future__ import annotations

import httpx

from questdrive_syncer.config import CONFIG
from questdrive_syncer.constants import (
    VIDEO_SHOTS_PATH,
)
from questdrive_syncer.structures import MissingVideoError, Video


def is_online() -> bool:
    """Check if QuestDrive is online."""
    try:
        response = httpx.get(CONFIG.questdrive_url)
    except httpx.ConnectError:
        return False
    else:
        return response.status_code == httpx.codes.OK


def fetch_video_list_html() -> str:
    """Fetch the URL and HTML of the video list."""
    return httpx.get(httpx.URL(CONFIG.questdrive_url).join(VIDEO_SHOTS_PATH)).text


def fetch_homepage_html() -> str:
    """Fetch the URL and HTML of the video list."""
    return httpx.get(CONFIG.questdrive_url).text


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
